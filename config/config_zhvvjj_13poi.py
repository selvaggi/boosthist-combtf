import hist
from collections import OrderedDict

debug = False
dataDir = "/mnt/data/"
lumi = 5e6

#### list of processes and respective variables/ranges and cross sections
Hbb = {
    "name": "Hbb",
    "datadir": "{}/wzp6_ee_nunuH_Hbb_ecm240_score_13classes_v1".format(dataDir),
    "xsec": 0.0269,
    "isSignal": True,
}
Hcc = {
    "name": "Hcc",
    "datadir": "{}/wzp6_ee_nunuH_Hcc_ecm240_score_13classes_v1".format(dataDir),
    "xsec": 0.001335,
    "isSignal": True,
}
Hss = {
    "name": "Hss",
    "datadir": "{}/wzp6_ee_nunuH_Hss_ecm240_score_13classes_v1".format(dataDir),
    "xsec": 1.109e-05,
    # "xsec": 1.109e-03,
    "isSignal": True,
}
Hdd = {
    "name": "Hdd",
    "datadir": "{}/wzp6_ee_nunuH_Hdd_ecm240_score_13classes_v1".format(dataDir),
    "xsec": 5.5e-07*0.04620,
    "isSignal": True,
}

Huu = {
    "name": "Huu",
    "datadir": "{}/wzp6_ee_nunuH_Huu_ecm240_score_13classes_v1".format(dataDir),
    "xsec": 1.2e-07*0.04620,
    "isSignal": True,
}
Hbs = {
    "name": "Hbs",
    "datadir": "{}/wzp6_ee_nunuH_Hbs_ecm240_score_13classes_v1".format(dataDir),
    "xsec": 8.9e-09*0.04620,
    "isSignal": True,
}

Hbd = {
    "name": "Hbd",
    "datadir": "{}/wzp6_ee_nunuH_Hbd_ecm240_score_13classes_v1".format(dataDir),
    "xsec": 3.8e-09*0.04620,
    "isSignal": True,
}
Hsd = {
    "name": "Hsd",
    "datadir": "{}/wzp6_ee_nunuH_Hsd_ecm240_score_13classes_v1".format(dataDir),
    "xsec": 1.9e-15*0.04620,
    "isSignal": True,
}

Hcu = {
    "name": "Hcu",
    "datadir": "{}/wzp6_ee_nunuH_Hcu_ecm240_score_13classes_v1".format(dataDir),
    "xsec": 2.7e-20*0.04620,
    "isSignal": True,
}

Hgg = {
    "name": "Hgg",
    "datadir": "{}/wzp6_ee_nunuH_Hgg_ecm240_score_13classes_v1".format(dataDir),
    "xsec": 0.003782,
    "isSignal": True,
}
Htautau = {
    "name": "Htautau",
    "datadir": "{}/wzp6_ee_nunuH_Htautau_ecm240_score_13classes_v1".format(dataDir),
    "xsec": 0.002897,
    "isSignal": True,
}

HWW = {
    "name": "HWW",
    "datadir": "{}/wzp6_ee_nunuH_HWW_ecm240_score_13classes_v1".format(dataDir),
    "xsec": 0.00994,
    "isSignal": True,
}
HZZ = {
    "name": "HZZ",
    "datadir": "{}/wzp6_ee_nunuH_HZZ_ecm240_score_13classes_v1".format(dataDir),
    "xsec": 0.00122,
    "isSignal": True,
}
qqH = {
    "name": "qqH",
    "datadir": "{}/wzp6_ee_qqH_ecm240_score_13classes_v1".format(dataDir),
    "xsec": 0.13635,
    "isSignal": False,
}

WW = {
    "name": "WW",
    "datadir": "{}/p8_ee_WW_ecm240_score_13classes_v1".format(dataDir),
    "xsec": 16.4385,
    "isSignal": False,
}
ZZ = {
    "name": "ZZ",
    "datadir": "{}/p8_ee_ZZ_ecm240_score_13classes_v1".format(dataDir),
    "xsec": 1.35899,
    "isSignal": False,
}
Zqq = {
    "name": "Zqq",
    "datadir": "{}/p8_ee_Zqq_ecm240_score_13classes_v1".format(dataDir),
    "xsec": 52.6539,
    "isSignal": False,
}

