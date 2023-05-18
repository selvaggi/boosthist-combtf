import sys, os, glob, shutil, json, math, re, random
import time
import ROOT
import narf
import hdf5plugin
import h5py
from narf.narf.ioutils import H5PickleProxy
from dataset import Dataset

ROOT.TH1.SetDefaultSumw2(True)


def build_and_run(datadict, build_function, outfile, maxFiles=-1, norm=False, lumi=1.):
    time0 = time.time()

    results = []
    hweights = []
    evtcounts = []
    chains = []
    datasets = []

    for val in datadict:
    
        if not os.path.exists(val['datadir']):
            print(f"WARNING: directory {val['datadir']} does not exist, skipping dataset {val['name']}")
            continue

        dataset = Dataset(val)
        datasets.append(dataset)

        chain = ROOT.TChain("events")
        nFiles = 0
        for fpath in dataset.rootfiles:
            if "248" in fpath: continue # ZZ /eos/experiment/fcc/ee/analyses/case-studies/higgs/flat_trees/zh_vvjj_v2/p8_ee_ZZ_ecm240_score3/events_248.root corr
            chain.Add(fpath)
            nFiles += 1
            if maxFiles > 0 and nFiles >= maxFiles: break
        nEvents = chain.GetEntries()
        print(f"Import {dataset.name} with {nFiles} files and {nEvents} events from directory {dataset.datadir}")
    
        # black magic why this needs to be protected from gc
        chains.append(chain)

        df = ROOT.ROOT.RDataFrame(chain)

        evtcount = df.Count()
        res, hweight = build_function(df, dataset)

        results.append(res)
        hweights.append(hweight)
        evtcounts.append(evtcount)

    time_built = time.time()

    print("Begin event loop")
    ROOT.ROOT.RDF.RunGraphs(evtcounts)
    print("Done event loop")
    time_done_event = time.time()
    
    print("Write output")
    
    
    resultdict = {}

    for dataset, res, hweight, evtcount in zip (datasets, results, hweights, evtcounts):

        dsetresult = {}

        dsetresult["dataset"] = { "name" : dataset.name,
                                  "xsec" : dataset.xsec,
                                  "lumi" : lumi,
                                }


        dsetresult["weight_sum"] = float(hweight[0].GetValue())
        dsetresult["event_count"] = float(evtcount.GetValue())

        output = {}

        for r in res:
            if isinstance(r.GetValue(), ROOT.TNamed):
                name = r.GetName()
                if norm:
                    r.Scale(dataset.xsec*lumi/evtcount.GetValue())
            elif hasattr(r.GetValue(), "name"):
                name = r.GetValue().name
            else:
                name = str(uuid.uuid1())
            output[name] = H5PickleProxy(r.GetValue())

        dsetresult["output"] = output

        resultdict[dataset.name] = dsetresult
        
    with h5py.File(outfile, 'w') as f:
        narf.narf.ioutils.pickle_dump_h5py("results", resultdict, f)

    time_done = time.time()

    
    print("Done")

    print("build graphs:", time_built - time0)
    print("event loop:", time_done_event - time_built)
    print("build results:", time_done - time_done_event)
    print("write results:", time.time() - time_done)
    print("total time:", time.time() - time_built)
    
    print("Output written to %s" % outfile)


    return
   
    
    
    fOut = ROOT.TFile(outfile, "RECREATE")
    for dataset, res, hweight, evtcount in zip (datasets, results, hweights, evtcounts):
        
        fOut.cd()
        fOut.mkdir(dataset.name)
        fOut.cd(dataset.name)

        histsToWrite = {}
        for r in res:
            hist = r.GetValue()
            hName = hist.GetName()
            if hist.GetName() in histsToWrite: # merge histograms in case histogram exists
                histsToWrite[hName].Add(hist)
            else:
                histsToWrite[hName] = hist
        
        for hist in histsToWrite.values():
            if norm:
                hist.Scale(dataset.xsec*lumi/evtcount.GetValue())
            hist.Write()
            
        h_meta = ROOT.TH1D("meta", "", 10, 0, 1)
        h_meta.SetBinContent(1, hweight.GetValue())
        h_meta.SetBinContent(2, evtcount.GetValue())
        h_meta.SetBinContent(3, dataset.xsec)
        h_meta.Write()

    time_done = time.time()
    
    fOut.cd()
    fOut.Close()
    
    print("Done")

    print("build graphs:", time_built - time0)
    print("event loop:", time_done_event - time_built)
    print("build results:", time_done - time_done_event)
    print("write results:", time.time() - time_done)
    print("total time:", time.time() - time_built)
    
    print("Output written to %s" % outfile)

   
def set_threads(args):

    ROOT.EnableImplicitMT()
    if args.nThreads: 
        ROOT.DisableImplicitMT()
        ROOT.EnableImplicitMT(int(args.nThreads))
    print("Run over %d threads" % ROOT.GetThreadPoolSize())
    
    
def get_hostname():

    import socket
    return socket.gethostname()
    
    
def get_basedir(sel=None):

    basedirs = {}
    basedirs['mit'] = "/data/submit/cms/store/fccee/"
    basedirs['cmswmass2'] = "/data/shared/jaeyserm/fccee/"
    basedirs['fcc_eos'] = "/eos/experiment/fcc/ee/generation/DelphesEvents/"
    
    if sel: return basedirs[sel]
    else:
        hostname = get_hostname()
        if "mit.edu" in hostname: return basedirs['mit']
        if "cmswmass2" in hostname: return basedirs['cmswmass2']
        if "lxplus" in hostname: return basedirs['fcc_eos']
    return None
    
    
def filter_datasets(datasets, filt=None):

    if isinstance(filt, str): return [dataset for dataset in datasets if fnmatch.fnmatch(dataset['name'], filt)]
    elif isinstance(filt, list): 
        ret = []
        for dataset in datasets:
            if dataset['name'] in filt: ret.append(dataset)
        return ret
    else: return datasets