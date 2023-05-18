import os
import subprocess
import argparse

# Define the constraint function, number of bins should be smaller than some amount
def clean_environment_variables(variables):
    for var in variables:
        if var in os.environ:
            del os.environ[var]


def compute_limits(datadir, anacfg, datacard, mcstat_min, ymin,tag):
    # Define the paths to the directories you want to bind
    WORKDIR = (
        "/afs/cern.ch/work/s/selvaggi/private/FCCSW-ee/analysis/ee_zh_vvjj"
    )
    DATA = datadir
    IMAGE_PATH = "/cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling:latest"

    # Set the LC_ALL environment variable to en_US.UTF-8
    os.environ["LANG"] = "C"
    os.environ["LC_ALL"] = "C"

    ANACFG = anacfg
    YMIN_ARG = ymin
    MCSTATMIN = mcstat_min

    print(
        "running limits with YMIN = {}, MCSTATMIN = {}".format(
            YMIN_ARG, MCSTATMIN
        )
    )

    # Run the Singularity container and execute the desired command inside it
    singularity_command = """singularity run --bind "{}:/mnt/ee_zh_vvjj" --bind "{}:/mnt/data" "{}" /bin/bash -c 'source /mnt/ee_zh_vvjj/combine_boost/setup.sh; python /mnt/ee_zh_vvjj/combine_boost/boosthist.py --cfg /mnt/ee_zh_vvjj/combine_boost/{}  --mcstatmin {} --min-yield {}' """.format(
        WORKDIR, DATA, IMAGE_PATH, ANACFG, MCSTATMIN, YMIN_ARG
    )

    print("")
    print("fill histograms in singularity container: ")
    print("")
    print(singularity_command)
    print("")
    print("")

    result = subprocess.run(
        singularity_command,
        shell=True,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )

    print(result.stdout)

    output_lines = result.stdout.split("\n")

    for line in output_lines:
        if "_rebin.root" in line:
            template_root_file = line
            break


    rootbasename = os.path.basename(template_root_file)
    jobname = "{}_{}".format(os.path.splitext(rootbasename)[0],tag)
    # template_root_file = template_root_file.replace("_rebin", "")
    root_fitresult = "fit_output.root"

    basedatacard = os.path.basename(datacard)

    combine_command = "rm -rf {}; mkdir -p {}; cp {} {}/output.root;  cp {} {}; text2hdf5.py {}/{} -o {}/card.hdf5 --X-allow-no-signal --X-allow-no-background; combinetf.py {}/card.hdf5 -o {}/{} -t -1 --binByBinStat --expectSignal=1".format(jobname, jobname,
        template_root_file, jobname, datacard, jobname, jobname, basedatacard, jobname, jobname, jobname, root_fitresult
    )

    print("")
    print("now run combine: ")
    print("")
    print(combine_command)
    print("")
    print("")

    # Example usage:
    conflicting_variables = ["PYTHONPATH", "LD_LIBRARY_PATH"]
    clean_environment_variables(conflicting_variables)

    shell_cmd = "cd CMSSW_10_6_20 && eval `scramv1 runtime -sh` && cd .. && {}".format(combine_command)
    process = subprocess.Popen(shell_cmd, shell=True, executable='/bin/bash', stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()

    return_code = process.returncode
    if return_code != 0:
        print("Error occurred: {}".format(stderr.decode('utf-8')))
    else:
        print("Output: {}".format(stdout.decode('utf-8')))
# _____________________________________________________________________________

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--datadir",
        dest="datadir",
        default="/eos/experiment/fcc/ee/analyses/case-studies/higgs/flat_trees/zh_vvjj_var_v3",
        required=True,
        help="abs path to the data flat trees",
    )   

    parser.add_argument(
        "--anacfg",
        dest="anacfg",
        default="config/config_zhvvjj_4poi.py",
        required=True,
        help="Path to the analysis config file",
    )

    parser.add_argument(
        "--datacard",
        dest="datacard",
        default="datacards/card_zhvvjj_4poi.txt",
        required=True,
        help="Path to the combine datacard file",
    )

    ## only applied if rebin
    parser.add_argument(
        "--min-yield", dest="ymin", type=float, default=1e-03, required=True, help=""
    )

    parser.add_argument(
        "--min-mcstat", dest="mcstat_min", type=float, default=7, required=True, help=""
    ) 
    parser.add_argument(
        "--tag", dest="tag", default="", required=True, help=""
    ) 

    args = parser.parse_args()

    compute_limits(args.datadir, args.anacfg, args.datacard, args.mcstat_min, args.ymin, args.tag)