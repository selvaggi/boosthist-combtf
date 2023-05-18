
import hist
from collections import OrderedDict

debug = False
name = "zhvvjj"
homeDir = "/afs/cern.ch/work/s/selvaggi/private/FCCSW-ee/analysis/ee_zh_vvjj/combine_boost/"
homeDir = "/tmp/"
dataDir = "/mnt/data/"
outputDir = "{}/output_{}".format(homeDir, name)
lumi = 5e6


#### list of processes and respective variables/ranges and cross sections
Hbb = {
    "name": "Hbb",
    "datadir": "{}/wzp6_ee_nunuH_Hbb_ecm240".format(dataDir),
    "xsec": 0.0269,
}
Hcc = {
    "name": "Hcc",
    "datadir": "{}/wzp6_ee_nunuH_Hcc_ecm240".format(dataDir),
    "xsec": 0.001335,
}
Hss = {
    "name": "Hss",
    "datadir": "{}/wzp6_ee_nunuH_Hss_ecm240".format(dataDir),
    "xsec": 1.109e-05,
}
Hdd = {
    "name": "Hdd",
    "datadir": "{}/wzp6_ee_nunuH_Hdd_ecm240".format(dataDir),
    "xsec": 9.702e-09,
}

Huu = {
    "name": "Huu",
    "datadir": "{}/wzp6_ee_nunuH_Huu_ecm240".format(dataDir),
    "xsec": 4.158e-09,
}
Hbs = {
    "name": "Hbs",
    "datadir": "{}/wzp6_ee_nunuH_Hbs_ecm240".format(dataDir),
    "xsec": 1e-10,
}

Hbd = {
    "name": "Hbd",
    "datadir": "{}/wzp6_ee_nunuH_Hbd_ecm240".format(dataDir),
    "xsec": 1e-12,
}
Hsd = {
    "name": "Hsd",
    "datadir": "{}/wzp6_ee_nunuH_Hsd_ecm240".format(dataDir),
    "xsec": 1e-19,
}

Hcu = {
    "name": "Hcu",
    "datadir": "{}/wzp6_ee_nunuH_Hcu_ecm240".format(dataDir),
    "xsec": 1e-14,
}

Hgg = {
    "name": "Hgg",
    "datadir": "{}/wzp6_ee_nunuH_Hgg_ecm240".format(dataDir),
    "xsec": 0.003782,
}
Htautau = {
    "name": "Htautau",
    "datadir": "{}/wzp6_ee_nunuH_Htautau_ecm240".format(dataDir),
    "xsec": 0.002897,
}
HWW = {
    "name": "HWW",
    "datadir": "{}/wzp6_ee_nunuH_HWW_ecm240".format(dataDir),
    "xsec": 0.00994,
}
HZZ = {
    "name": "HZZ",
    "datadir": "{}/wzp6_ee_nunuH_HZZ_ecm240".format(dataDir),
    "xsec": 0.00122,
}
qqH = {
    "name": "qqH",
    "datadir": "{}/wzp6_ee_qqH_ecm240".format(dataDir),
    "xsec": 0.13635,
}

WW = {
    "name": "WW",
    "datadir": "{}/p8_ee_WW_ecm240".format(dataDir),
    "xsec": 16.4385,
}
ZZ = {
    "name": "ZZ",
    "datadir": "{}/p8_ee_ZZ_ecm240".format(dataDir),
    "xsec": 1.35899,
}
Zqq = {
    "name": "Zqq",
    "datadir": "{}/p8_ee_Zqq_ecm240".format(dataDir),
    "xsec": 52.6539,
}



datasets = [Hbb, Hcc, Hss, Huu, Hdd, Hgg, Htautau, HWW, HZZ, qqH, ZZ, WW, Zqq]

#datasets = [Hbb]


procs = []
for d in datasets:
    if "name" in d:
        procs.append(d["name"])



var="ip"
scale = 1.0

label = "{}{}".format(var, scale).replace(".".format(dataDir),"p")

presel="muons_p_{} < 20 && electrons_p_{} < 20 && costhetainv_{} < 0.85 && costhetainv_{} > -0.85".format(label,label,label,label)

categories = {
    "B": {
        "formula": "(jet1_scoreB_{} + jet2_scoreB_{})".format(label,label),
        "bounds": [-999, 1.1, 1.9, 999]
    }, 
    "C": {
        "formula": "(jet1_scoreC_{} + jet2_scoreC_{})".format(label,label),
        "bounds": [-999, 1.0, 1.8, 999]
    }, 

    "S": {
        "formula": "(jet1_scoreS_{} + jet2_scoreS_{})".format(label,label),
        "bounds": [-999, 1.1, 1.7, 999]
    }, 
    
    "D": {
        "formula": "(jet1_scoreD_{} + jet2_scoreD_{})".format(label,label),
        "bounds": [-999, 1.0, 1.8, 999]
    }, 

    "U": {
        "formula": "(jet1_scoreU_{} + jet2_scoreU_{})".format(label,label),
        "bounds": [-999, 1.0, 1.8, 999]
    }, 

    "G": {
        "formula": "(jet1_scoreG_{} + jet2_scoreG_{})".format(label,label),
        "bounds": [-999, 1.2, 1.5, 999]
    }, 
    "TAU": {
        "formula": "(jet1_scoreTAU_{} + jet2_scoreTAU_{})".format(label,label),
        "bounds": [-999, 1.0, 1.8, 999]
    }, 

}

categories_list = list(categories.keys())


def make_pairs(input_list):
    pairs = []
    for i in range(len(input_list) - 1):
        pairs.append((input_list[i], input_list[i + 1]))
    return pairs

ncat = 0
cat_selection = ""
for cat in categories_list:
    for vmin, vmax in make_pairs(categories[cat]["bounds"]):
        ncat +=1
        cat_selection += "( "
        for cat2 in categories_list:
            cat_selection += " {} >= {} &&".format(categories[cat]["formula"], categories[cat2]["formula"])
        
        cat_selection += " {} >= {} &&  {} < {} )*{} + ".format(categories[cat]["formula"], vmin, categories[cat]["formula"], vmax, ncat)

cat_selection = cat_selection.rsplit(' +', 1)[0]

print(cat_selection)


defines = dict()
defines["cat"]=cat_selection


axes = OrderedDict()

axes["cat"] = hist.axis.Regular(ncat, 0.5, ncat + 0.5, name = "cat", underflow=False, overflow=False)
#axes["Mrec_jj_{}".format(label)] = hist.axis.Regular(400, 0, 200, name = "mrec", underflow=False, overflow=False)
#axes["M_jj_{}".format(label)] = hist.axis.Regular(400, 0, 200, name = "mjj", underflow=False, overflow=False)
axes["Mrec_jj_{}".format(label)] = hist.axis.Regular(105, 40, 145, name = "mrec", underflow=False, overflow=False)
axes["M_jj_{}".format(label)] = hist.axis.Regular(90, 60, 150, name = "mjj", underflow=False, overflow=False)
