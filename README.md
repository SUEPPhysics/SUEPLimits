# SUEP Final fitting 
Written for python3 (uproot).
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
git clone https://github.com/cms-analysis/CombineHarvester.git CombineHarvester

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

This tool sits on top of the Combine tools. Make sure that the combine tools are up to date, and familiarize yourself with them through the Combine documentation, if needed.

## 1. Configuration: normalizations and samples

Before we make cards, we need to set up the normalizations (cross sections, branching ratios, and k-factors) for the signal samples, and the list of samples for each era. These (and some files to produce them 'automatically') are stored in `config/`.

For the normalizations, add them for each sample to the `config/xsections_ERA.json` files. These json are common between analyses.

For the list of samples, you need to create a yaml file for each era specific to each analysis.
This configuration can differ between the different SUEP analyses.
The basic components, needed to be compatible with the common script to run the datacard-maker (`runcards.py`), are:

- Each key is a sample name, which is turn a dictionary containing
- A `type` key, which specifies if the sample is `signal` or `data`

This file is usually read in by the datacard-maker, which is different for each analysis, so the rest of the configuration files can differ between analyses. What is also commonly found in these files are:

- A `files` key, containing a list of paths to files containing histograms for each sample
- A  `sample` key, which is used since signal samples may have different names in different eras, but we want to combine them across eras

The production of the yaml file can be 'automated'. For example, for the offline analysis, `config/make_offline_yaml.py` will produce a yaml file for each year containing a list of histogram files for each sample.
You will need to configure the parameters of this script, such as the input directory, the channel, etc.

## 2. Creating Datacards

To create datacards, we use the `datacard` class in `ftool/__init__.py`. The class supports several functions to convert boost histogram objects to a datacard file that Combine can read, as well as functions to add uncertanties, and ABCD predictions.

In order to create the histogram objects for `datacard` from a list of root files, and in order to properly combine samples across eras, normalize them, and more, you can use the `datagroup` class in `ftool/__init__.py`. Each analysis can create a subclass to this one to read their own histograms correctly.

The process of creating a `datagroup` for each sample, and writing it out with `datacard`, is performed in a separate script for each analysis, `make<Analysis>DataCard.py`.

## 3. Running Datacards

The `make<Analysis>DataCard.py` will be ran over many signal samples, and for each signal sample, possibly over many eras and channels/bins.
To scale this out, we use the script `runcards.py`.

The analysis-dependent input to this script is a yaml file that contains the key `runcards` which in turn contains three arguments, unique for each analysis:

1. `commands`: a list of `python make<Analysis>DataCard.py` commands, one per channel/bin.
2. `eras`: a list of eras to execute the commands over.
3. `config`: the path to the configuration file described in section 1, which contains all the signal samples.

The script then iterates over signal samples found in the `config` file, all eras, and all commands, launching jobs to make a datacard for each combination, separately.

If you want to for example combine eras in the same card, you can set this up in your datacard-maker, and only run one era through `runcards.py`.

The script:
- expects an output tag/directory defined via `-t`.
- supports running via slurm and multithread via the `-m slurm/multithread` option.
- knows not to re-run cards that already exist under the same tag, but can be forced to via the `-f` parameter.
- can run on a subset of samples via the `--includeAny` and `--includAll` options, e.g. `--includeAll generic-mPhi300` will only run samples that contain 'generic' and 'mPhi300' in the name.
- can run on a subset of samples defined in a .txt file via the `--file` option.
  
See the script for more information.

Some examples:

e.g. run  over slurm a list of samples from a file
```bash
python runcards.py -a ggf-offline.yaml -m slurm -t my_tag --file sample.txt
```

e.g. run over multithread with 10 cores all samples with generic decay
```bash
python runcards.py -a ggf-offline.yaml -m multithread -c 10 -t my_tag --includeAny generic
```

## 4. Running the Combine tool

Once cards for each signal sample, channel, and era are made, they need to be combined, and only then Combine can be used to obtain limits.

`runcombine.py` executes both of these tasks, combinig the datacards into one per sample, and then running the limits.

The analysis-dependent input to this script is a `yaml` file that contains the key `runcombine` which in turn contains one argument, unique for each analysis:
- `combineCards`: a `combineCards.py` command to combine cards across different channels and eras for each sample. 

