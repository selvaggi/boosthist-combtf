This script allows to produce BoostHistograms in N dimensions in MT mode, unroll them in 1D and run combineTF. (credits J. Bendavid, J. Eysermans). After unrolling it is possible to remove empty bins and require either minimum total yield per bin or minimum total MC statistics per bin. 


## Installation


Make sure singularity is installed by typing 

```shell
singularity version
```

Install CMSSW and combineTF (do not source env with cmsenv)
```shell
cmsrel CMSSW_10_6_20
cd CMSSW_10_6_20/src/
cmsenv
git clone -b tensorflowfit https://github.com/bendavid/HiggsAnalysis-CombinedLimit.git HiggsAnalysis/CombinedLimit
scram b -j 8
cd ../../
```

## Run instructions

In a new shell source environment:

```shell
source /cvmfs/fcc.cern.ch/sw/latest/setup.sh 
```

To run the ```boosthist.py``` script to produce unrolled 1D template histograms with ```HistoBoost``` within the singularity image:

```shell
DATADIR="/eos/experiment/fcc/ee/analyses/case-studies/higgs/flat_trees/zh_vvjj_var_v3"
singularity run --bind "${PWD}:/mnt/" --bind "${DATADIR}:/mnt/data" "/cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling:latest" /bin/bash -c 'source /mnt/setup.sh; python /mnt/boosthist.py --cfg /mnt/config/config_zhvvjj_4poi.py  --min-mcstat 1.0 --min-yield 0.0'
```

arguments: 

- ```--cfg```: analysis config file, where processes, cuts, and axes for the Ndim boosthist are defined
- ```--min-yield```: minimum yield per bin when unrolling in 1D
- ```--min-mcstat```: minimum mc stat per bin when unrolling in 1D

Now run limits using combineTF:

```shell
unset PYTHONPATH && unset LD_LIBRARY_PATH
cd CMSSW_10_6_20 && eval `scramv1 runtime -sh` && cd ..
cp /tmp//output_zhvvjj/templates__ymin_0.0__mcmin_1.0_rebin.root output.root
text2hdf5.py datacards/card_zhvvjj_4poi.txt -o card.hdf5 --X-allow-no-signal --X-allow-no-background 
combinetf.py card.hdf5 -o fit_output.root -t -1 --binByBinStat --expectSignal=1
```

To run histogram generation and combine in 1 command: 
```shell
source /cvmfs/fcc.cern.ch/sw/latest/setup.sh
DATADIR="/eos/experiment/fcc/ee/analyses/case-studies/higgs/flat_trees/zh_vvjj_var_v3"
python template_and_limits.py --datadir ${DATADIR} --anacfg config/config_zhvvjj_4poi.py --datacard datacards/card_zhvvjj_4poi.txt --min-yield 0.0 --min-mcstat 1 --tag v0
```

arguments: 

- ```--datadir```: where flattuples are located
- ```--cfg```: analysis config file, where processes, cuts, and axes for the Ndim boosthist are defined
- ```--datacard```: combine datacard
- ```--min-yield```: minimum yield per bin when unrolling in 1D
- ```--min-mcstat```: minimum mc stat per bin when unrolling in 1D
- ```--tag```: a string to indentify the job


