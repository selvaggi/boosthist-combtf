import functions
import ROOT
import argparse
import narf.narf
import narf
import hist
import os
import h5py
import math
import copy
import numpy as np
import sys
from threading import Thread
import importlib.util

ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)
ROOT.gStyle.SetOptTitle(0)


# ______________________________________________________________________________
def load_config_file(config_file_path):
    spec = importlib.util.spec_from_file_location("config", config_file_path)
    config = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config)
    return config


parser = argparse.ArgumentParser()
parser.add_argument(
    "--cfg",
    dest="config_file",
    required=True,
    help="Path to the config file",
)
parser.add_argument("--nThreads", type=int, help="number of threads", default=None)

## only applied if rebin
parser.add_argument("--min-yield", dest="min_yield", type=float, required=True, help="")

parser.add_argument("--min-mcstat", dest="min_mcstat", type=float, required=True, help="")


args = parser.parse_args()

## require to run boost histogram in mt mode
functions.set_threads(args)

config = load_config_file(args.config_file)

procs = config.procs
axes = config.axes
defines = config.defines
presel = config.presel


# ______________________________________________________________________________
def build_graph(df, dataset):

    print("build graph", dataset.name)
    results = []

    df = df.Define("weight", "1.0")
    weightsum = df.SumAndCount("weight")

    for key, val in defines.items():
        df = df.Define(key, val)

    df = df.Filter(presel)

    results.append(
        df.HistoBoost(
            "histo_nd",
            list(axes.values()),
            list(axes.keys()),
        )
    )
    return results, weightsum


# ______________________________________________________________________________


def unroll(bhist, proc, weight):
    global rhists, rhists_raw
    print(f"Start unrolling {proc}")
    values, variances = bhist.values(), bhist.variances()
    values_flat, variances_flat = values.flatten(), variances.flatten()
    nbins = len(values_flat)

    rhist = ROOT.TH1D(f"hist_{proc}", "", nbins, 0, nbins)
    rhist_raw = ROOT.TH1D(f"hist_{proc}_raw", "", nbins, 0, nbins)

    for iBin in range(0, nbins):
        rhist_raw.SetBinContent(iBin + 1, values_flat[iBin])
        rhist_raw.SetBinError(iBin + 1, variances_flat[iBin] ** 0.5)
        rhist.SetBinContent(iBin + 1, weight * values_flat[iBin])
        rhist.SetBinError(iBin + 1, weight * variances_flat[iBin] ** 0.5)

    rhists_raw.append(rhist_raw)
    rhists.append(rhist)

    print(f"Finished {proc}")


# ______________________________________________________________________________


def sum_histograms(histograms):
    sum_hist = histograms[0].Clone("sum_hist")
    for hist in histograms[1:]:
        sum_hist.Add(hist)
    return sum_hist


# ______________________________________________________________________________


def th1_to_numpy(hist):
    n_bins = hist.GetNbinsX()
    bin_contents = np.zeros(n_bins)
    binerr_contents = np.zeros(n_bins)

    for i in range(n_bins):
        bin_contents[i] = hist.GetBinContent(i + 1)  # Note: Bin numbering starts from 1 in ROOT
        binerr_contents[i] = hist.GetBinError(i + 1)  # Note: Bin numbering starts from 1 in ROOT

    return bin_contents, binerr_contents


# ______________________________________________________________________________


def remove_zeros(array):
    nonzero_indices = np.nonzero(array)[0]
    zero_indices = np.setdiff1d(np.arange(array.size), nonzero_indices).tolist()
    filtered_array = array[nonzero_indices]
    return filtered_array, zero_indices


# ______________________________________________________________________________


def remove_indices(array, zero_indices):
    mask = np.ones(array.shape, dtype=bool)
    mask[zero_indices] = False
    filtered_array = array[mask]

    return filtered_array


# ______________________________________________________________________________


