import os
import argparse

# Define the constraint function, number of bins should be smaller than some amount
def clean_environment_variables(variables):
    for var in variables:
        if var in os.environ:
            del os.environ[var]

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--datacard",
        dest="datacard",
        default="datacards/card_zhvvjj_4poi.txt",
        required=True,
        help="Path to the combine datacard file",
    )

    parser.add_argument(
        "--tag", dest="tag", default="", required=True, help=""
    ) 

    args = parser.parse_args()

    datacard = args.datacard
    basedatacard = os.path.basename(datacard)

    jobname = "job_{}".format(args.tag)
    root_fitresult = "fit_output.root"

    conflicting_variables = ["PYTHONPATH", "LD_LIBRARY_PATH"]
    clean_environment_variables(conflicting_variables)

    combine_command = "cd CMSSW_10_6_20 && eval `scramv1 runtime -sh` && cd ..; cp {} {}; cd {}; text2hdf5.py {} -o card.hdf5 --X-allow-no-signal --X-allow-no-background; combinetf.py card.hdf5 -o {} -t -1 --binByBinStat --expectSignal=1".format(datacard, jobname, jobname, basedatacard, root_fitresult
    )
    
    os.system(combine_command)