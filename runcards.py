import yaml
import glob
import os
import multiprocessing
import subprocess
import shlex
import numpy as np


options_input = "config/Vivan_input_{}.yaml"

from multiprocessing.pool import ThreadPool

def call_makeDataCard(cmd):
    """ This runs in a separate thread. """
    print(" ---- [%] :", cmd)
    p = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    return (out, err)


pool = ThreadPool(multiprocessing.cpu_count())
results = []
new_bins = '0 20 50 100 600'
for year in [2016]:
#for year in [2016,2017]:
    with open(options_input.format(year)) as f:
        try:
            inputs = yaml.safe_load(f.read())
        except yaml.YAMLError as exc:
            print ("failed to open the YAML ....")
            print (exc)
    for n, sam in inputs.items():
        if "Graviton" not in n: continue
        print(" ===== processing : ", n, sam, year)
        cmd_sr = "python3 makeDataCard.py --channel catSig "
        cmd_sr += "--variable Zlep_cand_mass "
        cmd_sr += "--stack {signal} DY TOP HIGGS VV QCD data "
        #cmd_sr += "--rebin_piecewise " + new_bins + " "
        #cmd_sr += "--rebin 4 " 
        cmd_sr += "--input=config/Vivan_input_{era}.yaml --era={era}"
        cmd_sr = cmd_sr.format(signal=n, era=year)
        
        cmd_cr1 = "python3 makeDataCard.py --channel catDY "
        cmd_cr1 += "--variable Zlep_cand_mass_DY_control "
        #cmd_cr1 += "--stack {signal} QCD --binrange 1 20 "
        cmd_cr1 += "--stack {signal} DY TOP HIGGS VV QCD data "
        #cmd_cr1 += "--rebin_piecewise " + new_bins 
        cmd_cr1 += "--input=config/Vivan_input_{era}.yaml --era={era}"
        cmd_cr1 = cmd_cr1.format(signal=n, era=year)
        
        cmd_cr2 = "python3 makeDataCard.py --channel catTT "
        cmd_cr2 += "--variable Zlep_cand_mass_TT_control "
        #cmd_cr2 += "--stack {signal} QCD --binrange 1 20 "
        cmd_cr2 += "--stack {signal} DY TOP HIGGS VV QCD data "
        #cmd_cr2 += "--rebin_piecewise " + new_bins 
        cmd_cr2 += "--input=config/Vivan_input_{era}.yaml --era={era}"
        cmd_cr2 = cmd_cr2.format(signal=n, era=year)

        #cmd_cr3 = "python3 makeDataCard.py --channel catCR3 "
        #cmd_cr3 += "--variable nCleaned_Cands "
        #cmd_cr3 += "--stack {signal} QCD --binrange 1 20 "
        ##cmd_cr3 += "--stack {signal} QCD data --binrange 1 20 "#We need data first
        ##cmd_cr3 += "--rebin_piecewise " + new_bins 
        #cmd_cr3 += "--input=config/SUEP_inputs_{era}.yaml --era={era}"
        #cmd_cr3 = cmd_cr3.format(signal=n, era=year)
        
        results.append(pool.apply_async(call_makeDataCard, (cmd_sr,)))
        results.append(pool.apply_async(call_makeDataCard, (cmd_cr1,)))
        results.append(pool.apply_async(call_makeDataCard, (cmd_cr2,)))
        #results.append(pool.apply_async(call_makeDataCard, (cmd_cr3,)))

# Close the pool and wait for each running task to complete
pool.close()
pool.join()
for result in results:
    out, err = result.get()
    #print("out: {}".format(out))
    if "No such file or directory" in str(err):
        print(str(err))
        print(" ----------------- ")
        print()