def perform_operations(chunk, arrin, arrin_raw, min_value, min_mc_value):
    global chunks, splitted_sum_np_rebinned, splitted_sumraw_np_rebinned, splitted_recorded_operations

    def find_smallest_index(arr, value):
        min_index = np.argmin(arr)
        if arr[min_index] < value:
            return min_index
        return None

    arr = copy.copy(arrin)
    rawarr = copy.copy(arrin)

    operations = []
    min_index = find_smallest_index(arr, min_value)

    insize = len(arr)
    insum = np.sum(arr)

    count = np.count_nonzero(arr < min_value)

    frac_lt = float(count) / insize

    ## first fin all ops according to the min value criterion
    while min_index is not None and len(arr) > 1:

        red_fact = float(len(arr)) / insize

        # print("merging bins, size reduction factor: {}".format(float(len(arr)) / insize))
        left_indices = np.arange(max(0, min_index - 1), min_index)
        right_indices = np.arange(min_index + 1, min(len(arr), min_index + 2))
        neighbors = np.hstack((arr[left_indices], arr[right_indices]))
        smallest_neighbor_index = np.argmin(neighbors)
        smallest_neighbor = neighbors[smallest_neighbor_index]

        if smallest_neighbor_index < len(left_indices):
            op = (left_indices[smallest_neighbor_index], min_index)
        else:
            op = (
                min_index,
                right_indices[smallest_neighbor_index - len(left_indices)],
            )

        # Record the operation
        operations.append(op)

        # Replace the entry with the sum of that entry and the smallest of the two neighbors
        arr[op[0]] = arr[op[0]] + arr[op[1]]

        # Create a new array without the neighbors in question
        arr = np.delete(arr, op[1])

        min_index = find_smallest_index(arr, min_value)

    ## at this stage we have the new arr ops according to the min value criterion
    ## now apply all the  ops to the raw arr to get to the same point
    rawarr = rebinned(rawarr, operations)
    min_index = find_smallest_index(rawarr, min_mc_value)

    ## first fin all ops according to the min value criterion
    while min_index is not None and len(rawarr) > 1:

        red_fact = float(len(rawarr)) / insize

        # print("merging bins, size reduction factor: {}".format(float(len(arr)) / insize))
        left_indices = np.arange(max(0, min_index - 1), min_index)
        right_indices = np.arange(min_index + 1, min(len(rawarr), min_index + 2))
        neighbors = np.hstack((rawarr[left_indices], rawarr[right_indices]))
        smallest_neighbor_index = np.argmin(neighbors)
        smallest_neighbor = neighbors[smallest_neighbor_index]

        if smallest_neighbor_index < len(left_indices):
            op = (left_indices[smallest_neighbor_index], min_index)
        else:
            op = (
                min_index,
                right_indices[smallest_neighbor_index - len(left_indices)],
            )

        # Record the operation
        operations.append(op)

        # Replace the entry with the sum of that entry and the smallest of the two neighbors
        rawarr[op[0]] = rawarr[op[0]] + rawarr[op[1]]

        # Create a new array without the neighbors in question
        rawarr = np.delete(rawarr, op[1])

        min_index = find_smallest_index(rawarr, min_mc_value)

    ## at this stage we have the new arr ops according to the min value criterion
    ## now apply all the  ops to the raw arr to get to the same point
    arr = rebinned(arrin, operations)

    chunks.append(chunk)
    splitted_sum_np_rebinned.append(arr)
    splitted_sumraw_np_rebinned.append(rawarr)
    splitted_recorded_operations.append(operations)

    """
    print(
        f"{chunk}: {insize} -> {len(arr)}, check diff: {insum - np.sum(arr)}, nom sum: {insum}, rebin sum :{np.sum(arr)}"
    )
    """


# ______________________________________________________________________________


