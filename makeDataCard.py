import yaml
import uproot
import os
import argparse
import ftool
import numpy as np
from termcolor import colored

# from: https://twiki.cern.ch/twiki/bin/viewauth/CMS/LumiRecommendationsRun2#Combination_and_correlations
lumis = {
    "2016" : 16.811, #2016apv lumi 19.498 is applied in ftool
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
shape_Bin0 = { # Bin0 is used as validation region and therefore not anymore in combine fit
    "2016" : 1.01,
    "2017" : 1.01,
    "2018" : 1.01
}
shape_Bin1 = {
    "2016" : 1.14,
    "2017" : 1.20,
    "2018" : 1.15
}
shape_Bin2 = {
    "2016" : 1.40,
    "2017" : 1.80,
    "2018" : 1.50
}
shape_Bin3 = {
    "2016" : 2.0,
    "2017" : 0.65,
    "2018" : 2.0
}
shape_Bin4 = {
    "2016" : 2.00,
    "2017" : 2.00,
    "2018" : 2.00
}

# Statistical variation on F/C
shape_stat_Bin0 = { # Bin0 is used as validation region and therefore not anymore in combine fit
    "2016" : 1.008,
    "2017" : 1.007,
    "2018" : 1.006
}
shape_stat_Bin1 = {
    "2016" : 1.03,
    "2017" : 1.03,
    "2018" : 1.03
}
shape_stat_Bin2 = {
    "2016" : 1.17,
    "2017" : 1.16,
    "2018" : 1.13
}
shape_stat_Bin3 = {
    "2016" : 2.0,
    "2017" : 0.5,
    "2018" : 1.84
}
shape_stat_Bin4 = {
    "2016" : 2.00,
    "2017" : 2.00,
    "2018" : 2.00
}

# ABCD closure systematic applied to data (from ISR)
closure_systs = {
    "2016": 1.08,
    "2017": 1.08,
    "2018": 1.08
}

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
    parser.add_argument("--binrange" ,nargs='+', type=int, default=100)
    parser.add_argument("--rebin" ,type=int, default=1)
    parser.add_argument("--bins",'--list', nargs='*', help='<Required> Set flag', required=False,default=[])

    options = parser.parse_args()
    
    print("range =", options.binrange)
    
    inputs = None
    with open(options.input) as f:
        try:
            inputs = yaml.safe_load(f.read())
        except yaml.YAMLError as exc:
            print (exc)

    xsections = None

    if len(options.channel) == 1:
        options.channel = options.channel[0]
    
    xsections = 1.0
    # make datasets per process
    datasets = {}
    nsignals = 0
    signal = ""
    for dg in options.stack:
        print('dg',dg)
        p = ftool.datagroup( 
            inputs[dg]["files"],
            ptype      = inputs[dg]["type"], 
            observable = options.variable,
            era        = options.era,
            name       = dg,
            kfactor    = inputs[dg].get("kfactor", 1.0),
            xsections  = xsections,
            channel    = options.channel,
            rebin      = options.rebin,
            bins = options.bins,
            binrange   = options.binrange,
            luminosity = lumis[options.era]
        )
        #p.save()
        datasets[p.name] = p
        if p.ptype == "signal":
            signal = p.name
    print('datasets!',datasets['data'].get("nom")) #Empty already

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
                    shape_syst = shape_Bin1[options.era]
                    shape_stat = shape_stat_Bin1[options.era]
                if "Bin2" in options.channel:
                    Bin_cr = "Bin2crF"
                    shape_syst = shape_Bin2[options.era]
                    shape_stat = shape_stat_Bin2[options.era]
                if "Bin3" in options.channel:
                    Bin_cr = "Bin3crF"
                    shape_syst = shape_Bin3[options.era]
                    shape_stat = shape_stat_Bin3[options.era]
                if "Bin4" in options.channel:
                    Bin_cr = "Bin4crF"
                    shape_syst = shape_Bin4[options.era]
                    shape_stat = shape_stat_Bin4[options.era]

                closure_syst = closure_systs[options.era]
                
                # correlated between years, bins
                card.add_nuisance(name, "{:<21}  lnN".format("Closure"), closure_syst)
                
                # correlated between the bins, uncorrelated between years
                card.add_nuisance(name, "{:<21}  lnN".format("Shape_{}".format(options.era)), shape_syst)

                # uncorrelated systematics between the bins
                card.add_ABCD_rate_param("r" + options.era + "_" + options.channel, options.channel + options.era, name, options.era, Bin_cr )
                card.add_nuisance(name, "{:<21}  lnN".format("ShapeStat_{}_{}".format(options.era, options.channel)), shape_stat)
        else:
            rate_nom = p.get("nom").values().sum()
            rate_up = rate_nom + np.sqrt(p.get("nom").variances().sum())*5
            rate_down =  rate_nom - np.sqrt(p.get("nom").variances().sum())*5
            if rate_up == 0: 
                rate_up = 15.065 # 5 sigma, using poisson interval on a count of 0
            if p.name == "expected" and p.ptype == "data" :
                card.add_rate_param("r" + options.era + "_" + options.channel, options.channel + options.era, name, rate=rate_nom, vmin=rate_down, vmax=rate_up )

        if p.ptype=="data": continue #Now that we have expected nom we skip data

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
    card.dump()

if __name__ == "__main__":
    main()
