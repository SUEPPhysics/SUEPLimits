import yaml
import uproot
import os, sys
import argparse
import ftool
import numpy as np
from termcolor import colored
import logging
import json

# from: https://twiki.cern.ch/twiki/bin/viewauth/CMS/LumiRecommendationsRun2#Combination_and_correlations
lumis = {
    "2016apv":  19.497, 
    "2016" : 16.811,
    "2017" : 41.471,
    "2018" : 59.817
}

signal_variations = {
    "2018": {
        # era dependent
        "Lumi_Uncorr_18": 1.015,
        "Lumi_Corr_1718": 1.002,
        "JES_18": ["JES_up", "JES_down"],
        "PS_ISR_18": ["PSWeight_ISR_up", "PSWeight_ISR_down"],
        "PS_FSR_18": ["PSWeight_FSR_up", "PSWeight_FSR_down"],
        "Track_Eff_18": ["track_up", "track_down"],
        # era independent
        "Lumi_Corr": 1.020,
        "JER": ["JER_up", "JER_down"],
        "Unclustered": ["Unclustered_up", "Unclustered_down"],
        "PU": ["puweights_up", "puweights_down"],
        "HiggsPt_Reweight": ["higgs_weights_up", "higgs_weights_down"],
        "LepSF_El": ["LepSFElUp", "LepSFElDown"],
        "LepSF_Mu": ["LepSFMuUp", "LepSFMuDown"],
        "BTag_HFcorrelated": ["bTagWeight_HFcorrelated_Up", "bTagWeight_HFcorrelated_Dn"],
        "BTag_HFuncorrelated": ["bTagWeight_HFuncorrelated_Up", "bTagWeight_HFuncorrelated_Dn"],
        "BTag_LFcorrelated": ["bTagWeight_LFcorrelated_Up", "bTagWeight_LFcorrelated_Dn"],
        "BTag_LFuncorrelated": ["bTagWeight_LFuncorrelated_Up", "bTagWeight_LFuncorrelated_Dn"],
        "MuScale": ["MuScaleUp", "MuScaleDown"],
    },
    "2017": {
        # era dependent
        "Lumi_Uncorr_17": 1.009,
        "Lumi_Corr_1718": 1.006,
        "JES_17": ["JES_up", "JES_down"],
        "PS_ISR_17": ["PSWeight_ISR_up", "PSWeight_ISR_down"],
        "PS_FSR_17": ["PSWeight_FSR_up", "PSWeight_FSR_down"],
        "Track_Eff_17": ["track_up", "track_down"],
        # era independent
        "Lumi_Corr": 1.020,
        "Prefire": ["prefire_up", "prefire_down"],
        "JER": ["JER_up", "JER_down"],
        "Unclustered": ["Unclustered_up", "Unclustered_down"],
        "PU": ["puweights_up", "puweights_down"],
        "HiggsPt_Reweight": ["higgs_weights_up", "higgs_weights_down"],
        "LepSF_El": ["LepSFElUp", "LepSFElDown"],
        "LepSF_Mu": ["LepSFMuUp", "LepSFMuDown"],
        "BTag_HFcorrelated": ["bTagWeight_HFcorrelated_Up", "bTagWeight_HFcorrelated_Dn"],
        "BTag_HFuncorrelated": ["bTagWeight_HFuncorrelated_Up", "bTagWeight_HFuncorrelated_Dn"],
        "BTag_LFcorrelated": ["bTagWeight_LFcorrelated_Up", "bTagWeight_LFcorrelated_Dn"],
        "BTag_LFuncorrelated": ["bTagWeight_LFuncorrelated_Up", "bTagWeight_LFuncorrelated_Dn"],
        "MuScale": ["MuScaleUp", "MuScaleDown"],
    },
    "2016": {
        # era dependent
        "Lumi_Uncorr_16": 1.010,
        "JES_16": ["JES_up", "JES_down"],
        "PS_ISR_16": ["PSWeight_ISR_up", "PSWeight_ISR_down"],
        "PS_FSR_16": ["PSWeight_FSR_up", "PSWeight_FSR_down"],
        "Track_Eff_16": ["track_up", "track_down"],
        # era independent
        "Lumi_Corr": 1.006,
        "Prefire": ["prefire_up", "prefire_down"],
        "JER": ["JER_up", "JER_down"],
        "Unclustered": ["Unclustered_up", "Unclustered_down"],
        "PU": ["puweights_up", "puweights_down"],
        "HiggsPt_Reweight": ["higgs_weights_up", "higgs_weights_down"],
        "LepSF_El": ["LepSFElUp", "LepSFElDown"],
        "LepSF_Mu": ["LepSFMuUp", "LepSFMuDown"],
        "BTag_HFcorrelated": ["bTagWeight_HFcorrelated_Up", "bTagWeight_HFcorrelated_Dn"],
        "BTag_HFuncorrelated": ["bTagWeight_HFuncorrelated_Up", "bTagWeight_HFuncorrelated_Dn"],
        "BTag_LFcorrelated": ["bTagWeight_LFcorrelated_Up", "bTagWeight_LFcorrelated_Dn"],
        "BTag_LFuncorrelated": ["bTagWeight_LFuncorrelated_Up", "bTagWeight_LFuncorrelated_Dn"],
        "MuScale": ["MuScaleUp", "MuScaleDown"],
    },
    "2016apv": {
        # era dependent
        "Lumi_Uncorr_16": 1.010,
        "JES_16": ["JES_up", "JES_down"],
        "PS_ISR_16": ["PSWeight_ISR_up", "PSWeight_ISR_down"],
        "PS_FSR_16": ["PSWeight_FSR_up", "PSWeight_FSR_down"],
        "Track_Eff_16": ["track_up", "track_down"],
        # era independent
        "Lumi_Corr": 1.006,
        "Prefire": ["prefire_up", "prefire_down"],
        "JER": ["JER_up", "JER_down"],
        "Unclustered": ["Unclustered_up", "Unclustered_down"],
        "PU": ["puweights_up", "puweights_down"],
        "HiggsPt_Reweight": ["higgs_weights_up", "higgs_weights_down"],
        "LepSF_El": ["LepSFElUp", "LepSFElDown"],
        "LepSF_Mu": ["LepSFMuUp", "LepSFMuDown"],
        "BTag_HFcorrelated": ["bTagWeight_HFcorrelated_Up", "bTagWeight_HFcorrelated_Dn"],
        "BTag_HFuncorrelated": ["bTagWeight_HFuncorrelated_Up", "bTagWeight_HFuncorrelated_Dn"],
        "BTag_LFcorrelated": ["bTagWeight_LFcorrelated_Up", "bTagWeight_LFcorrelated_Dn"],
        "BTag_LFuncorrelated": ["bTagWeight_LFuncorrelated_Up", "bTagWeight_LFuncorrelated_Dn"],
        "MuScale": ["MuScaleUp", "MuScaleDown"],
    }
}

