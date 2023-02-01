# SUEP Final fitting 
Written for python3 (uproot)
Using SUEP histograms from coffea producer

1) Create datacards and root files to input into combine
2) Run combine for all signal samples

## Get the combine limit tool
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
curl -s https://raw.githubusercontent.com/cms-analysis/CombineHarvester/master/CombineTools/scripts/sparse-checkout-https.sh

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
git clone git@github.com:SUEPPhysics/SUEPLimits.git
cd $CMSSW_BASE/src/SUEPLimits/
```
Please make sure to edit config/inputs_XXX.yaml and make appropriate changes about how the group merging should be done

## The Code set up

This section sits on top of the Combine tools and is run in 3 sections. Make sure that the combine tools are up to date.

## Creating Datacards

The first section creates datacards and root files that will be ready to input into combine. It does this by reading in the histograms made by coffea and preparing the different control and signal regions as well as the different systematic variations. 

The nuisances for the datacard are defined in MakeDataCard.py 
The various regions and binnings are defined in runcards.py
The functions used to analyze the histograms as well as the nuisances are defined in ftool/__init__.py

You only need to run one file once you are satisfied with the setup. To make datacards for all the different regions you can run:
```bash
python runcards.py
```

## Running the Combine tool

If there are multiple eras or datacards for different regions they will need to be used together to make a combined.root and combined.dat file. This is done in the runcombine.py file which subsequently runs the combine tool on the created files. If you need to modify the combine commands you can do that here.

To make limits for all of the differnt samples you can run:
```bash
python runcombine.py
```

If you would like to look at the impacts you can make the coombined.root and combined.dat and then run the following:
```bash
combineTool.py -M Impacts -d combined.root -m 125 --doInitialFit --robustFit 1
combineTool.py -M Impacts -d combined.root -m 125 --robustFit 1 --doFits
combineTool.py -M Impacts -d combined.root -m 125 --o impacts.json
plotImpacts.py -i impacts.json -o impacts
```
## Creating Brazil plots with the combine tool limits

There is also a jupyter notebook that can be run on swan which will read in the output of the combine tool and make Brazil plots. This and other debugging tools can be found in the notebook_tools directory. 
