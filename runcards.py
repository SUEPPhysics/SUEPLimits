"""
Script to run the makeXYZDataCard.py script in parallel across many bins and samples.
Define in your makeXYZDataCard.py script the bins, commands, and samples to run,
this script will pull from there using:
    makeXYZDataCard.get_bins()        # list of bins to run over per sample
    makeXYZDataCard.get_commands()    # list of commands to run per sample, one per bin
    makeXYZDataCard.get_config_file() # .yaml file of samples

Example usage:
    python runcards.py -m multithread -c 1000 -channel ggf-offline

Authors: Luca Lavezzo, Chad Freer, Pieter van Steenweghen
"""

import argparse
import yaml
import glob
import os
import multiprocessing
import subprocess
import shlex
import numpy as np
from multiprocessing.pool import ThreadPool

import makeOfflineDataCard
import makeScoutingDataCard

def call_makeDataCard(cmd):
    """ This runs in a separate thread. """
    print(" ---- [%] :", cmd)
    p = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    return (out, err)

# SLURM script template
slurm_script_template = '''#!/bin/bash
#SBATCH --job-name={sample}
#SBATCH --output={log_dir}{sample}.out
#SBATCH --error={log_dir}{sample}.err
#SBATCH --time=05:00:00
#SBATCH --mem=1GB
#SBATCH --partition=submit

source ~/.bashrc
cd {work_dir}
conda activate SUEP
#source activate /work/submit/jinw65/limit
{cmd}
'''

def main():
    
    # script parameters
    parser = argparse.ArgumentParser(description="Famous Submitter")
    parser.add_argument(
        "-m", "--method", type=str, default="slurm", choices=['slurm', 'multithread'], help="How to execute the code: either via multithread or slurm."
    )
    parser.add_argument(
        "-f", "--force",action="store_true", help="Recreate cards even if they already exist. By default, it will not re-run existing cards."
    )
    parser.add_argument(
        "-c", "--cores", type=int, default=1000, help="Max number of CPUs to run on, if multithreading."
    )
    parser.add_argument(
        "-t", "--tag", type=str, default='cards', help="Output tag for cards. Creates a subfolder and puts cards there."
    )
    parser.add_argument("-include", "--include", type=str, default='', help="Pass a '-' separated list of strings you want your samples to include. e.g. generic-mPhi300 will only run samples that contain 'generic' and 'mPhi300' in the name.")
    parser.add_argument("-file"  , "--file", type=str, required=False, help='List of samples you want to make datacards for.')
    parser.add_argument("-channel"  , "--channel", type=str, required=True, choices=['ggf-offline', 'ggf-scouting'], help='Which channel to run on.')
    parser.add_argument("-v", "--verbose", action="store_true", help="Print out more information.")
    options = parser.parse_args()

    if options.file:
        with open(options.file) as f:
            samplesToRun = f.read().splitlines()

    if options.method == 'multithread':
        n_cpus = min(multiprocessing.cpu_count(), options.cores)
        pool = ThreadPool(n_cpus)
        print("Running on", n_cpus, "CPUs")
    elif options.method == 'slurm':
        work_dir = os.getcwd()
        log_dir = '/work/submit/{}/SUEP/logs/{}/'.format(os.environ['USER'], 'slurm_runcards')
        if not os.path.isdir(log_dir): os.mkdir(log_dir)
        print("Running on slurm")
        
    if not os.path.isdir(options.tag):
        os.mkdir(options.tag)
        print("Created", options.tag)
    print("Writing out to", options.tag)
    
    results = []
    years = ['2016', '2017', '2018']
    for year in years:

        if options.channel == 'ggf-offline':
            config_file = makeOfflineDataCard.get_config_file()
        elif options.channel == 'ggf-scouting':
            config_file = makeScoutingDataCard.get_config_file()

        with open(config_file.format(year)) as f: 
            try:
                inputs = yaml.safe_load(f.read())
            except yaml.YAMLError as exc:
                print ("failed to open the YAML ....")
                print (exc)

        for n, sam in inputs.items():
            if "SUEP" not in n: continue

            # select samples based on include
            if options.include != '':
                if any([i not in n for i in options.include.split('-')]): continue
            
            # select samples based on file
            if options.file:
                if n not in samplesToRun: continue

            # grab the commands and bins for this sample
            if options.channel == 'ggf-offline':
                commands = makeOfflineDataCard.get_commands(options, n, year)
                bins = makeOfflineDataCard.get_bins()
            elif options.channel == 'ggf-scouting':
                commands = makeScoutingDataCard.get_commands(options, n, year)
                bins = makeScoutingDataCard.get_bins()

            # either force the run, or check whether the file already exist before running
            run = False
            if options.force: run = True
            else:
                for bin_name in bins: 
                    for eof in ['dat','root']:
                        path = '{}/cards-{}/shapes-{}{}.{}'.format(options.tag, n,bin_name,year,eof)
                        if not os.path.exists(path) or os.path.getsize(path) == 0: 
                            run = True
            if not run: 
                print("File exists, skipping (use -f to overwrite):", path)
                continue
            
            print(" ===== processing : ", n, year)
            if options.verbose: print(" ---- inputs : ", sam)

            if options.method == 'multithread':
                for cmd in commands:
                    results.append(pool.apply_async(call_makeDataCard, (cmd,)))
            
            elif options.method == 'slurm':
                slurm_script_content = slurm_script_template.format(
                                            cmd='\n'.join(commands),
                                            work_dir=work_dir,
                                            log_dir=log_dir,
                                            sample=n+'_'+year)
                
                # Write the SLURM script to a file
                slurm_script_file = f'{log_dir}{n}.sh'
                with open(slurm_script_file, 'w') as f:
                    f.write(slurm_script_content)

                # Submit the SLURM job
                subprocess.run(['sbatch', slurm_script_file])
                
    # Close the pool and wait for each running task to complete
    if options.method == 'multithread':
        pool.close()
        pool.join()
        for result in results:
            out, err = result.get()
            if "No such file or directory" in str(err):
                print(str(err))
                print(" ----------------- ")
                print()
            
            
if __name__ == "__main__":
    main()
