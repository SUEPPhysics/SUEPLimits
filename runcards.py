import argparse
import yaml
import glob
import os
import multiprocessing
import subprocess
import shlex
import numpy as np
from multiprocessing.pool import ThreadPool

def call_makeDataCard(cmd):
    """ This runs in a separate thread. """
    print(" ---- [%] :", cmd)
    p = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    return (out, err)

def main():
    
    # script parameters
    parser = argparse.ArgumentParser(description="Famous Submitter")
    parser.add_argument(
        "-f", "--force",action="store_true", help="recreate all cards"
    )
    parser.add_argument(
        "-m", "--max", type=int, default=1000, help="Max number of CPUs to run on"
    )
    parser.add_argument(
        "-t", "--tag", type=str, default='cards', help="Output tag for cards. Creates a subfolder and puts cards there."
    )
    options = parser.parse_args()
    # these are hardcoded in for now
    bins  = ['Bin1Sig','Bin2Sig','Bin3Sig','Bin4Sig',
            'Bin0crF','Bin1crF','Bin2crF','Bin3crF','Bin4crF',
            'cat_crA','cat_crB','cat_crC','cat_crD','cat_crE','cat_crG','cat_crH']
    config_file = "config/create_list/SUEP_inputs_{}.yaml"
    years = [2016, 2017, 2018]
    
    n_cpus = min(multiprocessing.cpu_count(), options.max)
    pool = ThreadPool(n_cpus)
    print("Running on", n_cpus, "CPUs")
    if not os.path.isdir(options.tag):
        os.mkdir(options.tag)
        print("Created", options.tag)
    print("Writing out to", options.tag)
    results = []
    for year in years:
        with open(config_file.format(year)) as f: 
            try:
                inputs = yaml.safe_load(f.read())
            except yaml.YAMLError as exc:
                print ("failed to open the YAML ....")
                print (exc)
        for n, sam in inputs.items():
            if "SUEP" not in n: continue

            # either force the run, or check whether the file already exist before running
            run = False
            if options.force: run = True
            else:
                for bin_name in bins: 
                    for eof in ['dat','root']:
                        path = '{}/cards-{}/shapes-{}{}.{}'.format(options.tag, n,bin_name,year,eof)
                        if not os.path.exists(path): 
                            print('Making datacards:',path)
                            run = True
            if not run: 
                print("File exists, skipping (use -f to overwrite):", path)
                continue
            
            print(" ===== processing : ", n, sam, year)
            cmd_crA = "python3 makeDataCard.py --tag {tag} --channel cat_crA "
            cmd_crA += "--variable A_SUEP_nconst_Cluster70 "
            cmd_crA += "--stack {signal} expected data "
            cmd_crA += "--bins 0 500 "
            #cmd_crA += "--rebin 300 " 
            cmd_crA += "--input=config/SUEP_inputs_{era}.yaml --era={era}"
            cmd_crA = cmd_crA.format(tag=options.tag, signal=n, era=year)

            cmd_crB = "python3 makeDataCard.py --tag {tag} --channel cat_crB "
            cmd_crB += "--variable B_SUEP_nconst_Cluster70 "
            cmd_crB += "--stack {signal} expected data "
            cmd_crB += "--bins 0 500 "
            #cmd_crB += "--rebin 300 " 
            cmd_crB += "--input=config/SUEP_inputs_{era}.yaml --era={era}"
            cmd_crB = cmd_crB.format(tag=options.tag, signal=n, era=year)

            cmd_crC = "python3 makeDataCard.py --tag {tag} --channel cat_crC "
            cmd_crC += "--variable C_SUEP_nconst_Cluster70 "
            cmd_crC += "--stack {signal} expected data "
            cmd_crC += "--bins 0 500 "
            #cmd_crC += "--rebin 300 " 
            cmd_crC += "--input=config/SUEP_inputs_{era}.yaml --era={era}"
            cmd_crC = cmd_crC.format(tag=options.tag, signal=n, era=year)

            cmd_crD = "python3 makeDataCard.py --tag {tag} --channel cat_crD "
            cmd_crD += "--variable D_SUEP_nconst_Cluster70 "
            cmd_crD += "--stack {signal} expected data "
            cmd_crD += "--bins 0 500 "
            #cmd_crD += "--rebin 300 " 
            cmd_crD += "--input=config/SUEP_inputs_{era}.yaml --era={era}"
            cmd_crD = cmd_crD.format(tag=options.tag, signal=n, era=year)

            cmd_crE = "python3 makeDataCard.py --tag {tag} --channel cat_crE "
            cmd_crE += "--variable E_SUEP_nconst_Cluster70 "
            cmd_crE += "--stack {signal} expected data "
            cmd_crE += "--bins 0 500 "
            #cmd_crE += "--rebin 300 " 
            cmd_crE += "--input=config/SUEP_inputs_{era}.yaml --era={era}"
            cmd_crE = cmd_crE.format(tag=options.tag, signal=n, era=year)

            cmd_crF0 = "python3 makeDataCard.py --tag {tag} --channel Bin0crF "
            cmd_crF0 += "--variable F_SUEP_nconst_Cluster70 "
            cmd_crF0 += "--stack {signal} expected data "
            cmd_crF0 += "--bins 70 90 "
            #cmd_crF0 += "--rebin 25 " 
            cmd_crF0 += "--input=config/SUEP_inputs_{era}.yaml --era={era}"
            cmd_crF0 = cmd_crF0.format(tag=options.tag, signal=n, era=year)

            cmd_crF1 = "python3 makeDataCard.py --tag {tag} --channel Bin1crF "
            cmd_crF1 += "--variable F_SUEP_nconst_Cluster70 "
            cmd_crF1 += "--stack {signal} expected data "
            cmd_crF1 += "--bins 90 110 "
            #cmd_crF1 += "--rebin 25 " 
            cmd_crF1 += "--input=config/SUEP_inputs_{era}.yaml --era={era}"
            cmd_crF1 = cmd_crF1.format(tag=options.tag, signal=n, era=year)

            cmd_crF2 = "python3 makeDataCard.py --tag {tag} --channel Bin2crF "
            cmd_crF2 += "--variable F_SUEP_nconst_Cluster70 "
            cmd_crF2 += "--stack {signal} expected data "
            cmd_crF2 += "--bins 110 130 "
            #cmd_crF2 += "--rebin 25 " 
            cmd_crF2 += "--input=config/SUEP_inputs_{era}.yaml --era={era}"
            cmd_crF2 = cmd_crF2.format(tag=options.tag, signal=n, era=year)

            cmd_crF3 = "python3 makeDataCard.py --tag {tag} --channel Bin3crF "
            cmd_crF3 += "--variable F_SUEP_nconst_Cluster70 "
            cmd_crF3 += "--stack {signal} expected data "
            cmd_crF3 += "--bins 130 170 "
            #cmd_crF3 += "--rebin 25 " 
            cmd_crF3 += "--input=config/SUEP_inputs_{era}.yaml --era={era}"
            cmd_crF3 = cmd_crF3.format(tag=options.tag, signal=n, era=year)

            cmd_crF4 = "python3 makeDataCard.py --tag {tag} --channel Bin4crF "
            cmd_crF4 += "--variable F_SUEP_nconst_Cluster70 "
            cmd_crF4 += "--stack {signal} expected data "
            cmd_crF4 += "--bins 170 500 "
            #cmd_crF3 += "--rebin 25 " 
            cmd_crF4 += "--input=config/SUEP_inputs_{era}.yaml --era={era}"
            cmd_crF4 = cmd_crF4.format(tag=options.tag, signal=n, era=year)

            cmd_crG = "python3 makeDataCard.py --tag {tag} --channel cat_crG "
            cmd_crG += "--variable G_SUEP_nconst_Cluster70 "
            cmd_crG += "--stack {signal} expected data "
            cmd_crG += "--bins 0 500 "
            #cmd_crG += "--rebin 300 " 
            cmd_crG += "--input=config/SUEP_inputs_{era}.yaml --era={era}"
            cmd_crG = cmd_crG.format(tag=options.tag, signal=n, era=year)

            cmd_crH = "python3 makeDataCard.py --tag {tag} --channel cat_crH "
            cmd_crH += "--variable H_SUEP_nconst_Cluster70 "
            cmd_crH += "--stack {signal} expected data "
            cmd_crH += "--bins 0 500 "
            #cmd_crH += "--rebin 300 " 
            cmd_crH += "--input=config/SUEP_inputs_{era}.yaml --era={era}"
            cmd_crH = cmd_crH.format(tag=options.tag, signal=n, era=year)

            cmd_sr1 = "python3 makeDataCard.py --tag {tag} --channel Bin1Sig "
            cmd_sr1 += "--variable I_SUEP_nconst_Cluster70 "
            cmd_sr1 += "--stack {signal} expected data "
            cmd_sr1 += "--bins 90 110 "
            #cmd_sr1 += "--rebin 25 " 
            cmd_sr1 += "--input=config/SUEP_inputs_{era}.yaml --era={era}"
            cmd_sr1 = cmd_sr1.format(tag=options.tag, signal=n, era=year)

            cmd_sr2 = "python3 makeDataCard.py --tag {tag} --channel Bin2Sig "
            cmd_sr2 += "--variable I_SUEP_nconst_Cluster70 "
            cmd_sr2 += "--stack {signal} expected data "
            cmd_sr2 += "--bins 110 130 "
            #cmd_sr2 += "--rebin 25 " 
            cmd_sr2 += "--input=config/SUEP_inputs_{era}.yaml --era={era}"
            cmd_sr2 = cmd_sr2.format(tag=options.tag, signal=n, era=year)

            cmd_sr3 = "python3 makeDataCard.py --tag {tag} --channel Bin3Sig "
            cmd_sr3 += "--variable I_SUEP_nconst_Cluster70 "
            cmd_sr3 += "--stack {signal} expected data "
            cmd_sr3 += "--bins 130 170 "
            #cmd_sr3 += "--rebin 25 " 
            cmd_sr3 += "--input=config/SUEP_inputs_{era}.yaml --era={era}"
            cmd_sr3 = cmd_sr3.format(tag=options.tag, signal=n, era=year)

            cmd_sr4 = "python3 makeDataCard.py --tag {tag} --channel Bin4Sig "
            cmd_sr4 += "--variable I_SUEP_nconst_Cluster70 "
            cmd_sr4 += "--stack {signal} expected data "
            cmd_sr4 += "--bins 170 500 "
            #cmd_sr4 += "--rebin 25 " 
            cmd_sr4 += "--input=config/SUEP_inputs_{era}.yaml --era={era}"
            cmd_sr4 = cmd_sr4.format(tag=options.tag, signal=n, era=year)   


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
            
            
if __name__ == "__main__":
    main()