datasets = [
    Hbb,
    Hcc,
    Hss,
    Hgg,
    Htautau,
    HWW,
    HZZ,
    Huu,
    Hdd,
    Hbs,
    Hbd,
    Hcu,
    Hsd,
    qqH,
    ZZ,
    WW,
    Zqq,
]
# datasets = [Hbb]

procs = []
for d in datasets:
    if "name" in d:
        procs.append(d["name"])

var = "ip"
scale = 1.0

label = "{}{}".format(var, scale).replace(".".format(dataDir), "p")

presel = "muons_p_{} < 20 && electrons_p_{} < 20 && costhetainv_{} < 0.85 && costhetainv_{} > -0.85".format(
    label, label, label, label
)

"""
categories = {
    "B": {
        "formula": "Hbb",
        "bounds": [-999, -0., 999]
    }, 
    "C": {
        "formula": "Hcc",
        "bounds": [-999, -0., 999]
    }, 

    "S": {
        "formula": "Hss",
        "bounds": [-999, -0., 999]
    }, 
    
    "G": {
        "formula": "Hgg",
        "bounds": [-999, -0., 999]
    },
}
"""

categories = dict()
for d in datasets:
    if d["isSignal"]:
        categories[d["name"]] = {"formula": d["name"], "bounds": [-999, -1.0, 0.0, 1.0, 999]}

"""
categories["Hbb"]["bounds"] = [-999, -5, -1.5, 0.5, 2, 999]
categories["Hcc"]["bounds"] = [-999, -7.5, -5.5, 0.5, 2.5, 999]
categories["Hss"]["bounds"] = [-999, -6.5, -5.5, -4.5, -2.5, 1, 999]
categories["Hgg"]["bounds"] = [-999, -8, -7, -1.5, 0, 1, 999]
categories["Htautau"]["bounds"] = [-999, -3, 2, 999]
categories["Huu"]["bounds"] = [-999, -6.5, -5.5, -4, -2.5, -0.5, 0.5, 999]
categories["Hdd"]["bounds"] = [-999, -6.5, -5.5, -3.5, -2.5, -0.5, 0.5,  999]
categories["Hbs"]["bounds"] = [-999, -8, -1, 2, 999]
categories["Hbd"]["bounds"] = [-999, -8, -1, 2, 999]
categories["Hsd"]["bounds"] = [-999, -7, -5.5, -4.5, -3, 1, 999]
categories["Hcu"]["bounds"] = [-999, -8, -4, 0, 2, 999]
categories["HWW"]["bounds"] = [-999, -7, -3, 0, 2, 999]
categories["HZZ"]["bounds"] = [-999, -4.5, 0, 2.5, 999]
"""

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
        ncat += 1
        cat_selection += "( "
        for cat2 in categories_list:
            cat_selection += " {} >= {} &&".format(
                categories[cat]["formula"], categories[cat2]["formula"]
            )

        cat_selection += " {} >= {} &&  {} < {} )*{} + ".format(
            categories[cat]["formula"], vmin, categories[cat]["formula"], vmax, ncat
        )

cat_selection = cat_selection.rsplit(" +", 1)[0]


print(cat_selection)


defines = dict()
defines["cat"] = cat_selection

axes = OrderedDict()

axes["cat"] = hist.axis.Regular(
    ncat, 0.5, ncat + 0.5, name="cat", underflow=False, overflow=False
)
# axes["Mrec_jj_{}".format(label)] = hist.axis.Regular(400, 0, 200, name = "mrec", underflow=False, overflow=False)
# axes["M_jj_{}".format(label)] = hist.axis.Regular(400, 0, 200, name = "mjj", underflow=False, overflow=False)
axes["Mrec_jj_{}".format(label)] = hist.axis.Regular(
    105, 40, 145, name="mrec", underflow=False, overflow=False
)
axes["M_jj_{}".format(label)] = hist.axis.Regular(
    90, 60, 150, name="mjj", underflow=False, overflow=False
)
