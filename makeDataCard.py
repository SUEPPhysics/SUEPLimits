import yaml
import uproot
import os
import argparse
import ftool
import numpy as np
from termcolor import colored


lumis = {
    "2016" : 35.9,
    "2017" : 41.5,
    "2018" : 60.0
}

lumi_unc = {
    "2016" : 1.025,
    "2017" : 1.023,
    "2018" : 1.025
}
def main():
    parser = argparse.ArgumentParser(description='The Creator of Combinators')
    parser.add_argument("-i"  , "--input"   , type=str, default="config/SUEP_inputs_2018.yaml")
    parser.add_argument("-v"  , "--variable", type=str, default="nCleaned_Cands")
    parser.add_argument("-o"  , "--outdir"  , type=str, default="fitroom")
    parser.add_argument("-c"  , "--channel" , nargs='+', type=str)
    parser.add_argument("-s"  , "--signal"  , nargs='+', type=str)
    parser.add_argument("-t"  , "--stack"   , nargs='+', type=str)
    parser.add_argument("-era", "--era"     , type=str, default="2017")
    parser.add_argument("-f"  , "--force"   , action="store_true")
    parser.add_argument("-ns" , "--nostatuncert", action="store_false")
    parser.add_argument("--binrange" ,nargs='+', type=int, default=10)
    parser.add_argument("--rebin" ,type=int, default=1)
    parser.add_argument("--rebin_piecewise",'--list', nargs='*', help='<Required> Set flag', required=False,default=[])
    #parser.add_argument("-xs" , "--xsection", type=str, default="config/xsections_ERA.yaml")
    parser.add_argument("--onexsec", action="store_true")

    options = parser.parse_args()
    
    print("range =", options.binrange)
    # create a working directory where to store the datacards
    try:
        os.mkdir(options.outdir)
        print("Directory " , options.outdir ,  " Created ")
    except:
        if options.force:
            os.rmdir(options.outdir)
            os.mkdir(options.outdir)
            print("Directory " , options.outdir ,  " Re-created ")

    inputs = None
    with open(options.input) as f:
        try:
            inputs = yaml.safe_load(f.read())
        except yaml.YAMLError as exc:
            print (exc)

    xsections = None
    #with open(options.xsection.replace("ERA", options.era)) as f:
    #    print(" -- cross section file : ", options.xsection.replace("ERA", options.era))
    #    try:
    #        xsections = yaml.safe_load(f.read())
    #    except yaml.YAMLError as exc:
    #        print (exc)
    #if options.onexsec:
    #    xsections = { s: {'br': 1.0, 'kr': 1.0, 'xsec': 1.0} for s, xs in xsections.items()}

    if len(options.channel) == 1:
        options.channel = options.channel[0]
    
    xsections = 1.0
    # make datasets per prcess
    datasets = {}
    nsignals = 0
    signal = ""
    for dg in options.stack:
        print(dg)
        p = ftool.datagroup(
            inputs[dg]["files"],
            ptype      = inputs[dg]["type"],
            observable = options.variable,
            name       = dg,
            kfactor    = inputs[dg].get("kfactor", 1.0),
            xsections  = xsections,
            channel    = options.channel,
            rebin      = options.rebin,
            rebin_piecewise = options.rebin_piecewise,
            binrange   = options.binrange,
            luminosity = lumis[options.era]
        )
        #p.save()
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
        channel= card_name
    )
    card.shapes_headers()

    data_obs = datasets.get("data").get("nom")
    card.add_observation(data_obs)

    for n, p in datasets.items():
        name = "Signal" if p.ptype=="signal" else p.name
        if p.ptype=="data":
            continue
        card.add_nominal(name, p.get("nom"))
        card.add_nuisance(name, "{:<21}  lnN".format("CMS_lumi_{}".format(options.era)), lumi_unc[options.era])
       
        #card.add_shape_nuisance(name, "CMS_JES_{}".format(options.era), p.get("jesTotal") , symmetrise=False)
        #card.add_shape_nuisance(name, "CMS_JER_{}".format(options.era), p.get("jer")      , symmetrise=False)
        
        if options.era in ['2016','2017']:
            card.add_shape_nuisance(name, "CMS_pfire_{}".format(options.era), p.get("PrefireWeight"))
           
        card.add_shape_nuisance(name, "CMS_PU_{}".format(options.era), p.get("puWeight"  ), symmetrise=False)
        
        #QCD scale, PDF and other theory uncertainty
        #if "QCD" in name:
        #    card.add_qcd_scales(
        #        name, "CMS_QCDScale{}_{}".format(name, options.era), 
        #        [p.get("QCDScale0w"), p.get("QCDScale1w"), p.get("QCDScale2w")]
        #    )
        
        if options.era == '2016':
            card.add_shape_nuisance(name, "PDF_2016", p.get("PDF"), symmetrise=True)
        else:
            card.add_shape_nuisance(name, "PDF_1718", p.get("PDF"), symmetrise=True)
          
        card.add_nuisance(name, "{:<21}  lnN".format("UEPS"),  1.020) # Underlying events                         
        
        # define rates
        if name  in ["QCD"]:
            card.add_rate_param("QCDnorm_" + options.era, "catSig*", name)

        # adding statistical uncertainties
        card.add_auto_stat()
    card.dump()


if __name__ == "__main__":
    main()
