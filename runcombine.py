import os
import glob
import multiprocessing
from multiprocessing.pool import ThreadPool
import subprocess
import shlex
import argparse

# SLURM script template
slurm_script_template = '''#!/bin/bash
#SBATCH --job-name={sample}
#SBATCH --output={log_dir}{sample}.out
#SBATCH --error={log_dir}{sample}.err
#SBATCH --time=12:00:00
#SBATCH --mem=1GB
#SBATCH --partition=submit

source ~/.bashrc
echo "cd {work_dir}"
cd {work_dir}
echo "cmsenv"
cmsenv
echo "{rm_command}"
{rm_command}
echo "{combine_card_command}"
{combine_card_command}
echo "{text2workspace_command}"
{text2workspace_command}
echo "{combine_command}"
{combine_command}
'''


def call_combine(cmd):
    p = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    return (out, err)


parser = argparse.ArgumentParser()
parser.add_argument(
        "-m", "--method", type=str, default="slurm", choices=['slurm', 'multithread'], help="How to execute the code: either via multithread or slurm."
)
parser.add_argument("-p"  , "--print_commands"   , action='store_true', help='Print the executed combine commands.')
parser.add_argument("-r"  , "--rerun", nargs='+', type=str, help='Rerun a list of datacards.')
parser.add_argument("-i"  , "--input", type=str, required=True, help='Where to find the cards.')
parser.add_argument("-f"  , "--force", action='store_true', help="Force rerunning of limits. By default will not re-run combine if the output .root file exists.")
parser.add_argument("-M"  , "--combineMethod", type=str, default="HybridNew", help="Combine method to use. Supported: HybridNew, AsymptoticLimits")
parser.add_argument("-o"  , "--combineOptions", type=str, default="", help="Additional options to run the combine command with.")
parser.add_argument("-include", "--include", type=str, default='', help="Pass a '-' separated list of strings you want your samples to include. e.g. generic-mPhi300 will only run samples that contain 'generic' and 'mPhi300' in the name.")
options = parser.parse_args()



if options.method == 'multithread':
    pool = ThreadPool(multiprocessing.cpu_count())
    results = []
    print("Running on multithread")
elif options.method == 'slurm':
    work_dir = os.getcwd() + '/' + options.input + '/'
    log_dir = '/work/submit/{}/SUEP/logs/{}/'.format(os.environ['USER'], 'slurm_runcombine')
    if not os.path.isdir(log_dir): os.mkdir(log_dir)
    print("Running on slurm")

# change cwd to the input tag: combine will read the cards from here and will make the higgsCombine file here
os.chdir(options.input)
print("Working in", options.input)

# Read in the datacards
if options.rerun != None:
    dcards = options.rerun
else:
    dcards = glob.glob("cards-*")

# select datacards based on the --include options
if options.include != '':
    dcards = [dc for dc in dcards if all([i in dc for i in options.include.split('-')])]
    
