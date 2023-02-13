import yaml
import glob
import os
import multiprocessing
import subprocess
import shlex
import numpy as np
from multiprocessing.pool import ThreadPool

options_input = "config/SUEP_inputs_{}.yaml"

def call_makeDataCard(cmd):
    """ This runs in a separate thread. """
    print(" ---- [%] :", cmd)
    p = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    return (out, err)


pool = ThreadPool(multiprocessing.cpu_count())
results = []
new_bins = '80 100 150 300'
for year in [2018]:
#for year in [2016,2017]:
    with open(options_input.format(year)) as f:
        try:
            inputs = yaml.safe_load(f.read())
        except yaml.YAMLError as exc:
            print ("failed to open the YAML ....")
            print (exc)
    for n, sam in inputs.items():
        if "SUEP" not in n: continue

        print(" ===== processing : ", n, sam, year)
        cmd_crA = "python3 makeDataCard.py --channel cat_crA "
        cmd_crA += "--variable A_SUEP_nconst_Cluster "
        cmd_crA += "--stack {signal} data "
        #cmd_crA += "--bins " + new_bins + " "
        #cmd_crA += "--rebin 25 " 
        cmd_crA += "--input=config/SUEP_inputs_{era}.yaml --era={era}"
        cmd_crA = cmd_crA.format(signal=n, era=year)

        cmd_crB = "python3 makeDataCard.py --channel cat_crB "
        cmd_crB += "--variable B_SUEP_nconst_Cluster "
        cmd_crB += "--stack {signal} data "
        #cmd_crB += "--bins " + new_bins + " "
        #cmd_crB += "--rebin 25 " 
        cmd_crB += "--input=config/SUEP_inputs_{era}.yaml --era={era}"
        cmd_crB = cmd_crB.format(signal=n, era=year)

        cmd_crC = "python3 makeDataCard.py --channel cat_crC "
        cmd_crC += "--variable C_SUEP_nconst_Cluster "
        cmd_crC += "--stack {signal} data "
        #cmd_crC += "--bins " + new_bins + " "
        #cmd_crC += "--rebin 25 " 
        cmd_crC += "--input=config/SUEP_inputs_{era}.yaml --era={era}"
        cmd_crC = cmd_crC.format(signal=n, era=year)

        cmd_crD = "python3 makeDataCard.py --channel cat_crD "
        cmd_crD += "--variable D_SUEP_nconst_Cluster "
        cmd_crD += "--stack {signal} data "
        #cmd_crD += "--bins " + new_bins + " "
        #cmd_crD += "--rebin 25 " 
        cmd_crD += "--input=config/SUEP_inputs_{era}.yaml --era={era}"
        cmd_crD = cmd_crD.format(signal=n, era=year)

        cmd_crE = "python3 makeDataCard.py --channel cat_crE "
        cmd_crE += "--variable E_SUEP_nconst_Cluster "
        cmd_crE += "--stack {signal} data "
        #cmd_crE += "--bins " + new_bins + " "
        #cmd_crE += "--rebin 25 " 
        cmd_crE += "--input=config/SUEP_inputs_{era}.yaml --era={era}"
        cmd_crE = cmd_crE.format(signal=n, era=year)

        cmd_crF = "python3 makeDataCard.py --channel cat_crF "
        cmd_crF += "--variable F_SUEP_nconst_Cluster "
        cmd_crF += "--stack {signal} data "
        #cmd_crF += "--bins " + new_bins + " "
        #cmd_crF += "--rebin 25 " 
        cmd_crF += "--input=config/SUEP_inputs_{era}.yaml --era={era}"
        cmd_crF = cmd_crF.format(signal=n, era=year)

        cmd_crG = "python3 makeDataCard.py --channel cat_crG "
        cmd_crG += "--variable G_SUEP_nconst_Cluster "
        cmd_crG += "--stack {signal} data "
        #cmd_crG += "--bins " + new_bins + " "
        #cmd_crG += "--rebin 25 " 
        cmd_crG += "--input=config/SUEP_inputs_{era}.yaml --era={era}"
        cmd_crG = cmd_crG.format(signal=n, era=year)

        cmd_crH = "python3 makeDataCard.py --channel cat_crH "
        cmd_crH += "--variable H_SUEP_nconst_Cluster "
        cmd_crH += "--stack {signal} data "
        #cmd_crH += "--bins " + new_bins + " "
        #cmd_crH += "--rebin 25 " 
        cmd_crH += "--input=config/SUEP_inputs_{era}.yaml --era={era}"
        cmd_crH = cmd_crH.format(signal=n, era=year)

        cmd_sr = "python3 makeDataCard.py --channel catSig "
        cmd_sr += "--variable I_SUEP_nconst_Cluster "
        cmd_sr += "--stack {signal} expected data "
        #cmd_sr += "--bins " + new_bins + " "
        #cmd_sr += "--rebin 25 " 
        cmd_sr += "--input=config/SUEP_inputs_{era}.yaml --era={era}"
        cmd_sr = cmd_sr.format(signal=n, era=year)

        results.append(pool.apply_async(call_makeDataCard, (cmd_crA,)))
        results.append(pool.apply_async(call_makeDataCard, (cmd_crB,)))
        results.append(pool.apply_async(call_makeDataCard, (cmd_crC,)))
        results.append(pool.apply_async(call_makeDataCard, (cmd_crD,)))
        results.append(pool.apply_async(call_makeDataCard, (cmd_crE,)))
        results.append(pool.apply_async(call_makeDataCard, (cmd_crF,)))
        results.append(pool.apply_async(call_makeDataCard, (cmd_crG,)))
        results.append(pool.apply_async(call_makeDataCard, (cmd_crH,)))        
        results.append(pool.apply_async(call_makeDataCard, (cmd_sr,)))

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
