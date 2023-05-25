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

bins =['Bin1Sig','Bin2Sig','Bin3Sig','Bin4Sig','Bin0crF','Bin1crF','Bin2crF','Bin3crF','Bin4crF','cat_crA','cat_crB','cat_crC','cat_crD','cat_crE','cat_crG','cat_crH']

pool = ThreadPool(multiprocessing.cpu_count())
results = []

for year in [2016,2017,2018]: # Combining all years!
    with open(options_input.format(year)) as f: 
        try:
            inputs = yaml.safe_load(f.read())
        except yaml.YAMLError as exc:
            print ("failed to open the YAML ....")
            print (exc)
    for n, sam in inputs.items():
        try: #To check and resubmit missing datacards
            if "SUEP" not in n: continue
        
            for bin_name in bins: 
                for eof in ['dat','root']:
                    path = 'cards-{}/shapes-{}{}.{}'.format(n,bin_name,year,eof)
                    if not os.path.exists(path): 
                        print('Missing datacards:',path)
                        raise Exception('Missing datacards:', path)

        except:

            print(" ===== processing : ", n, sam, year)
            cmd_crA = "python3 makeDataCard.py --channel cat_crA "
            cmd_crA += "--variable A_SUEP_nconst_Cluster70 "
            cmd_crA += "--stack {signal} expected data "
            cmd_crA += "--bins 0 500 "
            #cmd_crA += "--rebin 300 " 
            cmd_crA += "--input=config/SUEP_inputs_{era}.yaml --era={era}"
            cmd_crA = cmd_crA.format(signal=n, era=year)

            cmd_crB = "python3 makeDataCard.py --channel cat_crB "
            cmd_crB += "--variable B_SUEP_nconst_Cluster70 "
            cmd_crB += "--stack {signal} expected data "
            cmd_crB += "--bins 0 500 "
            #cmd_crB += "--rebin 300 " 
            cmd_crB += "--input=config/SUEP_inputs_{era}.yaml --era={era}"
            cmd_crB = cmd_crB.format(signal=n, era=year)

            cmd_crC = "python3 makeDataCard.py --channel cat_crC "
            cmd_crC += "--variable C_SUEP_nconst_Cluster70 "
            cmd_crC += "--stack {signal} expected data "
            cmd_crC += "--bins 0 500 "
            #cmd_crC += "--rebin 300 " 
            cmd_crC += "--input=config/SUEP_inputs_{era}.yaml --era={era}"
            cmd_crC = cmd_crC.format(signal=n, era=year)

            cmd_crD = "python3 makeDataCard.py --channel cat_crD "
            cmd_crD += "--variable D_SUEP_nconst_Cluster70 "
            cmd_crD += "--stack {signal} expected data "
            cmd_crD += "--bins 0 500 "
            #cmd_crD += "--rebin 300 " 
            cmd_crD += "--input=config/SUEP_inputs_{era}.yaml --era={era}"
            cmd_crD = cmd_crD.format(signal=n, era=year)

            cmd_crE = "python3 makeDataCard.py --channel cat_crE "
            cmd_crE += "--variable E_SUEP_nconst_Cluster70 "
            cmd_crE += "--stack {signal} expected data "
            cmd_crE += "--bins 0 500 "
            #cmd_crE += "--rebin 300 " 
            cmd_crE += "--input=config/SUEP_inputs_{era}.yaml --era={era}"
            cmd_crE = cmd_crE.format(signal=n, era=year)

            cmd_crF0 = "python3 makeDataCard.py --channel Bin0crF "
            cmd_crF0 += "--variable F_SUEP_nconst_Cluster70 "
            cmd_crF0 += "--stack {signal} expected data "
            cmd_crF0 += "--bins 70 90 "
            #cmd_crF0 += "--rebin 25 " 
            cmd_crF0 += "--input=config/SUEP_inputs_{era}.yaml --era={era}"
            cmd_crF0 = cmd_crF0.format(signal=n, era=year)

            cmd_crF1 = "python3 makeDataCard.py --channel Bin1crF "
            cmd_crF1 += "--variable F_SUEP_nconst_Cluster70 "
            cmd_crF1 += "--stack {signal} expected data "
            cmd_crF1 += "--bins 90 110 "
            #cmd_crF1 += "--rebin 25 " 
            cmd_crF1 += "--input=config/SUEP_inputs_{era}.yaml --era={era}"
            cmd_crF1 = cmd_crF1.format(signal=n, era=year)

            cmd_crF2 = "python3 makeDataCard.py --channel Bin2crF "
            cmd_crF2 += "--variable F_SUEP_nconst_Cluster70 "
            cmd_crF2 += "--stack {signal} expected data "
            cmd_crF2 += "--bins 110 130 "
            #cmd_crF2 += "--rebin 25 " 
            cmd_crF2 += "--input=config/SUEP_inputs_{era}.yaml --era={era}"
            cmd_crF2 = cmd_crF2.format(signal=n, era=year)

            cmd_crF3 = "python3 makeDataCard.py --channel Bin3crF "
            cmd_crF3 += "--variable F_SUEP_nconst_Cluster70 "
            cmd_crF3 += "--stack {signal} expected data "
            cmd_crF3 += "--bins 130 170 "
            #cmd_crF3 += "--rebin 25 " 
            cmd_crF3 += "--input=config/SUEP_inputs_{era}.yaml --era={era}"
            cmd_crF3 = cmd_crF3.format(signal=n, era=year)

            cmd_crF4 = "python3 makeDataCard.py --channel Bin4crF "
            cmd_crF4 += "--variable F_SUEP_nconst_Cluster70 "
            cmd_crF4 += "--stack {signal} expected data "
            cmd_crF4 += "--bins 170 500 "
            #cmd_crF3 += "--rebin 25 " 
            cmd_crF4 += "--input=config/SUEP_inputs_{era}.yaml --era={era}"
            cmd_crF4 = cmd_crF4.format(signal=n, era=year)

            cmd_crG = "python3 makeDataCard.py --channel cat_crG "
            cmd_crG += "--variable G_SUEP_nconst_Cluster70 "
            cmd_crG += "--stack {signal} expected data "
            cmd_crG += "--bins 0 500 "
            #cmd_crG += "--rebin 300 " 
            cmd_crG += "--input=config/SUEP_inputs_{era}.yaml --era={era}"
            cmd_crG = cmd_crG.format(signal=n, era=year)

            cmd_crH = "python3 makeDataCard.py --channel cat_crH "
            cmd_crH += "--variable H_SUEP_nconst_Cluster70 "
            cmd_crH += "--stack {signal} expected data "
            cmd_crH += "--bins 0 500 "
            #cmd_crH += "--rebin 300 " 
            cmd_crH += "--input=config/SUEP_inputs_{era}.yaml --era={era}"
            cmd_crH = cmd_crH.format(signal=n, era=year)

            cmd_sr1 = "python3 makeDataCard.py --channel Bin1Sig "
            cmd_sr1 += "--variable I_SUEP_nconst_Cluster70 "
            cmd_sr1 += "--stack {signal} expected data "
            cmd_sr1 += "--bins 90 110 "
            #cmd_sr1 += "--rebin 25 " 
            cmd_sr1 += "--input=config/SUEP_inputs_{era}.yaml --era={era}"
            cmd_sr1 = cmd_sr1.format(signal=n, era=year)

            cmd_sr2 = "python3 makeDataCard.py --channel Bin2Sig "
            cmd_sr2 += "--variable I_SUEP_nconst_Cluster70 "
            cmd_sr2 += "--stack {signal} expected data "
            cmd_sr2 += "--bins 110 130 "
            #cmd_sr2 += "--rebin 25 " 
            cmd_sr2 += "--input=config/SUEP_inputs_{era}.yaml --era={era}"
            cmd_sr2 = cmd_sr2.format(signal=n, era=year)

            cmd_sr3 = "python3 makeDataCard.py --channel Bin3Sig "
            cmd_sr3 += "--variable I_SUEP_nconst_Cluster70 "
            cmd_sr3 += "--stack {signal} expected data "
            cmd_sr3 += "--bins 130 170 "
            #cmd_sr3 += "--rebin 25 " 
            cmd_sr3 += "--input=config/SUEP_inputs_{era}.yaml --era={era}"
            cmd_sr3 = cmd_sr3.format(signal=n, era=year)

            cmd_sr4 = "python3 makeDataCard.py --channel Bin4Sig "
            cmd_sr4 += "--variable I_SUEP_nconst_Cluster70 "
            cmd_sr4 += "--stack {signal} expected data "
            cmd_sr4 += "--bins 170 500 "
            #cmd_sr4 += "--rebin 25 " 
            cmd_sr4 += "--input=config/SUEP_inputs_{era}.yaml --era={era}"
            cmd_sr4 = cmd_sr4.format(signal=n, era=year)   


            results.append(pool.apply_async(call_makeDataCard, (cmd_crA,)))
            results.append(pool.apply_async(call_makeDataCard, (cmd_crB,)))
            results.append(pool.apply_async(call_makeDataCard, (cmd_crC,)))
            results.append(pool.apply_async(call_makeDataCard, (cmd_crD,)))
            results.append(pool.apply_async(call_makeDataCard, (cmd_crE,)))
            results.append(pool.apply_async(call_makeDataCard, (cmd_crF0,))) #sr0 is omitted because this was used as validation region 
            results.append(pool.apply_async(call_makeDataCard, (cmd_crF1,)))
            results.append(pool.apply_async(call_makeDataCard, (cmd_crF2,)))
            results.append(pool.apply_async(call_makeDataCard, (cmd_crF3,)))
            results.append(pool.apply_async(call_makeDataCard, (cmd_crF4,)))
            results.append(pool.apply_async(call_makeDataCard, (cmd_crG,)))
            results.append(pool.apply_async(call_makeDataCard, (cmd_crH,)))        
            results.append(pool.apply_async(call_makeDataCard, (cmd_sr1,)))
            results.append(pool.apply_async(call_makeDataCard, (cmd_sr2,)))
            results.append(pool.apply_async(call_makeDataCard, (cmd_sr3,)))
            results.append(pool.apply_async(call_makeDataCard, (cmd_sr4,)))

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
