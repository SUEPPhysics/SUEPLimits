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
        "CMS_scale_j": ["JES_up", "JES_down"],
        "ps_isr": ["PSWeight_ISR_up", "PSWeight_ISR_down"],
        "ps_fsr": ["PSWeight_FSR_up", "PSWeight_FSR_down"],
        "CMS_EXO24030_tracking": ["track_up", "track_down"],
        "CMS_res_j": ["JER_up", "JER_down"],
        "CMS_scale_met_unclustered_energy": ["Unclustered_up", "Unclustered_down"],
        "CMS_pileup": ["puweights_up", "puweights_down"],
        "CMS_eff_e": ["LepSFElUp", "LepSFElDown"],
        "CMS_eff_m": ["LepSFMuUp", "LepSFMuDown"],
        "CMS_EXO24030_btag_heavy_corr": ["bTagWeight_HFcorrelated_Up", "bTagWeight_HFcorrelated_Dn"],
        "CMS_EXO24030_btag_heavy_uncorr": ["bTagWeight_HFuncorrelated_Up", "bTagWeight_HFuncorrelated_Dn"],
        "CMS_EXO24030_btag_light_corr": ["bTagWeight_LFcorrelated_Up", "bTagWeight_LFcorrelated_Dn"],
        "CMS_EXO240030_btag_light_uncorr": ["bTagWeight_LFuncorrelated_Up", "bTagWeight_LFuncorrelated_Dn"],
        "CMS_scale_m": ["MuScaleUp", "MuScaleDown"],
    },
    "2017": {
        "CMS_scale_j": ["JES_up", "JES_down"],
        "ps_isr": ["PSWeight_ISR_up", "PSWeight_ISR_down"],
        "ps_fsr": ["PSWeight_FSR_up", "PSWeight_FSR_down"],
        "CMS_EXO24030_tracking": ["track_up", "track_down"],
        "CMS_l1_ecal_prefiring": ["prefire_up", "prefire_down"],
        "CMS_res_j": ["JER_up", "JER_down"],
        "CMS_scale_met_unclustered_energy": ["Unclustered_up", "Unclustered_down"],
        "CMS_pileup": ["puweights_up", "puweights_down"],
        "CMS_eff_e": ["LepSFElUp", "LepSFElDown"],
        "CMS_eff_m": ["LepSFMuUp", "LepSFMuDown"],
        "CMS_EXO24030_btag_heavy_corr": ["bTagWeight_HFcorrelated_Up", "bTagWeight_HFcorrelated_Dn"],
        "CMS_EXO24030_btag_heavy_uncorr": ["bTagWeight_HFuncorrelated_Up", "bTagWeight_HFuncorrelated_Dn"],
        "CMS_EXO24030_btag_light_corr": ["bTagWeight_LFcorrelated_Up", "bTagWeight_LFcorrelated_Dn"],
        "CMS_EXO240030_btag_light_uncorr": ["bTagWeight_LFuncorrelated_Up", "bTagWeight_LFuncorrelated_Dn"],
        "CMS_scale_m": ["MuScaleUp", "MuScaleDown"],
    },
    "2016": {
        "CMS_scale_j": ["JES_up", "JES_down"],
        "ps_isr": ["PSWeight_ISR_up", "PSWeight_ISR_down"],
        "ps_fsr": ["PSWeight_FSR_up", "PSWeight_FSR_down"],
        "CMS_EXO24030_tracking": ["track_up", "track_down"],
        "CMS_l1_ecal_prefiring": ["prefire_up", "prefire_down"],
        "CMS_res_j": ["JER_up", "JER_down"],
        "CMS_scale_met_unclustered_energy": ["Unclustered_up", "Unclustered_down"],
        "CMS_pileup": ["puweights_up", "puweights_down"],
        "CMS_eff_e": ["LepSFElUp", "LepSFElDown"],
        "CMS_eff_m": ["LepSFMuUp", "LepSFMuDown"],
        "CMS_EXO24030_btag_heavy_corr": ["bTagWeight_HFcorrelated_Up", "bTagWeight_HFcorrelated_Dn"],
        "CMS_EXO24030_btag_heavy_uncorr": ["bTagWeight_HFuncorrelated_Up", "bTagWeight_HFuncorrelated_Dn"],
        "CMS_EXO24030_btag_light_corr": ["bTagWeight_LFcorrelated_Up", "bTagWeight_LFcorrelated_Dn"],
        "CMS_EXO24030_btag_light_uncorr": ["bTagWeight_LFuncorrelated_Up", "bTagWeight_LFuncorrelated_Dn"],
        "CMS_scale_m": ["MuScaleUp", "MuScaleDown"],
    },
    "2016apv": {
        "CMS_scale_j": ["JES_up", "JES_down"],
        "ps_isr": ["PSWeight_ISR_up", "PSWeight_ISR_down"],
        "ps_fsr": ["PSWeight_FSR_up", "PSWeight_FSR_down"],
        "CMS_EXO24030_tracking": ["track_up", "track_down"],
        "CMS_l1_ecal_prefiring": ["prefire_up", "prefire_down"],
        "CMS_res_j": ["JER_up", "JER_down"],
        "CMS_scale_met_unclustered_energy": ["Unclustered_up", "Unclustered_down"],
        "CMS_pileup": ["puweights_up", "puweights_down"],
        "CMS_eff_e": ["LepSFElUp", "LepSFElDown"],
        "CMS_eff_m": ["LepSFMuUp", "LepSFMuDown"],
        "CMS_EXO24030_btag_heavy_corr": ["bTagWeight_HFcorrelated_Up", "bTagWeight_HFcorrelated_Dn"],
        "CMS_EXO24030_btag_heavy_uncorr": ["bTagWeight_HFuncorrelated_Up", "bTagWeight_HFuncorrelated_Dn"],
        "CMS_EXO24030_btag_light_corr": ["bTagWeight_LFcorrelated_Up", "bTagWeight_LFcorrelated_Dn"],
        "CMS_EXO240030_btag_light_uncorr": ["bTagWeight_LFuncorrelated_Up", "bTagWeight_LFuncorrelated_Dn"],
        "CMS_scale_m": ["MuScaleUp", "MuScaleDown"],
    }
}

