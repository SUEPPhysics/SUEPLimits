import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import yaml
import uproot
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

# Shape closure systematic applied to data (from F/C)
shape_extrapolated_Bin0 = { # Bin0 is used as validation region and therefore not anymore in combine fit
    "2016" : 1.01,
    "2017" : 1.01,
    "2018" : 1.01,
    "all": 1.01
}
shape_extrapolated_Bin1 = {
    "2016" : 1.14,
    "2017" : 1.20,
    "2018" : 1.15,
    "all": 1.16
}
shape_extrapolated_Bin2 = {
    "2016" : 1.28,
    "2017" : 1.43,
    "2018" : 1.32,
    "all": 1.55
}
shape_extrapolated_Bin3 = {
    "2016" : 1.5,
    "2017" : 1.76,
    "2018" : 1.56,
    "all": 2.0
}
shape_extrapolated_Bin4 = {
    "2016" : 2.00,
    "2017" : 2.00,
    "2018" : 2.00,
    "all": 2.00
}

# ABCD closure systematic applied to data (from ISR)
closure_systs = {
    "2016": 1.08,
    "2017": 1.08,
    "2018": 1.08
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
    parser.add_argument("-i"  , "--input"   , type=str, default="config/SUEP_inputs_2018.yaml")
    parser.add_argument("-tag"  , "--tag"   , type=str, default=".")
    parser.add_argument("-v"  , "--variable", type=str, default="nCleaned_Cands")
    parser.add_argument("-c"  , "--channel" , nargs='+', type=str)
    parser.add_argument("-s"  , "--signal"  , nargs='+', type=str)
    parser.add_argument("-t"  , "--stack"   , nargs='+', type=str)
    parser.add_argument("-era", "--era"     , type=str, default="2017")
    parser.add_argument("-f"  , "--force"   , action="store_true")
    parser.add_argument("-ns" , "--nostatuncert", action="store_false")
    parser.add_argument("--rebin" ,type=int, default=1)
    parser.add_argument("--bins",'--list', nargs='*', help='<Required> Set flag', required=False,default=[])
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

    if len(options.channel) == 1:
        options.channel = options.channel[0]
    
    # make datasets per process
    datasets = {}
    nsignals = 0
    signal = ""
    for dg in options.stack:
        logging.info(dg)
        p = ftool.ggf_datagroup( 
            inputs[dg]["files"],
            ptype      = inputs[dg]["type"], 
            observable = options.variable,
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
            p_merge = ftool.ggf_datagroup(
                inputs2016apv[sample2016apv]["files"],
                ptype      = inputs2016apv[sample2016apv]["type"],
                observable = options.variable,
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

        datasets[p.name] = p
        if p.ptype == "signal":
            signal = p.name

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

    data_obs = datasets.get("data").get("nom") 
    card.add_observation(data_obs)

    for n, p in datasets.items():
        name = "Signal" if p.ptype=="signal" else p.name
        if p.ptype=="data" and p.name == "data": continue #Skip the data_obs

        #Look at expected and add in the rate_params
        card.add_nominal(name,options.channel, p.get("nom"))
        if "Sig" in options.channel:
            if p.name == "expected" and p.ptype == "data" :
                
                if "Bin1" in options.channel:
                    Bin_cr = "Bin1crF"
                    shape_syst = shape_extrapolated_Bin1[options.era]
                if "Bin2" in options.channel:
                    Bin_cr = "Bin2crF"
                    shape_syst = shape_extrapolated_Bin2[options.era]
                if "Bin3" in options.channel:
                    Bin_cr = "Bin3crF"
                    shape_syst = shape_extrapolated_Bin3[options.era]
                if "Bin4" in options.channel:
                    Bin_cr = "Bin4crF"
                    shape_syst = shape_extrapolated_Bin4[options.era]
                    
                # real
                closure_syst = closure_systs[options.era]
                
                # correlated between years, bins
                #N/A
                
                # correlated between the bins, uncorrelated between years
                card.add_nuisance(name, "{:<21}  lnN".format("Closure_{}".format(options.era)), closure_syst)
                card.add_nuisance(name, "{:<21}  lnN".format("Shape_{}".format(options.era)), shape_syst)

                # uncorrelated systematics between the bins
                card.add_ABCD_rate_param("r" + options.era + "_" + options.channel, options.channel + options.era, name, options.era, Bin_cr )

        else:
            rate_nom = p.get("nom").values().sum()
            rate_up = rate_nom*5
            rate_down = 0
            if rate_up == 0: 
                rate_nom = 0.0001
                rate_up = 20
                rate_down = 0
            if p.name == "expected" and p.ptype == "data" :
                card.add_rate_param("r" + options.era + "_" + options.channel, options.channel + options.era, name, rate=rate_nom, vmin=rate_down, vmax=rate_up )

        if p.ptype=="data": continue #Now that we have expected nom we skip data

        # add rate param
        
        #Add lnN nuisances
        card.add_nuisance(name, "{:<21}  lnN".format("CMS_lumi_uncorr_{}".format(options.era)), lumi_uncorr[options.era])
        card.add_nuisance(name, "{:<21}  lnN".format("CMS_lumi_corr"), lumi_corr[options.era])
        if options.era in ["2017","2018"]:
            card.add_nuisance(name, "{:<21}  lnN".format("CMS_lumi_corr1718"), lumi_corr1718[options.era])

        #Shape based uncertainties
        card.add_shape_nuisance(name, "CMS_JES_{}".format(options.era), p.get("JES"))
        card.add_shape_nuisance(name, "CMS_JER", p.get("JER"))
        card.add_shape_nuisance(name, "CMS_PU", p.get("puweights"))
        card.add_shape_nuisance(name, "CMS_trigSF_{}".format(options.era), p.get("trigSF"))
        card.add_shape_nuisance(name, "CMS_PS_ISR_{}".format(options.era), p.get("PSWeight_ISR"))
        card.add_shape_nuisance(name, "CMS_PS_FSR_{}".format(options.era), p.get("PSWeight_FSR"))
        card.add_shape_nuisance(name, "CMS_trk_kill_{}".format(options.era), p.get("track"))
        if options.era == "2016" or options.era == "2017":
             card.add_shape_nuisance(name, "CMS_Prefire", p.get("prefire"))
        if "mS125" in p.name:
             card.add_shape_nuisance(name, "CMS_Higgs", p.get("higgs_weights"))
        card.add_auto_stat()

    logging.info("All done!")
    card.dump()

if __name__ == "__main__":
    main()