def apply_rebinning(chunks, splitted_sum_np_hist, splitted_recorded_operations, available_cpus):
    global chunks_hist, splitted_sum_np_rebinned
    chunks_hist, splitted_sum_np_rebinned = [], []
    debug = False
    for chunk, sub_hist in enumerate(splitted_sum_np_hist):

        """
        apply_operations(
            chunk,
            sub_hist,
            splitted_recorded_operations[chunks.index(chunk)],
        )
        """

        thread = Thread(
            target=apply_operations,
            args=(
                chunk,
                sub_hist,
                splitted_recorded_operations[chunks.index(chunk)],
            ),
        )

        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    sum_np_rebinned = np.array([])
    for m in range(available_cpus):
        # for m, sub_hist in enumerate(splitted_sum_np):

        sum_np_rebinned = np.concatenate(
            (
                sum_np_rebinned,
                splitted_sum_np_rebinned[chunks_hist.index(m)],
            )
        )

        if debug:
            print(
                m,
                chunks_hist.index(m),
                len(sum_np_rebinned),
                np.sum(splitted_sum_np_hist[m]),
                np.sum(splitted_sum_np_rebinned[chunks_hist.index(m)]),
                np.sum(splitted_sum_np_hist[m]) - np.sum(splitted_sum_np_rebinned[chunks_hist.index(m)]),
            )

    return sum_np_rebinned


# ______________________________________________________________________________


def apply_operations(chunk, arrin, operations):
    global chunks_hist, splitted_sum_np_rebinned
    arr = copy.copy(arrin)
    for min_index, neighbor_index in operations:

        if neighbor_index < min_index:
            min_index, neighbor_index = neighbor_index, min_index

        arr[min_index] = arr[min_index] + arr[neighbor_index]

        arr = np.delete(arr, neighbor_index)

    splitted_sum_np_rebinned.append(arr)
    chunks_hist.append(chunk)


# ______________________________________________________________________________


def rebinned(arrin, operations):

    arr = copy.copy(arrin)
    for min_index, neighbor_index in operations:

        if neighbor_index < min_index:
            min_index, neighbor_index = neighbor_index, min_index

        arr[min_index] = arr[min_index] + arr[neighbor_index]

        arr = np.delete(arr, neighbor_index)
    return arr


