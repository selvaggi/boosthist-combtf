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

To run the ```templates.py``` script to produce unrolled 1D template histograms with ```HistoBoost``` within the singularity image:

```shell
python template.py  --datadir /eos/experiment/fcc/ee/analyses/case-studies/higgs/flat_trees/zh_vvjj_var_v3 --cfg config/config_zhvvjj_4poi.py --min-yield 0.0 --min-mcstat 1.0 --tag vvjj_4poi
```

arguments: 

- ```--datadir```: where the processes flat trees are located
- ```--cfg```: analysis config file, where processes, cuts, and axes for the Ndim boosthist are defined
- ```--min-yield```: minimum yield per bin when unrolling in 1D
- ```--min-mcstat```: minimum mc stat per bin when unrolling in 1D

Now run limits using combineTF:

```shell
python limits.py  --datacard datacards/card_zhvvjj_4poi.txt --tag vvjj_4poi
```

arguments: 

- ```--datadir```: where flattuples are located
- ```--tag```: a string to indentify the job (has to be the same as in the ```template.py``` script)
