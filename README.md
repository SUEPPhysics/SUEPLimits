# SUEP Final fitting 
Written for python3 (uproot)
Using SUEP histograms from coffea producer

1) Create datacards and root files to input into combine
2) Run combine for all signal samples

# Installation Instructions

## Get combine
Follow instructions on the [combine documentation](https://cms-analysis.github.io/HiggsAnalysis-CombinedLimit/) to get the combine tool.
At the time of writing, this code has been tested with the latest and reccomended version, v9.

## Get CombineTool
You can follow the instructions on the [combine documentation](https://cms-analysis.github.io/HiggsAnalysis-CombinedLimit/#combine-tool), reported here for your convenience:
```bash
cd $CMSSW_BASE/src
bash <(curl -s https://raw.githubusercontent.com/cms-analysis/CombineHarvester/master/CombineTools/scripts/sparse-checkout-https.sh)

cd $CMSSW_BASE/src/
scramv1 b clean; scramv1 b -j 10
```

## Additional software
To run some of the plotting tools, you need third party pakages such as uproot. You can install by:
```bash
pip install uproot
pip install thermcolor
```

## Get SUEPLimits
```bash
cd $CMSSW_BASE/src/
git clone git@github.com:SUEPPhysics/SUEPLimits.git
cd $CMSSW_BASE/src/SUEPLimits/
```

# The Code set up

This section sits on top of the Combine tools and is run in 4 sections. Make sure that the combine tools are up to date. 

## 1. Configuration: cross sections and histograms

Before we make cards, we need to set up the cross sections for the signal samples, and the list of histograms that are used as inputs for the cards for each year.

Run `make_yaml.py` which will produce a .yaml file for each year containing a list of histogram files for each sample.
You will need to configure the parameters of this script, such as the input directory, the channel, etc.
This script will ***NOT*** inform you if some histograms files are missing, make sure that they're all there when you produce them!	

To make the cross section list, you can use `make_xsec.py`.

## 2. Creating Datacards

The first section creates datacards and root files that will be ready to input into combine.
It does this by reading in the .root histograms and preparing the different control and signal regions as well as the different systematic variations. 
Notice that after activating the combine tools through cmsenv, functions and packages from other environments might not work anymore so only activate cmsenv after completing the datacards. 

The nuisances for the datacard are defined in `makeDataCard.py`. 
The various regions and binnings are defined in `runcards.py`.
The functions used to analyze the histograms as well as the nuisances are defined in `ftool/__init__.py`.

You only need to run one file once you are satisfied with the setup. 
To make datacards for all the different regions you can run:
```bash
python runcards.py
```

The script:
- expects an output tag/directory defined via `-t`.
- supports running via slurm and multithread via the `-m slurm/multithread` option.
- knows not to re-run cards that already exist under the same tag, but can be forced to via the `-f` parameter.
- can run on a subset of samples via the `--includeAny` and `--includAll` options, e.g. `--includeAll generic-mPhi300` will only run samples that contain 'generic' and 'mPhi300' in the name.
- can run on a subset of samples defined in a .txt file via the `--file` option.
  
See the script for more information.

Some examples:

e.g. run  over slurm a list of sapmles from a file
```
python runcards.py -m slurm -t my_tag --file sample.txt
```

e.g. run over multithread with 10 cores all samples with generic decay
```
python runcards.py -m multithread -c 10 -t my_tag --includeAny generic
```

## 3. Running the Combine tool

If there are multiple eras or datacards for different regions they will need to be used together to make a combined.root and combined.dat files, which are the input to the `combine` command.
This is done in the runcombine.py file which subsequently runs the combine tool on the created files. If you need to modify the combine commands you can do that here.

To make limits for all of the different samples you can run:
```bash
python runcombine.py
```

The script:
- expects an input/output tag/directory defined via `-i`.
- supports running via any of the following options: iteratively, multithread, slurm, condor.
- supports running different combine options via `--combineMethod`: `AsymptoticLimits`, `HybridNew`.
- supports further options to be passed to the `combine` command via `--combineOptions`, e.g. `--combineOptions " --fork 100 --expectedFromGrid 0.5"`.
- knows not to re-run cards that already eixst under the same tag, but can be forced to via the `-f` parameter.
- can run on a subset of samples via the `--includeAny` and `--includeAll` option, e.g. `--includeAll generic-mPhi300` will only run samples that contain 'generic' and 'mPhi300' in the name, `--includeAny generic-mPhi300` will run samples that include 'generic' or 'mPhi300' in the name.
- can run all quantiles when running toys with `--quantiles`.
- can run on a subset of samples defined in a .txt file via the `--file` option.
- can be ran 'dry' such that it will not actually run/submit anything with the `--dry` option.

See the script for more information.

Some examples:

e.g. running asymptotic limits for all mS = 125 GeV samples via slurm with setting min and max values on the signal strength `r`:
```bash
python runcombine.py -M AsymptoticLimits -i my_tag --includeAny mS125 -m slurm -o " --rMax 10000 --rMin 0.1 "
```

e.g. running toys (need to run separately for observed, and each 'quanile': expected (0.5), +/-1 sigma (0.84, 0.16), and +/-2 sigma (0.975, 0.025)). Note that these are very computationally intensive, and work best when you are able to split them across several cores, for this example we use 10.
```
python runcombine.py -m condor -i approval_higherPrecision/ -M HybridNew -o " --fork 10 "                            # observed
python runcombine.py -m condor -i approval_higherPrecision/ -M HybridNew -o " --expectedFromGrid 0.025 --fork 10 "   # -2 sigma
python runcombine.py -m condor -i approval_higherPrecision/ -M HybridNew -o " --expectedFromGrid 0.975 --fork 10 "   # +2 sigma
python runcombine.py -m condor -i approval_higherPrecision/ -M HybridNew -o " --expectedFromGrid 0.500 --fork 10 "   # expected
python runcombine.py -m condor -i approval_higherPrecision/ -M HybridNew -o " --expectedFromGrid 0.840 --fork 10 "   # +1 sigma
python runcombine.py -m condor -i approval_higherPrecision/ -M HybridNew -o " --expectedFromGrid 0.160 --fork 10 "   # -1 sigma
```
Alternatively, use the option `--quantiles` to run them all at the same time,
```
python runcombine.py -m condor -i approval_higherPrecision/ -M HybridNew -o " --fork 10 " --quantiles                # runs all quantiles and observed
```

Some notes on running the limits:
- Use `--fork` in the combine command if you are having memory issues.
- Set `--rMax` and `--rMin` if limits are not converging, check the logs, they should say when you are hitting the limits.
- Set `--rAbsAcc` and `--rRelAcc` by hand; make sure that these are smaller than the ~1 sigma bands.

## 4. Monitoring, Plotting and additional tools

## Monitoring

You can use the `monitor.py` script to:
1. **Monitor the completion of the cards.**
    Checks that for sample in the config/<yaml_file>, every sample has all the cards in the 
    local directory/tag.
   - ```python monitor.py --checkMissingCards --tag my_tag```

2. **Monitor the completion of the limits produced via combine, and verify that the they are not corrupted.**
    Will check that for each cards-SAMPLE/ subdirectory under the directory/tag --tag, the correspodning 
    limit files have been produced successfully.
   - ```python monitor.py --checkMissingLimits --deleteCorruptedLimits --combineMethod HybridNew --tag my_tag```

3. **Move the limit files from the remote directory, where condor places the outputs, to the local directory/tag.**
   - ```python monitor.py --moveLimits --remoteDir /path/to/dir/ --tag my_tag```

The above commands can all be combined to run in one go:
```bash
python monitor.py --checkMissingCards --tag my_tag --checkMissingLimits --deleteCorruptedLimits --combineMethod HybridNew  --moveLimits --remoteDir /path/to/dir/ --tag my_tag
```

## Limit Plotting

In `notebook_tools/plot_utils.py` there are many useful functions to plot the limits as functions of the different model parameters.

For the ggF offline analysis, use `notebook_tools/limits_offline.ipynb`.

## Pre and Post Fit Plots

See `prefit_postfit.ipynb`.
This notebook plots the prefit and postift distributions using the output of the following command.

After running runcards.py and runcombine.py, make a fitDiagnostics.root file containin the pre/post-fit distributions by activating cmsenv and running

```bash
combine -M FitDiagnostics cards-<sample>/combined.root -m 200 --rMin -1 --rMax 2 --saveShapes
```

Make sure to adjust the r-interval (--rMin, --rMax) accordingly.
Use `notebook_tools/prefit_postfit.ipynb` to plot the pre and post-fit plots by pointing it to the output of this command.

## Correlations

See `notebook_tools/CorrelationPlots.ipynb`. 
This notebook plots the correlation matrix of the nuisances and/or the bins, using the outputs of the following commands.

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

## Impact Plots

If you would like to look at the impacts you can make the coombined.root and combined.dat and then run the following:
```bash
combineTool.py -M Impacts -d combined.root -m 125 --doInitialFit --robustFit 1
combineTool.py -M Impacts -d combined.root -m 125 --robustFit 1 --doFits
combineTool.py -M Impacts -d combined.root -m 125 --o impacts.json
plotImpacts.py -i impacts.json -o impacts
```
Often, you might need to toggle: `--rMin`, `--rMax`, and `--stepSize`  to make everything converge.
