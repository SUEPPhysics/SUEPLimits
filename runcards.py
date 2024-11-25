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
import os
import multiprocessing
import subprocess
import shlex
from multiprocessing.pool import ThreadPool

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
conda activate suep
{cmd}
'''

def main():
    
    # script parameters
    parser = argparse.ArgumentParser(description="Famous Submitter")
    parser.add_argument(
        "-a", "--analysis", type=str, required=True, help="YAML file with analysis configuration."
    )
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
    parser.add_argument("-includeAll", "--includeAll", type=str, default='', help="Pass a '-' separated list of strings you want all your samples to include. e.g. generic-mPhi300 will only run samples that contain 'generic' AND 'mPhi300' in the name.")
    parser.add_argument("-includeAny", "--includeAny", type=str, default='', help="Pass a '-' separated list of strings you want any of your samples to include. e.g. generic-mPhi300 will only run samples that contain 'generic' OR 'mPhi300' in the name.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Print out more information.")
    options = parser.parse_args()

    with open(options.analysis) as f:
        analysis = yaml.safe_load(f.read())
        analysis = analysis['runcards']

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
        os.makedirs(options.tag)
        print("Created", options.tag)
    print("Writing out to", options.tag)
    
    results = []
    for sample in analysis['samples']:

        # select samples based on include
        if options.includeAll != '' and options.includeAny != '':
            raise Exception("Either run with --includeAll or --includeAny or neither, not both")
        elif options.includeAny != '':
            if all([i not in sample for i in options.includeAny.split('-')]): continue
        elif options.includeAll != '':
            if any([i not in sample for i in options.includeAll.split('-')]): continue
        
        # grab the commands and bins for this sample
        commands = analysis['commands']
        commands = [com.format(n=sample, tag=options.tag) for com in commands]

        # either force the run, or check whether the file already exist before running
        bins_to_run = [com.split('--channel ')[1].split()[0] for com in commands]
        eras_to_run = [com.split('--era ')[1].split()[0] for com in commands]
        if not options.force:
            completed = []
            for bin_name, era in zip(bins_to_run, eras_to_run): 
                for eof in ['dat','root']:
                    path = '{}/cards-{}/shapes-{}{}.{}'.format(options.tag, sample, bin_name, era, eof)
                    if os.path.exists(path) and os.path.getsize(path) > 0: 
                        completed.append(bin_name)
            bins_to_run = list(set(bins_to_run) - set(completed))
            if len(bins_to_run) == 0: 
                print("Cards for this sample are completed, skipping (use -f to overwrite):", sample, era)
                continue
    
        # only run the commands for the bins that are not already completed
        commands = [com for com in commands if com.split('--channel ')[1].split()[0] in bins_to_run]

        print(" ===== processing : ", sample, bins_to_run)

        if options.method == 'multithread':
            for cmd in commands:
                results.append(pool.apply_async(call_makeDataCard, (cmd,)))
        
        elif options.method == 'slurm':
            slurm_script_content = slurm_script_template.format(
                                        cmd='\n'.join(commands),
                                        work_dir=work_dir,
                                        log_dir=log_dir,
                                        sample=sample+'_'+era)
            
            # Write the SLURM script to a file
            slurm_script_file = f'{log_dir}{sample}.sh'
            with open(slurm_script_file, 'w') as f:
                f.write(slurm_script_content)

            # Submit the SLURM job
            subprocess.run(['sbatch', slurm_script_file])
                
    # Close the pool and wait for each running task to complete
    if options.method == 'multithread':
        pool.close()
        pool.join()
        print()
        print(" ----------------- ")
        for result in results:
            out, err = result.get()
            print(err.decode('utf-8'))
            print(" ----------------- ")
            print()
            
            
if __name__ == "__main__":
    main()