The script:
- expects an input/output tag/directory defined via `-i`.
- supports running via any of the following options: iteratively, multithread, slurm, condor, via the `-m` option.
   - automatically requests the correct number of CPUs, and its best guess at memory usage, in the condor and slurm jobs if using `--combineOptions "--fork N"`.
- supports running different combine options via `--combineMethod`: `AsymptoticLimits`, `HybridNew`, `HybridNewAuto`***.
   - *** `HybridNewAuto` is not a real combine option, it's something that we came up with out of convenience. The `AsymptoticLimits` are first ran on the sample to obtain rough bounds on `r`; these are then fed back as `--rMin` and `--rMax` when running the `HybridNew` (toys) option. This is done because the toys are extremely slow and compute-intensive, and it is thus more efficient to constrain the space that needs to be scanned by Combine. 
- supports further options to be passed to the `combine` command via `--combineOptions`, e.g. `--combineOptions " --fork 20 --expectedFromGrid 0.5"` tells Combine to fork over 20 threads and calculate the expected limits.
- knows not to re-run cards that already eixst under the same tag, but can be forced to via the `-f` parameter.
- can run on a subset of samples via the `--includeAny` and `--includeAll` option, e.g. `--includeAll generic-mPhi300` will only run samples that contain 'generic' and 'mPhi300' in the name, `--includeAny generic-mPhi300` will run samples that include 'generic' or 'mPhi300' in the name.
- can run all quantiles when running toys with `--quantiles`.
- can run on a subset of samples defined in a .txt file via the `--file` option.
- can be ran 'dry' such that it will not actually run/submit anything with the `--dry` option.

See the script for more information.

Some examples:

e.g. running asymptotic limits for all mS = 125 GeV samples via slurm with setting min and max values on the signal strength `r`:
```bash
python runcombine.py -a ggf-offline.yaml -M AsymptoticLimits -i my_tag --includeAny mS125 -m slurm -o " --rMax 10000 --rMin 0.1 "
```

e.g. running toys (need to run separately for observed, and each 'quanile': expected (0.5), +/-1 sigma (0.84, 0.16), and +/-2 sigma (0.975, 0.025)). Note that these are very computationally intensive, and work best when you are able to split them across several cores, for this example we use 10. 
```bash
python runcombine.py -a ggf-offline.yaml -m condor -i my_tag -M HybridNew -o " --fork 10 "                            # observed
python runcombine.py -a ggf-offline.yaml -m condor -i my_tag -M HybridNew -o " --expectedFromGrid 0.025 --fork 10 "   # -2 sigma
python runcombine.py -a ggf-offline.yaml -m condor -i my_tag -M HybridNew -o " --expectedFromGrid 0.975 --fork 10 "   # +2 sigma
python runcombine.py -a ggf-offline.yaml -m condor -i my_tag -M HybridNew -o " --expectedFromGrid 0.500 --fork 10 "   # expected
python runcombine.py -a ggf-offline.yaml -m condor -i my_tag -M HybridNew -o " --expectedFromGrid 0.840 --fork 10 "   # +1 sigma
python runcombine.py -a ggf-offline.yaml -m condor -i my_tag -M HybridNew -o " --expectedFromGrid 0.160 --fork 10 "   # -1 sigma
```
Alternatively, use the option `--quantiles` to run them all at the same time,
```bash
python runcombine.py -a ggf-offline.yaml -m condor -i my_tag -M HybridNew -o " --fork 10 " --quantiles                # runs all quantiles and observed
```
As aforementioned, toys also work best when the `r` space is constrained,
```bash
python runcombine.py -a ggf-offline.yaml -m condor -i my_tag -M HybridNewAuto -o " --fork 10 " --quantiles                # runs all quantiles and observed, running first toys to constrain the --rMin and --rMax dynamically
```

Some notes on running the limits:
- Use `--fork` in the combine command if you are having memory issues.
- Set `--rMax` and `--rMin` if limits are not converging, check the logs, they should say when you are hitting the limits.
- Set `--rAbsAcc` and `--rRelAcc` by hand; make sure that these are smaller than the ~1 sigma bands.

## 5. Monitoring, Plotting and additional tools

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
