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
git clone git@github.com:SUEPPhysics/SUEPLimits.git
cd $CMSSW_BASE/src/SUEPLimits/
```
Given the large number of phase space points in this analysis, it is recommendable to edit or create new datafiles config/inputs_20XX.yaml with a smaller number of files and adjust options_input in runcards.py to the corresponding file name. The code config/create_list/make_yaml.py helps with writing these yaml files.

# The Code set up

This section sits on top of the Combine tools and is run in 4 sections. Make sure that the combine tools are up to date. 

## 1. Configuration

Before we make cards, we need to set up the cross sections for the signal samples, and the list of histograms that are used as inputs for the cards for each year.

Run `make_yaml.py` which will produce a .yaml file for each year containing a list of histogram files for each sample.
You will need to configure the parameters of this script, such as the input directory, the channel, etc.
This script will ***NOT*** inform you if some histograms files are missing, make sure that they're all there when you produce them!	

To make the cross section list, you can use `make_xsec.py`.

## 2. Creating Datacards

The first section creates datacards and root files that will be ready to input into combine. It does this by reading in the histograms made by coffea and preparing the different control and signal regions as well as the different systematic variations. 
Notice that after activating the combine tools through cmsenv, functions and packages from other environments might not work anymore so only activate cmsenv after completing the datacards. 

The nuisances for the datacard are defined in MakeDataCard.py 
The various regions and binnings are defined in runcards.py
The functions used to analyze the histograms as well as the nuisances are defined in ftool/__init__.py

You only need to run one file once you are satisfied with the setup. To make datacards for all the different regions you can run:
```bash
python runcards.py
```

The script expects an output tag/directory defined via `-t`.
The script supports running via slurm and multithread via the `-m slurm/multithread` option.
The script knows not to re-run cards that already eixst under the same tag, but can be forced to via the `-f` parameter.
You can define a subset of samples to run on via the `--include` option, e.g. `--include generic-mPhi300` will only run samples that contain 'generic' and 'mPhi300' in the name.
See the script for more information.

## 3. Running the Combine tool

If there are multiple eras or datacards for different regions they will need to be used together to make a combined.root and combined.dat file. This is done in the runcombine.py file which subsequently runs the combine tool on the created files. If you need to modify the combine commands you can do that here.

To make limits for all of the different samples you can run:
```bash
python runcombine.py
```

The script expects an input/output directory defined via `-i`.
The script knows not to re-run cards that already eixst under the same tag, but can be forced to via the `-f` parameter.
You can define a subset of samples to run on via the `--include` option, e.g. `--include generic-mPhi300` will only run samples that contain 'generic' and 'mPhi300' in the name.
See the script for more information.

The script supports different combine methods, defined via `--combineMethod`. For example to run `AsymptoticLimits`:
```bash
python runcombine.py -M AsymptoticLimits
```
And to run with toys (warning: CPU intensive):
```bash
python runcombine.py -M HybridNew -o "--expectedFromGrid -1"     # observed
python runcombine.py -M HybridNew -o "--expectedFromGrid 0.50"   # expected
python runcombine.py -M HybridNew -o "--expectedFromGrid 0.16"   # -1 sigma
python runcombine.py -M HybridNew -o "--expectedFromGrid 0.84"   # +1 sigma
python runcombine.py -M HybridNew -o "--expectedFromGrid 0.025"  # -2 sigma
python runcombine.py -M HybridNew -o "--expectedFromGrid 0.975"  # +2 sigma
```

## 4. Plotting and additional tools

## Impact Plots

If you would like to look at the impacts you can make the coombined.root and combined.dat and then run the following:
```bash
combineTool.py -M Impacts -d combined.root -m 125 --doInitialFit --robustFit 1
combineTool.py -M Impacts -d combined.root -m 125 --robustFit 1 --doFits
combineTool.py -M Impacts -d combined.root -m 125 --o impacts.json
plotImpacts.py -i impacts.json -o impacts
```
Often, you might need to use `--rMin -1 --rMax 1 --stepSize 0.001` to make everything converge.

## Pre and Post Fit Plots
After running runcards.py and runcombine.py, make a fitDiagnostics.root file containin the pre/post-fit distributions by activating cmsenv and running

```bash
combine -M FitDiagnostics cards-<sample>/combined.root -m 200 --rMin -1 --rMax 2 --saveShapes
```

Make sure to adjust the r-interval (--rMin, --rMax) accordingly.
Use `notebook_tools/prefit_postfit.ipynb` to plot the pre and post-fit plots by pointing it to the output of this command.

## Correlations
See `notebook_tools/CorrelationPlots.ipynb`. 
This notebook plots the correlation matrix of the nuisances and/or the bins, using the outputs from running runcards.py and runcombine.py. 

### Bin-to-Bin Correlations
In order to check the bin-to-bin covariances and correlations, firstly, make a `fitDiagnostics.root` file by activating cmsenv and running any of

- `combine -M FitDiagnostics combined.root  -t -1 --expectSignal 0 --rMin -10 --forceRecreateNLL  --saveWithUncertainties --saveOverallShapes --numToysForShapes 200` (background only)
- `combine -M FitDiagnostics combined.root -t -1 --expectSignal 1 --forceRecreateNLL  --saveWithUncertainties --saveOverallShapes --numToysForShapes 200` (s+b only)
- `combine -M FitDiagnostics combined.root --forceRecreateNLL  --saveWithUncertainties --saveOverallShapes --numToysForShapes 200` (data)

You can use the script `getCovariances.sh` instead (from https://github.com/cericeci/combineScripts/blob/master/getCovariances.sh), and https://twiki.cern.ch/twiki/bin/viewauth/CMS/SUSPAGPreapprovalChecks for a nice walkthrough of the checks.

### Correlations between Nuisances
In to check the nuisance parameters correlations, the command, which produces `robustHesse.root`, is

- ` combine -M MultiDimFit combined.root -m 125 --robustHesse 1 --robustHesseSave 1 --saveFitResult`

See https://cms-analysis.github.io/HiggsAnalysis-CombinedLimit/tutorial2023/parametric_exercise/#correlations-between-parameters.

## Creating Brazil plots with the combine tool limits

The notebook_tools directory contains jupyter notebooks which read in the output of the combine tool and plot the exclusion limits through 1D limit Brazil plots, 2D temperature plots, and 3D summary plots keeping different parameters fixed.
