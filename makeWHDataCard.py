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

lumi_uncorr = {
    "2016" : 1.010,
    "2017" : 1.020,
    "2018" : 1.015
}

lumi_corr = {
    "2016" : 1.006,
    "2017" : 1.009,
    "2018" : 1.020
}

lumi_corr1718 = {
    "2017" : 1.006,
    "2018" : 1.002
}

ABCD_yield_systematic = {
    "WJHS": {
        "2018": 1.04,
    },
    "GJHS": {
        "2018": 1.04,
    },
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
    parser.add_argument("-i"  , "--input"   , type=str, default="config/WH_inputs_2018.yaml")
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
    parser.add_argument("--bias", type=str, default=None, help="Name of signal model you want to inject.")
    parser.add_argument("--gamma", action='store_true', help="Use gamma region as your background.")
    parser.add_argument("--verbose", action="store_true", help="Print out more information.")

    options = parser.parse_args()

    if options.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
        
    with open(options.input) as f:
        inputs = yaml.safe_load(f.read())
    if options.era == "2016":
        with open(options.input.replace("2016","2016apv")) as f:
            inputs2016apv = yaml.safe_load(f.read())
    
    # make datasets per process
    datasets = {}
    nsignals = 0
    signal = ""
    for dg in options.stack:
        logging.info(dg)

        observable = options.variable
        if inputs[dg]["type"] == "signal":
            if signal == "":
                signal = dg
            else:
                raise ValueError("I wasn't expecting multiple signals in the same card.")
            if 'GJ' in options.channel:
                if options.gamma:
                    # in this case, use gamma as background, and signal as signal
                    observable = options.variable.replace("VRGJhighS", "SR")
                else:
                    # skip signal in gamma+jets region
                    continue
            
        p = ftool.wh_datagroup( 
            inputs[dg]["files"],
            ptype      = inputs[dg]["type"], 
            observable = observable,
            era        = options.era,
            name       = dg,
            kfactor    = inputs[dg].get("kfactor", 1.0),
            channel    = options.channel,
            rebin      = options.rebin,
            bins       = options.bins,
            luminosity = lumis[options.era],
            xsections  = xs_scale(inputs[dg].get("sample", dg), options.era) if inputs[dg]["type"] == "signal" else 1,
            normalise  = (inputs[dg]["type"] == "signal")
        )

        # merge 2016apv with 2016
        if options.era == "2016":
            sample2016apv = dg.replace("2016","2016apv").replace("UL16", "UL16APV")
            logging.info("Merging with 2016apv sample: " + sample2016apv)
            p_merge = ftool.wh_datagroup(
                inputs2016apv[sample2016apv]["files"],
                ptype      = inputs2016apv[sample2016apv]["type"],
                observable = observable,
                era        = "2016apv",
                name       = sample2016apv,
                kfactor    = inputs2016apv[sample2016apv].get("kfactor", 1.0),
                channel    = options.channel,
                rebin      = options.rebin,
                bins       = options.bins,
                luminosity = lumis["2016apv"],
                xsections  = xs_scale(inputs2016apv[sample2016apv].get("sample", sample2016apv), "2016apv") if inputs2016apv[sample2016apv]["type"] == "signal" else 1,
                normalise  = (inputs2016apv[sample2016apv]["type"] == "signal")
            )
            p.add(p_merge)

        if options.bias and inputs[dg]["type"] != "signal":
            logging.info("Injecting signal in data.")
            # Note this is a lazy way to do this, we should generate toys instead of adding the same signal we are extracting
            p_bias = ftool.wh_datagroup(
                inputs[options.bias]["files"],
                ptype      = "signal",
                observable = observable,
                era        = options.era,
                name       = options.bias,
                kfactor    = inputs[options.bias].get("kfactor", 1.0),
                channel    = options.channel,
                rebin      = options.rebin,
                bins       = options.bins,
                luminosity = lumis[options.era],
                xsections  = xs_scale(inputs[options.bias].get("sample", options.bias), options.era),
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
                card.add_9ABCD_rate_param("r" + options.era + "_" + options.channel, options.channel + options.era, name, options.era, bin_cr=Bin_cr, region=region)
                
                # add systematics for the ABCD prediction

                # correlated between the regions, bins, uncorrelated between years
                # TODO need to derive these values. non closure?
                # NB assuming that options.channel looks something like "WJHScrF1"
                card.add_nuisance(name, "{:<21}  lnN".format("ABCD_yield_{}_{}".format(region, options.era)), ABCD_yield_systematic[region][options.era])

        else:
            rate_nom = p.get("nom").values().sum()
            # minor workaround for MC
            if rate_nom < 0:
                rate_nom = 0
            rate_up = rate_nom*5
            rate_down = 0
            if rate_up == 0: 
                rate_nom = 0.0001
                rate_up = 20
                rate_down = 0
            if "expected" in p.name and p.ptype == "data" :
                card.add_rate_param("r" + options.era + "_" + options.channel, options.channel + options.era, name, rate=rate_nom, vmin=rate_down, vmax=rate_up )

        if p.ptype=="data": continue #Now that we have expected nom we skip data

        # add rate param
        
        #Add lnN nuisances
        card.add_nuisance(name, "{:<21}  lnN".format("CMS_lumi_uncorr_{}".format(options.era)), lumi_uncorr[options.era])
        card.add_nuisance(name, "{:<21}  lnN".format("CMS_lumi_corr"), lumi_corr[options.era])
        if options.era in ["2017","2018"]:
            card.add_nuisance(name, "{:<21}  lnN".format("CMS_lumi_corr1718"), lumi_corr1718[options.era])

        #Shape based uncertainties
        # TODO missing: trigger SFs!
        card.add_shape_nuisance(name, "CMS_JES_{}".format(options.era), p.get("JES"))
        card.add_shape_nuisance(name, "CMS_JER", p.get("JER"))
        card.add_shape_nuisance(name, "CMS_PU", p.get("puweights"))
        # card.add_shape_nuisance(name, "CMS_trigSF_{}".format(options.era), p.get("trigSF"))
        card.add_shape_nuisance(name, "CMS_PS_ISR_{}".format(options.era), p.get("PSWeight_ISR"))
        card.add_shape_nuisance(name, "CMS_PS_FSR_{}".format(options.era), p.get("PSWeight_FSR"))
        card.add_shape_nuisance(name, "CMS_trk_kill_{}".format(options.era), p.get("track"))
        card.add_shape_nuisance(name, "CMS_Higgs", p.get("higgs_weights"))
        card.add_shape_nuisance(name, "CMS_LepSFEl", p.get("LepSFEl"))
        card.add_shape_nuisance(name, "CMS_LepSFMu", p.get("LepSFMu"))
        card.add_shape_nuisance(name, "CMS_bTagWeight_HFcorrelated", p.get("bTagWeight_HFcorrelated"))
        card.add_shape_nuisance(name, "CMS_bTagWeight_HFuncorrelated", p.get("bTagWeight_HFuncorrelated"))
        card.add_shape_nuisance(name, "CMS_bTagWeight_LFcorrelated", p.get("bTagWeight_LFcorrelated"))
        card.add_shape_nuisance(name, "CMS_bTagWeight_LFuncorrelated", p.get("bTagWeight_LFuncorrelated"))
        if options.era in ["2016apv", "2016", "2017"]:
             card.add_shape_nuisance(name, "CMS_Prefire", p.get("prefire"))
             
    card.add_auto_stat()

    logging.info("All done!")
    card.dump()

if __name__ == "__main__":
    main()