# ABCD_yield_systematic = {
#     "WJHS": 1.04,
#     "GJHS": 1.04
#     #"GJHS": 1.00
# }
# ABCD_shape_systematic = {
#     "WJHSsr0": 1.005,
#     "WJHSsr1": 1.05,
#     "WJHSsr2": 1.05,
#     "WJHSsr3": 1.5,
#     "WJHSsr4": 2.0,
#     "GJHSsr0": 1.005,
#     "GJHSsr1": 1.05,
#     "GJHSsr2": 1.05,
#     "GJHSsr3": 1.5,
#     "GJHSsr4": 2.0,
#     # "GJHSsr0": 1.0,
#     # "GJHSsr1": 1.0,
#     # "GJHSsr2": 1.0,
#     # "GJHSsr3": 1.0,
#     # "GJHSsr4": 1.0,
# }
ABCD_yield_systematic = {
    "WJHS": 1.04,
}
ABCD_shape_systematic = {
    "WJHSmusr0": 1.01,
    "WJHSmusr1": 1.05,
    "WJHSmusr2": 1.05,
    "WJHSmusr3": 1.05,
    "WJHSmusr4": 2.0,
    "WJHSesr0": 1.00,
    "WJHSesr1": 1.04,
    "WJHSesr2": 1.04,
    "WJHSesr3": 1.04,
    "WJHSesr4": 2.0,
}


