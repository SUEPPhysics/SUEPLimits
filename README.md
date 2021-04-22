# SUEP Final fitting 
Written for python3 (uproot)
Using SUEP histograms from coffea producer

1) Create datacards and root files to input into combine
2) Run combine for all signal samples

## Get the combine tools
```bash
export SCRAM_ARCH=slc7_amd64_gcc700
cmsrel CMSSW_10_2_13
cd CMSSW_10_2_13/src
cmsenv

git clone https://github.com/cms-analysis/HiggsAnalysis-CombinedLimit.git HiggsAnalysis/CombinedLimit
cd $CMSSW_BASE/src/HiggsAnalysis/CombinedLimit
git fetch origin
git checkout v8.0.1
```

## fetch CombineTool
```bash
cd $CMSSW_BASE/src
bash <(curl -s https://raw.githubusercontent.com/cms-analysis/CombineHarvester/master/CombineTools/scripts/sparse-checkout-https.sh)

cd $CMSSW_BASE/src/
scramv1 b clean; scramv1 b -j 10
```

To run some of the plotting tools, you need third party pakages such as uproot. You can install by:
```bash
pip install uproot --user
pip install thermcolor --user
```

## Now get the FinalFit tools
```bash
cd $CMSSW_BASE/src/
git clone https://github.com/SUEPPhysics/SUEPLimits.git
cd $CMSSW_BASE/src/SUEPLimits/
```
Please make sure to edit config/inputs_XXX.yaml and make appropriate changes about how the group merging should be done

to make datacards for all the different control regions you can run:
```bash
python runcards.py
```

To make limits for all of the differnt samples you can run:
```bash
python runcombine.py
```

To run the impact parameters tools check the documentation here
```bash
combineTool.py -M Impacts -d combined_XXX.dat.root -m 125 --doInitialFit --robustFit 1
combineTool.py -M Impacts -d combined_XXX.dat.root -m 125 --robustFit 1 --doFits
combineTool.py -M Impacts -d combined_XXX.dat.root -m 125 --o impacts.json
plotImpacts.py -i impacts.json -o impacts
```
