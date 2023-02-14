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
for year in [2016,2017,2018]:
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
        cmd_crA += "--stack {signal} expected data "
        cmd_crA += "--bins 0 500 "
        #cmd_crA += "--rebin 300 " 
        cmd_crA += "--input=config/SUEP_inputs_{era}.yaml --era={era}"
        cmd_crA = cmd_crA.format(signal=n, era=year)

        cmd_crB = "python3 makeDataCard.py --channel cat_crB "
        cmd_crB += "--variable B_SUEP_nconst_Cluster "
        cmd_crB += "--stack {signal} expected data "
        cmd_crB += "--bins 0 500 "
        #cmd_crB += "--rebin 300 " 
        cmd_crB += "--input=config/SUEP_inputs_{era}.yaml --era={era}"
        cmd_crB = cmd_crB.format(signal=n, era=year)

        cmd_crC = "python3 makeDataCard.py --channel cat_crC "
        cmd_crC += "--variable C_SUEP_nconst_Cluster "
        cmd_crC += "--stack {signal} expected data "
        cmd_crC += "--bins 0 500 "
        #cmd_crC += "--rebin 300 " 
        cmd_crC += "--input=config/SUEP_inputs_{era}.yaml --era={era}"
        cmd_crC = cmd_crC.format(signal=n, era=year)

        cmd_crD = "python3 makeDataCard.py --channel cat_crD "
        cmd_crD += "--variable D_SUEP_nconst_Cluster "
        cmd_crD += "--stack {signal} expected data "
        cmd_crD += "--bins 0 500 "
        #cmd_crD += "--rebin 300 " 
        cmd_crD += "--input=config/SUEP_inputs_{era}.yaml --era={era}"
        cmd_crD = cmd_crD.format(signal=n, era=year)

        cmd_crE = "python3 makeDataCard.py --channel cat_crE "
        cmd_crE += "--variable E_SUEP_nconst_Cluster "
        cmd_crE += "--stack {signal} expected data "
        cmd_crE += "--bins 0 500 "
        #cmd_crE += "--rebin 300 " 
        cmd_crE += "--input=config/SUEP_inputs_{era}.yaml --era={era}"
        cmd_crE = cmd_crE.format(signal=n, era=year)

        cmd_crF1 = "python3 makeDataCard.py --channel Bin1crF "
        cmd_crF1 += "--variable F_SUEP_nconst_Cluster "
        cmd_crF1 += "--stack {signal} expected data "
        cmd_crF1 += "--bins 70 100 "
        #cmd_crF1 += "--rebin 25 " 
        cmd_crF1 += "--input=config/SUEP_inputs_{era}.yaml --era={era}"
        cmd_crF1 = cmd_crF1.format(signal=n, era=year)

        cmd_crF2 = "python3 makeDataCard.py --channel Bin2crF "
        cmd_crF2 += "--variable F_SUEP_nconst_Cluster "
        cmd_crF2 += "--stack {signal} expected data "
        cmd_crF2 += "--bins  100 120 "
        #cmd_crF2 += "--rebin 25 " 
        cmd_crF2 += "--input=config/SUEP_inputs_{era}.yaml --era={era}"
        cmd_crF2 = cmd_crF2.format(signal=n, era=year)

        cmd_crF3 = "python3 makeDataCard.py --channel Bin3crF "
        cmd_crF3 += "--variable F_SUEP_nconst_Cluster "
        cmd_crF3 += "--stack {signal} expected data "
        cmd_crF3 += "--bins 120 500 "
        #cmd_crF3 += "--rebin 25 " 
        cmd_crF3 += "--input=config/SUEP_inputs_{era}.yaml --era={era}"
        cmd_crF3 = cmd_crF3.format(signal=n, era=year)

        cmd_crG = "python3 makeDataCard.py --channel cat_crG "
        cmd_crG += "--variable G_SUEP_nconst_Cluster "
        cmd_crG += "--stack {signal} expected data "
        cmd_crG += "--bins 0 500 "
        #cmd_crG += "--rebin 300 " 
        cmd_crG += "--input=config/SUEP_inputs_{era}.yaml --era={era}"
        cmd_crG = cmd_crG.format(signal=n, era=year)

        cmd_crH = "python3 makeDataCard.py --channel cat_crH "
        cmd_crH += "--variable H_SUEP_nconst_Cluster "
        cmd_crH += "--stack {signal} expected data "
        cmd_crH += "--bins 0 500 "
        #cmd_crH += "--rebin 300 " 
        cmd_crH += "--input=config/SUEP_inputs_{era}.yaml --era={era}"
        cmd_crH = cmd_crH.format(signal=n, era=year)

        cmd_sr1 = "python3 makeDataCard.py --channel Bin1Sig "
        cmd_sr1 += "--variable I_SUEP_nconst_Cluster "
        cmd_sr1 += "--stack {signal} expected data "
        cmd_sr1 += "--bins 70 100 "
        #cmd_sr1 += "--rebin 25 " 
        cmd_sr1 += "--input=config/SUEP_inputs_{era}.yaml --era={era}"
        cmd_sr1 = cmd_sr1.format(signal=n, era=year)

        cmd_sr2 = "python3 makeDataCard.py --channel Bin2Sig "
        cmd_sr2 += "--variable I_SUEP_nconst_Cluster "
        cmd_sr2 += "--stack {signal} expected data "
        cmd_sr2 += "--bins 100 120 "
        #cmd_sr2 += "--rebin 25 " 
        cmd_sr2 += "--input=config/SUEP_inputs_{era}.yaml --era={era}"
        cmd_sr2 = cmd_sr2.format(signal=n, era=year)

        cmd_sr3 = "python3 makeDataCard.py --channel Bin3Sig "
        cmd_sr3 += "--variable I_SUEP_nconst_Cluster "
        cmd_sr3 += "--stack {signal} expected data "
        cmd_sr3 += "--bins 120 500 "
        #cmd_sr3 += "--rebin 25 " 
        cmd_sr3 += "--input=config/SUEP_inputs_{era}.yaml --era={era}"
        cmd_sr3 = cmd_sr3.format(signal=n, era=year)

        results.append(pool.apply_async(call_makeDataCard, (cmd_crA,)))
        results.append(pool.apply_async(call_makeDataCard, (cmd_crB,)))
        results.append(pool.apply_async(call_makeDataCard, (cmd_crC,)))
        results.append(pool.apply_async(call_makeDataCard, (cmd_crD,)))
        results.append(pool.apply_async(call_makeDataCard, (cmd_crE,)))
        results.append(pool.apply_async(call_makeDataCard, (cmd_crF1,)))
        results.append(pool.apply_async(call_makeDataCard, (cmd_crF2,)))
        results.append(pool.apply_async(call_makeDataCard, (cmd_crF3,)))
        results.append(pool.apply_async(call_makeDataCard, (cmd_crG,)))
        results.append(pool.apply_async(call_makeDataCard, (cmd_crH,)))        
        results.append(pool.apply_async(call_makeDataCard, (cmd_sr1,)))
        results.append(pool.apply_async(call_makeDataCard, (cmd_sr2,)))
        results.append(pool.apply_async(call_makeDataCard, (cmd_sr3,)))

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