ABCD_yield_systematic = {
    "bkg": 1.04,
    #"GJHS": 1.04
}
ABCD_shape_systematic = {
    # "WJHSsr0": 1.005,
    # "WJHSsr1": 1.05,
    # "WJHSsr2": 1.05,
    # "WJHSsr3": 1.5,
    # "WJHSsr4": 2.0,
    "SR_SR_SRbin0": 1.005,
    "SR_SR_SRbin1": 1.05,
    "SR_SR_SRbin2": 1.05,
    "SR_SR_SRbin3": 1.2,
    "SR_SR_SRbin4": 2.0,
    # "GJHSsr0": 1.005,
    # "GJHSsr1": 1.05,
    # "GJHSsr2": 1.05,
    # "GJHSsr3": 1.5,
    # "GJHSsr4": 2.0,
    # "GJHSsr0": 1.0,
    # "GJHSsr1": 1.0,
    # "GJHSsr2": 1.0,
    # "GJHSsr3": 1.0,
    # "GJHSsr4": 1.0,
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
    parser.add_argument("--bins",'--list', nargs='*', help='<Required> Set flag', required=False,default=[])
    parser.add_argument("--biasSample", type=str, default=None, help="Name of signal model you want to inject.")
    parser.add_argument("--biasStrength", type=float, default=1.0, help="Strength of signal model you want to inject.")
    parser.add_argument("--dcname", type=str, required=False, default='', help="Name of the datacard to be created.")
    parser.add_argument("--gamma", action='store_true', help="Use gamma region as your background.")
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
        card_name = options.channel 
    elif isinstance(options.channel, list):
        if np.all(["signal" in c.lower() for c in options.channel]):
            card_name = "catSig"+options.era

    card = ftool.datacard(
        name = signal,
        channel= card_name,
        tag = options.tag,
        analysis="CMS_EXO24030",
        dcname=options.dcname,
    )
    card.shapes_headers()

    card.process_indx_map = {
        "Signal" : 0,
        #"WJHSdata" : 1,
        "bkg" : 1,
        #"WJLSdata" : 3,
        # "WJLSexpected" : 4,
        # "GJLSdata" : 5,
        # "GJLSexpected" : 6,
        # "GJHSdata" : 7,
        # "GJHSexpected" : 8
    }

    # add the observed data for this channel
    # since this can be 'data', 'dataCRWJ', 'dataVRGJlowS', etc. we need to loop over all data samples to find it
    data_samples = []
    for _, p in datasets.items():
        if p.ptype != 'data': continue
        if 'obs' in p.name: data_samples.append(dg)
    if len(data_samples) != 1: raise Exception("Need exactly one data sample, found {}".format(len(data_samples)))
    data_sample = data_samples[0]
    data_obs = datasets[data_sample].get("nom") 
    data_obs[:] = np.stack([np.where(data_obs.values() > 0, data_obs.values(), 0), data_obs.variances()], axis=-1) # workaround for MC edge cases
    card.add_observation(data_obs)

    for n, p in datasets.items():
        name = "Signal" if p.ptype=="signal" else p.name
        if p.ptype=="data" and p.name == data_sample: continue #Skip the data_obs

        #Look at expected and add in the rate_params
        card.add_nominal(name, options.channel, p.get("nom"))
        if "SR_SR" in options.channel:
            if "bkg" in p.name and p.ptype == "data" :

                # the bin of the F histogram that is used for the ABCD prediction of this channel 
                Bin_cr = options.channel.replace("SR_SR_SR","SR_F_F")

                # ABCD prediction as a rate parameter
                card.add_9ABCD_rate_param(
                    "CMS_EXO24030_" + options.channel,
                    options.channel,
                    process=name,
                    bin_cr=Bin_cr,
                    region="SR"
                )
                
                # add systematics for the ABCD prediction

                # correlated between the regions, bins, uncorrelated between years
                # NB assuming that options.channel looks something like "SR_SR_SRbin1" since we use the last character to determine the bin
                card.add_nuisance(name, "{:<21}  lnN".format("CMS_EXO24030_ABCDClosure_Yield"), ABCD_yield_systematic[name])
                card.add_nuisance(name, "{:<21}  lnN".format("CMS_EXO24030_ABCDClosure_bin" + options.channel[-1]), ABCD_shape_systematic[options.channel])

        elif ("bkg" in p.name and p.ptype == "data"):
            rate_nom = max(p.get("nom").values().sum(), 0)
            rate_up = rate_nom*5
            rate_down = 0
            if rate_up == 0: 
                rate_nom = 0.0001
                rate_up = 20
                rate_down = 0

            card.add_rate_param(
                "CMS_EXO24030_" + options.channel,
                options.channel,
                name,
                rate=rate_nom,
                vmin=rate_down,
                vmax=rate_up
            )

        if p.ptype=="data": continue #Now that we have expected nom we skip data

        # add manual MC stats
        card.add_manual_MCstats(name)

        # add nuisances
        # TODO missing: trigger SFs!
        # card.add_shape_nuisance(name, "trigSF_{}".format(options.era), p.get("trigSF"))
        card.add_shape_nuisance(name, "CMS_scale_j", p.get("CMS_scale_j"))
        card.add_shape_nuisance(name, "CMS_res_j", p.get("CMS_res_j"))
        card.add_shape_nuisance(name, "CMS_pileup", p.get("CMS_pileup"))
        card.add_shape_nuisance(name, "CMS_scale_met_unclustered_energy", p.get("CMS_scale_met_unclustered_energy"))
        card.add_shape_nuisance(name, "ps_fsr", p.get("ps_fsr"))
        card.add_shape_nuisance(name, "ps_isr", p.get("ps_isr"))
        card.add_shape_nuisance(name, "CMS_EXO24030_tracking", p.get("CMS_EXO24030_tracking"))
        card.add_shape_nuisance(name, "CMS_eff_e", p.get("CMS_eff_e"))
        card.add_shape_nuisance(name, "CMS_eff_m", p.get("CMS_eff_m"))
        card.add_shape_nuisance(name, "CMS_scale_m", p.get("CMS_scale_m"))
        card.add_shape_nuisance(name, "CMS_EXO24030_btag_heavy_corr", p.get("CMS_EXO24030_btag_heavy_corr"))
        card.add_shape_nuisance(name, "CMS_EXO24030_btag_heavy_uncorr", p.get("CMS_EXO24030_btag_heavy_uncorr"))
        card.add_shape_nuisance(name, "CMS_EXO24030_btag_light_corr", p.get("CMS_EXO24030_btag_light_corr"))
        card.add_shape_nuisance(name, "CMS_EXO240030_btag_light_uncorr", p.get("CMS_EXO240030_btag_light_uncorr"))
        card.add_shape_nuisance(name, "CMS_l1_ecal_prefiring", p.get("CMS_l1_ecal_prefiring"))
        card.add_nuisance(name, "{:<21}  lnN".format("lumi_13TeV"), 1.016)
             
    card.dump()
    logging.info("All done!")

if __name__ == "__main__":
    main()