def xs_scale(proc, era):
    xsec = 1.0
    xsec_file = f"config/xsections_{era}.json"
    with open(xsec_file) as file:
        MC_xsecs = json.load(file)
    xsec  = MC_xsecs[proc]["xsec"]
    xsec *= MC_xsecs[proc]["kr"]
    xsec *= MC_xsecs[proc]["br"]
    xsec *= 1000.0
    assert xsec > 0, "{} has a null cross section!".format(proc)
    return xsec

def main():
    parser = argparse.ArgumentParser(description='The Creator of Combinators')
    parser.add_argument("-i"  , "--input"   , type=str, default="config/WH_inputs_{era}.yaml")
    parser.add_argument("-t"  , "--tag"   , type=str, default=".")
    parser.add_argument("-v"  , "--variable", type=str, required=True)
    parser.add_argument("-c"  , "--channel" , type=str)
    parser.add_argument("-s"  , "--signal"  , nargs='+', type=str)
    parser.add_argument("--stack"   , nargs='+', type=str)
    parser.add_argument("-era", "--era"     , type=str, default="2017")
    parser.add_argument("-f"  , "--force"   , action="store_true")
    parser.add_argument("-ns" , "--nostatuncert", action="store_false")
    parser.add_argument("--rebin" ,type=int, default=1)
    parser.add_argument("--flavor", choices=["e", "mu"], required=True)
    parser.add_argument("--bins",'--list', nargs='*', help='<Required> Set flag', required=False,default=[])
    parser.add_argument("--biasSample", type=str, default=None, help="Name of signal model you want to inject.")
    parser.add_argument("--biasStrength", type=float, default=1.0, help="Strength of signal model you want to inject.")
    parser.add_argument("--gamma", action='store_true', help="Use gamma region as your background.")
    parser.add_argument("--agnostic", action='store_true', help="Do signal agnostic datacard.")
    parser.add_argument("--verbose", action="store_true", help="Print out more information.")

    options = parser.parse_args()

    if options.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    logging.info("Starting to make datacard for {} in {}".format(options.variable, options.channel))

    if options.era == 'all':
        eras = ["2016apv", "2016", "2017", "2018"]
    elif options.era == '2016':
        eras = ["2016", "2016apv"]
    else:
        eras = [options.era]
        
    inputs_by_era = {}
    for era in eras:
        with open(options.input.format(era=era)) as f:
            inputs_by_era[era] = yaml.safe_load(f.read())

    active_variations = {era: signal_variations[era] for era in eras}
    for era in eras:
        era_vars = active_variations[era]
        for other_era in active_variations.keys():
            if era == other_era: continue
            for var, val in active_variations[other_era].items():
                if var not in era_vars.keys():
                    era_vars[var] = 1
    
    # make datasets per process
    datasets = {}
    signal = ""
    for dg in options.stack:
        logging.info(dg)

        for iera, era in enumerate(eras):
            logging.info(era)

            observable = options.variable
            if inputs_by_era[era][dg]["type"] == "signal":
                if signal == "":
                    signal = dg
                if signal != dg:
                    raise ValueError("I wasn't expecting multiple signals in the same card.")
                if 'GJ' in options.channel:
                    if options.gamma:
                        # in this case, use gamma as background, and signal as signal
                        observable = options.variable.replace("VRGJhighS", "SR")
                    else:
                        # skip signal in gamma+jets region
                        continue
                
            p_era = ftool.wh_datagroup( 
                inputs_by_era[era][dg]["files"],
                ptype      = inputs_by_era[era][dg]["type"], 
                observable = observable,
                era        = era,
                name       = dg,
                kfactor    = inputs_by_era[era][dg].get("kfactor", 1.0),
                channel    = options.channel,
                rebin      = options.rebin,
                bins       = options.bins,
                luminosity = lumis[era],
                xsections  = xs_scale(inputs_by_era[era][dg].get("sample", dg), era) if inputs_by_era[era][dg]["type"] == "signal" else 1,
                normalise  = (inputs_by_era[era][dg]["type"] == "signal"),
                variations = signal_variations[era] if inputs_by_era[era][dg]["type"] == "signal" else {}
            )
            if iera == 0: 
                p = p_era
            else:
                p.add(p_era)

            if options.biasSample and inputs_by_era[era][dg]["type"] != "signal":
                logging.info("Injecting signal in data.")
                if 'GJ' in options.channel:
                    observable = options.variable.replace("VRGJhighS", "SR")
                # Note this is a lazy way to do this, we should generate toys instead of adding the same signal we are extracting
                p_bias = ftool.wh_datagroup(
                    inputs_by_era[era][options.biasSample]["files"],
                    ptype      = "signal",
                    observable = observable,
                    era        = era,
                    name       = options.biasSample,
                    kfactor    = inputs_by_era[era][options.biasSample].get("kfactor", 1.0) * options.biasStrength,
                    channel    = options.channel,
                    rebin      = options.rebin,
                    bins       = options.bins,
                    luminosity = lumis[era],
                    xsections  = xs_scale(inputs_by_era[era][options.biasSample].get("sample", options.biasSample), era),
                    normalise  = True
                )
                p.add(p_bias)

        datasets[p.name] = p

    card_name = "ch"+options.era
    if isinstance(options.channel, str):
        card_name = options.channel+options.era 
    elif isinstance(options.channel, list):
        if np.all(["signal" in c.lower() for c in options.channel]):
            card_name = "catSig"+options.era

    card = ftool.datacard(
        name = signal,
        channel= card_name,
        tag = options.tag
    )
    card.shapes_headers()

    card.process_indx_map = {
        "Signal" : 0,
        "WJHSdata" : 1,
        "WJHSexpected" : 2,
        "WJLSdata" : 3,
        "WJLSexpected" : 4,
        "GJLSdata" : 5,
        "GJLSexpected" : 6,
        "GJHSdata" : 7,
        "GJHSexpected" : 8
    }

    # add the observed data for this channel
    # since this can be 'data', 'dataCRWJ', 'dataVRGJlowS', etc. we need to loop over all data samples to find it
    data_samples = []
    for _, p in datasets.items():
        if p.ptype != 'data': continue
        if 'data' in p.name: data_samples.append(dg)
    if len(data_samples) != 1: raise Exception("Need exactly one data sample, found {}".format(len(data_samples)))
    data_sample = data_samples[0]
    data_obs = datasets[data_sample].get("nom") 
    data_obs[:] = np.stack([np.where(data_obs.values() > 0, data_obs.values(), 0), data_obs.variances()], axis=-1) # workaround for MC edge cases
    card.add_observation(data_obs)

    for n, p in datasets.items():
        name = "Signal" if p.ptype=="signal" else p.name
        if p.ptype=="data" and p.name == data_sample: continue #Skip the data_obs

        region = ""
        if "WJHS" in options.channel: region = "WJHS"
        elif "WJLS" in options.channel: region = "WJLS"
        elif "GJHS" in options.channel: region = "GJHS"
        elif "GJLS" in options.channel: region = "GJLS"

        #Look at expected and add in the rate_params
        card.add_nominal(name,options.channel, p.get("nom"))
        if "sr" in options.channel:
            if "expected" in p.name and p.ptype == "data" :

                # the bin of the F histogram that is used for the ABCD prediction of this channel 
                Bin_cr = options.channel.replace("sr","crF")

                # ABCD prediction as a rate parameter
                card.add_9ABCD_rate_param("r_" + options.channel + options.era, options.channel + options.era, name, options.era, bin_cr=Bin_cr, region=region + options.flavor)
                
                # add systematics for the ABCD prediction

                # correlated between the regions, bins, uncorrelated between years
                # NB assuming that options.channel looks something like "WJHScrF1"
                card.add_nuisance(name, "{:<21}  lnN".format("ABCD_yield_{}_{}".format(region, options.era)), ABCD_yield_systematic[region])
                card.add_nuisance(name, "{:<21}  lnN".format("ABCD_shape_{}_{}".format(options.channel, options.era)), ABCD_shape_systematic[options.channel])

        else:
            rate_nom = max(p.get("nom").values().sum(), 0)
            rate_up = rate_nom*5
            rate_down = 0
            if rate_up == 0: 
                rate_nom = 0.0001
                rate_up = 20
                rate_down = 0
            if "expected" in p.name and p.ptype == "data":
                card.add_rate_param("r_" + options.channel + options.era, options.channel + options.era, name, rate=rate_nom, vmin=rate_down, vmax=rate_up )

        if p.ptype=="data": continue #Now that we have expected nom we skip data

        # add manual MC stats
        card.add_manual_MCstats(name)

        # no systematics for agnostic
        if options.agnostic: continue

        # add nuisances
        # TODO missing: trigger SFs!
        # card.add_shape_nuisance(name, "trigSF_{}".format(options.era), p.get("trigSF"))
        card.add_shape_nuisance(name, "JES_16", p.get("JES_16"))
        card.add_shape_nuisance(name, "JES_17", p.get("JES_17"))
        card.add_shape_nuisance(name, "JES_18", p.get("JES_18"))
        card.add_shape_nuisance(name, "JER", p.get("JER"))
        card.add_shape_nuisance(name, "PU", p.get("PU"))
        card.add_shape_nuisance(name, "Unclustered", p.get("Unclustered"))
        card.add_shape_nuisance(name, "PS_ISR_16".format(options.era), p.get("PS_ISR_16"))
        card.add_shape_nuisance(name, "PS_ISR_17".format(options.era), p.get("PS_ISR_17"))
        card.add_shape_nuisance(name, "PS_ISR_18".format(options.era), p.get("PS_ISR_18"))
        card.add_shape_nuisance(name, "PS_FSR_18".format(options.era), p.get("PS_FSR_18"))
        card.add_shape_nuisance(name, "PS_FSR_17".format(options.era), p.get("PS_FSR_17"))
        card.add_shape_nuisance(name, "PS_FSR_16".format(options.era), p.get("PS_FSR_16"))
        card.add_shape_nuisance(name, "Track_Eff_18".format(options.era), p.get("Track_Eff_18"))
        card.add_shape_nuisance(name, "Track_Eff_17".format(options.era), p.get("Track_Eff_17"))
        card.add_shape_nuisance(name, "Track_Eff_16".format(options.era), p.get("Track_Eff_16"))
        card.add_shape_nuisance(name, "HiggsPt_Reweight", p.get("HiggsPt_Reweight"))
        card.add_shape_nuisance(name, "LepSF_El", p.get("LepSF_El"))
        card.add_shape_nuisance(name, "LepSF_Mu", p.get("LepSF_Mu"))
        card.add_shape_nuisance(name, "MuScale", p.get("MuScale"))
        card.add_shape_nuisance(name, "BTag_HFcorrelated", p.get("BTag_HFcorrelated"))
        card.add_shape_nuisance(name, "BTag_HFuncorrelated", p.get("BTag_HFuncorrelated"))
        card.add_shape_nuisance(name, "BTag_LFcorrelated", p.get("BTag_LFcorrelated"))
        card.add_shape_nuisance(name, "BTag_LFuncorrelated", p.get("BTag_LFuncorrelated"))
        card.add_shape_nuisance(name, "Prefire", p.get("Prefire"))
        card.add_shape_nuisance(name, "Lumi_Uncorr_18", p.get("Lumi_Uncorr_18"))
        card.add_shape_nuisance(name, "Lumi_Uncorr_17", p.get("Lumi_Uncorr_17"))
        card.add_shape_nuisance(name, "Lumi_Uncorr_16", p.get("Lumi_Uncorr_16"))
        card.add_shape_nuisance(name, "Lumi_Corr", p.get("Lumi_Corr"))
        card.add_shape_nuisance(name, "Lumi_Corr_1718", p.get("Lumi_Corr_1718"))
             
    logging.info("All done!")
    card.dump()

if __name__ == "__main__":
    main()
