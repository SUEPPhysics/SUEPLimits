import yaml
import uproot
import os, sys
import argparse
import ftool
import numpy as np
from termcolor import colored

# from: https://twiki.cern.ch/twiki/bin/viewauth/CMS/LumiRecommendationsRun2#Combination_and_correlations
lumis = {
    "2016" : 16.811, #2016apv lumi 19.498 is applied in ftool IFF the filename contains 2016apv
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

def get_commands(options, n, year):

    cmd_crA = "python3 makeDataCard.py --tag {tag} --channel cat_crA "
    cmd_crA += "--variable A_SUEP_nconst_Cluster70 "
    cmd_crA += "--stack {signal} expected data "
    cmd_crA += "--bins 0 2000 "
    cmd_crA += "--input=config/SUEP_inputs_{era}.yaml --era={era}"
    cmd_crA = cmd_crA.format(tag=options.tag, signal=n, era=year)

    cmd_crB = "python3 makeDataCard.py --tag {tag} --channel cat_crB "
    cmd_crB += "--variable B_SUEP_nconst_Cluster70 "
    cmd_crB += "--stack {signal} expected data "
    cmd_crB += "--bins 0 2000 "
    cmd_crB += "--input=config/SUEP_inputs_{era}.yaml --era={era}"
    cmd_crB = cmd_crB.format(tag=options.tag, signal=n, era=year)

    cmd_crC = "python3 makeDataCard.py --tag {tag} --channel cat_crC "
    cmd_crC += "--variable C_SUEP_nconst_Cluster70 "
    cmd_crC += "--stack {signal} expected data "
    cmd_crC += "--bins 0 2000 "
    cmd_crC += "--input=config/SUEP_inputs_{era}.yaml --era={era}"
    cmd_crC = cmd_crC.format(tag=options.tag, signal=n, era=year)

    cmd_crD = "python3 makeDataCard.py --tag {tag} --channel cat_crD "
    cmd_crD += "--variable D_SUEP_nconst_Cluster70 "
    cmd_crD += "--stack {signal} expected data "
    cmd_crD += "--bins 0 2000 "
    cmd_crD += "--input=config/SUEP_inputs_{era}.yaml --era={era}"
    cmd_crD = cmd_crD.format(tag=options.tag, signal=n, era=year)

    cmd_crE = "python3 makeDataCard.py --tag {tag} --channel cat_crE "
    cmd_crE += "--variable E_SUEP_nconst_Cluster70 "
    cmd_crE += "--stack {signal} expected data "
    cmd_crE += "--bins 0 2000 "
    cmd_crE += "--input=config/SUEP_inputs_{era}.yaml --era={era}"
    cmd_crE = cmd_crE.format(tag=options.tag, signal=n, era=year)

    cmd_crF0 = "python3 makeDataCard.py --tag {tag} --channel Bin0crF "
    cmd_crF0 += "--variable F_SUEP_nconst_Cluster70 "
    cmd_crF0 += "--stack {signal} expected data "
    cmd_crF0 += "--bins 70 90 "
    cmd_crF0 += "--input=config/SUEP_inputs_{era}.yaml --era={era}"
    cmd_crF0 = cmd_crF0.format(tag=options.tag, signal=n, era=year)

    cmd_crF1 = "python3 makeDataCard.py --tag {tag} --channel Bin1crF "
    cmd_crF1 += "--variable F_SUEP_nconst_Cluster70 "
    cmd_crF1 += "--stack {signal} expected data "
    cmd_crF1 += "--bins 90 110 "
    cmd_crF1 += "--input=config/SUEP_inputs_{era}.yaml --era={era}"
    cmd_crF1 = cmd_crF1.format(tag=options.tag, signal=n, era=year)

    cmd_crF2 = "python3 makeDataCard.py --tag {tag} --channel Bin2crF "
    cmd_crF2 += "--variable F_SUEP_nconst_Cluster70 "
    cmd_crF2 += "--stack {signal} expected data "
    cmd_crF2 += "--bins 110 130 "
    cmd_crF2 += "--input=config/SUEP_inputs_{era}.yaml --era={era}"
    cmd_crF2 = cmd_crF2.format(tag=options.tag, signal=n, era=year)

    cmd_crF3 = "python3 makeDataCard.py --tag {tag} --channel Bin3crF "
    cmd_crF3 += "--variable F_SUEP_nconst_Cluster70 "
    cmd_crF3 += "--stack {signal} expected data "
    cmd_crF3 += "--bins 130 170 "
    cmd_crF3 += "--input=config/SUEP_inputs_{era}.yaml --era={era}"
    cmd_crF3 = cmd_crF3.format(tag=options.tag, signal=n, era=year)

    cmd_crF4 = "python3 makeDataCard.py --tag {tag} --channel Bin4crF "
    cmd_crF4 += "--variable F_SUEP_nconst_Cluster70 "
    cmd_crF4 += "--stack {signal} expected data "
    cmd_crF4 += "--bins 170 2000 "
    cmd_crF4 += "--input=config/SUEP_inputs_{era}.yaml --era={era}"
    cmd_crF4 = cmd_crF4.format(tag=options.tag, signal=n, era=year)

    cmd_crG = "python3 makeDataCard.py --tag {tag} --channel cat_crG "
    cmd_crG += "--variable G_SUEP_nconst_Cluster70 "
    cmd_crG += "--stack {signal} expected data "
    cmd_crG += "--bins 0 2000 "
    cmd_crG += "--input=config/SUEP_inputs_{era}.yaml --era={era}"
    cmd_crG = cmd_crG.format(tag=options.tag, signal=n, era=year)

    cmd_crH = "python3 makeDataCard.py --tag {tag} --channel cat_crH "
    cmd_crH += "--variable H_SUEP_nconst_Cluster70 "
    cmd_crH += "--stack {signal} expected data "
    cmd_crH += "--bins 0 2000 "
    cmd_crH += "--input=config/SUEP_inputs_{era}.yaml --era={era}"
    cmd_crH = cmd_crH.format(tag=options.tag, signal=n, era=year)

    cmd_sr1 = "python3 makeDataCard.py --tag {tag} --channel Bin1Sig "
    cmd_sr1 += "--variable I_SUEP_nconst_Cluster70 "
    cmd_sr1 += "--stack {signal} expected data "
    cmd_sr1 += "--bins 90 110 "
    cmd_sr1 += "--input=config/SUEP_inputs_{era}.yaml --era={era}"
    cmd_sr1 = cmd_sr1.format(tag=options.tag, signal=n, era=year)

    cmd_sr2 = "python3 makeDataCard.py --tag {tag} --channel Bin2Sig "
    cmd_sr2 += "--variable I_SUEP_nconst_Cluster70 "
    cmd_sr2 += "--stack {signal} expected data "
    cmd_sr2 += "--bins 110 130 "
    cmd_sr2 += "--input=config/SUEP_inputs_{era}.yaml --era={era}"
    cmd_sr2 = cmd_sr2.format(tag=options.tag, signal=n, era=year)

    cmd_sr3 = "python3 makeDataCard.py --tag {tag} --channel Bin3Sig "
    cmd_sr3 += "--variable I_SUEP_nconst_Cluster70 "
    cmd_sr3 += "--stack {signal} expected data "
    cmd_sr3 += "--bins 130 170 "
    cmd_sr3 += "--input=config/SUEP_inputs_{era}.yaml --era={era}"
    cmd_sr3 = cmd_sr3.format(tag=options.tag, signal=n, era=year)

    cmd_sr4 = "python3 makeDataCard.py --tag {tag} --channel Bin4Sig "
    cmd_sr4 += "--variable I_SUEP_nconst_Cluster70 "
    cmd_sr4 += "--stack {signal} expected data "
    cmd_sr4 += "--bins 170 2000 "
    cmd_sr4 += "--input=config/SUEP_inputs_{era}.yaml --era={era}"
    cmd_sr4 = cmd_sr4.format(tag=options.tag, signal=n, era=year) 

    commands = [cmd_crA, cmd_crB, cmd_crC, cmd_crD, cmd_crE, cmd_crF0, cmd_crF1, cmd_crF2, cmd_crF3, cmd_crF4, cmd_crG, cmd_crH, cmd_sr1, cmd_sr2, cmd_sr3, cmd_sr4]

    return commands

def get_bins():
    bins  = ['Bin1Sig','Bin2Sig',
            'Bin3Sig','Bin4Sig',
            'Bin0crF','Bin1crF','Bin2crF',
            'Bin3crF','Bin4crF',
            'cat_crA','cat_crB','cat_crC','cat_crD','cat_crE','cat_crG','cat_crH']
    return bins

def get_config_file():
    return "config/SUEP_inputs_{}.yaml"

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
    card.dump()

if __name__ == "__main__":
    main()