# _____________________________________________________________________________
if __name__ == "__main__":

    ###########################################################################
    ## start by filling N dim boosted histograms
    ###########################################################################

    """
    nbins = 1
    for nb in args.Nbins:
        nbins *= nb

    print("nbins total = {:.2e}".format(nbins))
    """
    ## create output directory
    if not os.path.exists(config.outputDir):
        os.makedirs(config.outputDir)

    ## create label
    label = "templates"
    # for proc, nb in zip(config.procs, args.Nbins):
    #    label += "__{}_{}".format(proc, nb)

    label += "__ymin_{}".format(args.min_yield)
    label += "__mcmin_{}".format(args.min_mcstat)

    print("job label: {}".format(label))

    h5fname = "{}/{}.hdf5".format(config.outputDir, label)

    ## fill N dim histos if not done already
    """
    if os.path.exists(h5fname):
        print(
            "{} was already produced in a previous run exist, not re-producing it ... ".format(
                h5fname
            )
        )

    else:
        print(
            "{} was not already produced in a previous run exist, re-producing it ... ".format(
                h5fname
            )
        )
    """
    result = functions.build_and_run(
        config.datasets,
        build_graph,
        h5fname,
        maxFiles=-1,
        norm=True,
        lumi=config.lumi,
    )

    rfname = "{}/{}.root".format(config.outputDir, label)
    rfname_rebin = "{}/{}_rebin.root".format(config.outputDir, label)

    ###########################################################################
    ## filling root with raw 1D histograms
    ###########################################################################

    ## fill original root file
    h5file = h5py.File(h5fname, "r")
    results = narf.narf.ioutils.pickle_load_h5py(h5file["results"])

    procs = config.procs

    bh_tot = None
    rhists = []
    rhists_raw = []
    threads = []

    for proc in procs:
        print(f"Process {proc}")
        xsec = results[proc]["dataset"]["xsec"]
        lumi = results[proc]["dataset"]["lumi"]
        weight_sum = results[proc]["weight_sum"]
        bhist = results[proc]["output"]["histo_nd"].get()
        weight = xsec * lumi / weight_sum

        # bhist *= xsec * lumi / weight_sum

        if bh_tot == None:
            bh_tot = bhist
        else:
            bh_tot += bhist

        ## ADD BHIST2 not normalised here, or unrolled not normalised and then reweights the others
        thread = Thread(
            target=unroll,
            args=(bhist, proc, weight),
        )
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    h5file.close()

    bh_tot_arr = bh_tot.values().flatten()
    nz = (bh_tot_arr.size - np.count_nonzero(bh_tot_arr)) / (bh_tot_arr.size)
    print("fraction zero bins: {}".format(nz))

    xsec * lumi / weight_sum

    fIn = ROOT.TFile(rfname, "RECREATE")
    for h, hraw in zip(rhists, rhists_raw):
        h.Write()
        hraw.Write()

    fIn.Close()

    print("")
    print("ROOT file written to:")
    print("")
    print(rfname)
    print("")

    ###########################################################################
    ## here starts all the post-processing, first removing zeroes, and then rebinning
    ## until only yield > min_value found in each bin
    ###########################################################################

    if args.min_yield == 0 and args.min_mcstat == 0:
        print("no rebinning applied.")
        sys.exit()

    print("summing hists ...")

    sum_hist = sum_histograms(rhists)
    sum_hist_raw = sum_histograms(rhists_raw)

    sum_np, sumerr_np = th1_to_numpy(sum_hist)
    sumraw_np, sumrawerr_np = th1_to_numpy(sum_hist_raw)

    available_cpus = os.cpu_count()

    nbins_min__per_chunk = 10
    nparts = len(sum_np) // nbins_min__per_chunk

    # available_cpus = 1

    print("available CPUs: {}".format(available_cpus))
    print("number of parts: {}".format(nparts))

    # do not need to
    if nparts <= available_cpus:
        available_cpus = nparts

    print("number of chunks: {}".format(available_cpus))

    ## 1st step remove all 0 entries and keep track

    print("reading out which bins have zeroes ...")
    sum_np, zero_indices = remove_zeros(sum_np)
    sumraw_np, zero_indices = remove_zeros(sumraw_np)

    print("found {} ...".format(len(zero_indices)))

    ## now split into much smaller arrays
    splitted_sum_np = np.array_split(sum_np, available_cpus)
    splitted_sumraw_np = np.array_split(sumraw_np, available_cpus)

    threads = []

    min_yield_value = args.min_yield
    min_mc_value = args.min_mcstat

    chunks, splitted_sum_np_rebinned, splitted_sumraw_np_rebinned, splitted_recorded_operations = [], [], [], []
    for chunk, (sub_hist, sub_histraw) in enumerate(zip(splitted_sum_np, splitted_sumraw_np)):
        thread = Thread(
            target=perform_operations,
            args=(chunk, sub_hist, sub_histraw, min_yield_value, min_mc_value),
        )

        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    """
    for chunk, sub_hist in enumerate(splitted_sum_np):
        print(chunk, np.sum(splitted_sum_np[chunk]))
        perform_operations(chunk, sub_hist, min_yield_value)
        print(chunk, np.sum(splitted_sum_np[chunk]))
    """

    sum_np_rebinned = np.array([])
    sumraw_np_rebinned = np.array([])

    # Append arrays one after the other
    for m in range(available_cpus):
        ##
        sum_np_rebinned = np.concatenate((sum_np_rebinned, splitted_sum_np_rebinned[chunks.index(m)]))
        sumraw_np_rebinned = np.concatenate((sumraw_np_rebinned, splitted_sumraw_np_rebinned[chunks.index(m)]))

        if config.debug:
            print(
                m,
                chunks.index(m),
                len(sum_np_rebinned),
                np.sum(splitted_sum_np[m]),
                np.sum(splitted_sum_np_rebinned[chunks.index(m)]),
                np.sum(splitted_sum_np[m]) - np.sum(splitted_sum_np_rebinned[chunks.index(m)]),
            )

    if 1:

        print("initial array: ", len(sum_np))
        print("final array:", len(sum_np_rebinned))
        print("final array (raw):", len(sumraw_np_rebinned))
        print("check sum diff events after rebin: {}".format(np.sum(sum_np) - np.sum(sum_np_rebinned)))

    ## make a final pass on the merged chunks
    perform_operations(available_cpus, sum_np_rebinned, sumraw_np_rebinned, min_yield_value, min_mc_value)

    sum_np_rebinned = splitted_sum_np_rebinned[-1]
    sumraw_np_rebinned = splitted_sumraw_np_rebinned[-1]
    last_recorded_operations = splitted_recorded_operations[-1]

    chunks.pop()
    splitted_sum_np_rebinned.pop()
    splitted_sumraw_np_rebinned.pop()
    splitted_recorded_operations.pop()

    if 1:

        print("initial array: ", len(sum_np))
        print("final array:", len(sum_np_rebinned))
        print("final array (raw):", len(sumraw_np_rebinned))
        print("check sum diff events after rebin: {}".format(np.sum(sum_np) - np.sum(sum_np_rebinned)))

    ## now apply same transformation to individual proccesses
    rhists_rebin = []
    for h in rhists:

        threads = []
        proc_np, procerr_np = th1_to_numpy(h)
        hist_sum = np.sum(proc_np)

        ## removing indices corresponding to 0 entries in the sum hist
        print("removing {} zeroes on {} ...".format(len(zero_indices), h.GetName()))

        proc_nozeroes_np = remove_indices(proc_np, zero_indices)
        procerr_nozeroes_np = remove_indices(procerr_np, zero_indices)

        if config.debug:
            print(
                "check that this hist has same length as original after removing zeroes: {}".format(
                    len(proc_nozeros_np) - len(proc_np)
                )
            )
            print(
                "check that integral is same as original after removing zeroes: {}".format(
                    np.sum(proc_nozeroes_np) - hist_sum
                )
            )

        ## now rebin
        splitted_sum_np_hist = np.array_split(proc_nozeroes_np, available_cpus)
        splitted_sumerr_np_hist = np.array_split(procerr_nozeroes_np, available_cpus)

        print("rebinning on {} until reach {} events per bin ".format(h.GetName(), min_yield_value))

        sum_np_rebinned = apply_rebinning(
            chunks,
            splitted_sum_np_hist,
            splitted_recorded_operations,
            available_cpus,
        )

        sumerr_np_rebinned = apply_rebinning(
            chunks,
            splitted_sumerr_np_hist,
            splitted_recorded_operations,
            available_cpus,
        )

        ## last step of rebinned applied on the the merge histogram
        sum_np_rebinned = rebinned(sum_np_rebinned, last_recorded_operations)
        sumerr_np_rebinned = rebinned(sumerr_np_rebinned, last_recorded_operations)

        if 1:
            print("Initial array {}: ".format(h.GetName()), len(sum_np))
            print("Final array {}:".format(h.GetName()), len(sum_np_rebinned))
            # print("Recorded operations:", len(recorded_operations))
            print(
                "Check sum diff events after rebin {}: {}".format(
                    h.GetName(),
                    np.sum(proc_nozeroes_np) - np.sum(sum_np_rebinned),
                )
            )

        ## now filling rebinned histograms
        print("removed {} bin after rebinning".format(len(proc_nozeroes_np) - len(sum_np_rebinned)))

        """
        #sum_np_rebinned = proc_np
        #sumerr_np_rebinned = procerr_np

        #sum_np_rebinned = proc_nozeroes_np
        #sumerr_np_rebinned = procerr_nozeroes_np
        """

        nbins = len(sum_np_rebinned)
        hname = h.GetName()

        rhist = ROOT.TH1D(hname + "_rebin", "", nbins, 0, nbins)
        for iBin in range(0, nbins):
            rhist.SetBinContent(iBin + 1, sum_np_rebinned[iBin])
            rhist.SetBinError(iBin + 1, sumerr_np_rebinned[iBin])
        print("final number of bins in {}: {}".format(hname + "_rebin", rhist.GetNbinsX()))

        rhists_rebin.append(rhist)

    ## store rebinned rootfiles
    fIn = ROOT.TFile(rfname_rebin, "RECREATE")
    for h in rhists_rebin:
        h.Write()
    fIn.Close()

    print("")
    print("ROOT file written to:")
    print("")
    print(rfname_rebin)
    print("")

    ###########################################################################
    ## now run combine
    ###########################################################################