for dc in dcards:

    name= dc.replace("cards-", "")
    if "SUEP" not in name:
        continue

    # don't re run cards, unless running with --force
    if os.path.isfile("higgsCombine{name}.{method}.mH125.root".format(name=name, method=options.combineMethod)) and not options.force:
        print(" -- skipping :", name)
        continue

    print(" -- making :", name)
    
    # Write combine commmands

    # remove the old combined cards
    rm_command = "rm -rf cards-{}/combined.dat".format(name)

    # make the combined.dat cards
    combine_card_command = ("combineCards.py -S "
            "catcrA2016=cards-{name}/shapes-cat_crA2016.dat "
            "catcrB2016=cards-{name}/shapes-cat_crB2016.dat "
            "catcrC2016=cards-{name}/shapes-cat_crC2016.dat "
            "catcrD2016=cards-{name}/shapes-cat_crD2016.dat "
            "catcrE2016=cards-{name}/shapes-cat_crE2016.dat "
            "Bin0crF2016=cards-{name}/shapes-Bin0crF2016.dat "
            "Bin1crF2016=cards-{name}/shapes-Bin1crF2016.dat "
            "Bin2crF2016=cards-{name}/shapes-Bin2crF2016.dat "
            "Bin3crF2016=cards-{name}/shapes-Bin3crF2016.dat "
            "Bin4crF2016=cards-{name}/shapes-Bin4crF2016.dat "
            "catcrG2016=cards-{name}/shapes-cat_crG2016.dat "
            "catcrH2016=cards-{name}/shapes-cat_crH2016.dat "
            "Bin1Sig2016=cards-{name}/shapes-Bin1Sig2016.dat "
            "Bin2Sig2016=cards-{name}/shapes-Bin2Sig2016.dat "
            "Bin3Sig2016=cards-{name}/shapes-Bin3Sig2016.dat "
            "Bin4Sig2016=cards-{name}/shapes-Bin4Sig2016.dat "
            "catcrA2017=cards-{name}/shapes-cat_crA2017.dat "
            "catcrB2017=cards-{name}/shapes-cat_crB2017.dat "
            "catcrC2017=cards-{name}/shapes-cat_crC2017.dat "
            "catcrD2017=cards-{name}/shapes-cat_crD2017.dat "
            "catcrE2017=cards-{name}/shapes-cat_crE2017.dat "
            "Bin0crF2017=cards-{name}/shapes-Bin0crF2017.dat "
            "Bin1crF2017=cards-{name}/shapes-Bin1crF2017.dat "
            "Bin2crF2017=cards-{name}/shapes-Bin2crF2017.dat "
            "Bin3crF2017=cards-{name}/shapes-Bin3crF2017.dat "
            "Bin4crF2017=cards-{name}/shapes-Bin4crF2017.dat "
            "catcrG2017=cards-{name}/shapes-cat_crG2017.dat "
            "catcrH2017=cards-{name}/shapes-cat_crH2017.dat "
            "Bin1Sig2017=cards-{name}/shapes-Bin1Sig2017.dat "
            "Bin2Sig2017=cards-{name}/shapes-Bin2Sig2017.dat "
            "Bin3Sig2017=cards-{name}/shapes-Bin3Sig2017.dat "
            "Bin4Sig2017=cards-{name}/shapes-Bin4Sig2017.dat "
            "catcrA2018=cards-{name}/shapes-cat_crA2018.dat "
            "catcrB2018=cards-{name}/shapes-cat_crB2018.dat "
            "catcrC2018=cards-{name}/shapes-cat_crC2018.dat "
            "catcrD2018=cards-{name}/shapes-cat_crD2018.dat "
            "catcrE2018=cards-{name}/shapes-cat_crE2018.dat "
            "Bin0crF2018=cards-{name}/shapes-Bin0crF2018.dat "
            "Bin1crF2018=cards-{name}/shapes-Bin1crF2018.dat "
            "Bin2crF2018=cards-{name}/shapes-Bin2crF2018.dat "
            "Bin3crF2018=cards-{name}/shapes-Bin3crF2018.dat "
            "Bin4crF2018=cards-{name}/shapes-Bin4crF2018.dat "
            "catcrG2018=cards-{name}/shapes-cat_crG2018.dat "
            "catcrH2018=cards-{name}/shapes-cat_crH2018.dat "
            "Bin1Sig2018=cards-{name}/shapes-Bin1Sig2018.dat "
            "Bin2Sig2018=cards-{name}/shapes-Bin2Sig2018.dat "
            "Bin3Sig2018=cards-{name}/shapes-Bin3Sig2018.dat "
            "Bin4Sig2018=cards-{name}/shapes-Bin4Sig2018.dat "        
            "> cards-{name}/combined.dat").format(name=name)
    
    # converts .dat to .root
    text2workspace_command = "text2workspace.py -m 125 cards-{name}/combined.dat -o cards-{name}/combined.root".format(name=name)
    
    # this is the command running combine. Some options are passed through the parser
    if options.combineMethod == 'HybridNew':
        combine_method = " -M HybridNew --LHCmode LHC-limits "
    elif options.combineMethod == 'AsymptoticLimits':
        combine_method = " -M AsymptoticLimits "
    combine_command = (
        "combine "
        " --datacard cards-{name}/combined.root "
        " {combine_method}"
        " -m 125 --cl 0.95 --name {name}"
        " {options}"
        " --X-rtd MINIMIZER_analytic --X-rtd FAST_VERTICAL_MORPH --rAbsAcc 0.00001 --rRelAcc 0.05".format(
            name=name,
            combine_method=combine_method,
            options=options.combineOptions
        )
    )
    
    # Execute and optionally print the commands   
    if options.print_commands:
        print('--- removing old combined datacard:', rm_command)
        print('--- combining datacards:', combine_card_command)
        print('--- text2workspace:', text2workspace_command)
        print('--- running combine:', combine_command)
    
    if options.method == 'multithread':
        os.system(rm_command)
        os.system(combine_card_command)
        os.system(text2workspace_command)
        results.append(pool.apply_async(call_combine, (combine_command,)))
    elif options.method == 'slurm':
        slurm_script_content = slurm_script_template.format(
                                    rm_command=rm_command,
                                    combine_card_command=combine_card_command,
                                    text2workspace_command=text2workspace_command,
                                    combine_command=combine_command,
                                    work_dir=work_dir,
                                    log_dir=log_dir,
                                    sample=name)

        # Write the SLURM script to a file
        slurm_script_file = f'{log_dir}submit_{name}.sh'
        with open(slurm_script_file, 'w') as f:
            f.write(slurm_script_content)

        # Submit the SLURM job
        subprocess.run(['sbatch', slurm_script_file])
                
if options.method == 'multithread':
    pool.close()
    pool.join()

    for result in results:
        out, err = result.get()
        if "error" in str(err).lower():
            print(str(err))
            print(" ----------------- ")
            print()
