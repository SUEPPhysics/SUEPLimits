import os
import glob
import multiprocessing
from multiprocessing.pool import ThreadPool
import subprocess
import shlex
import argparse
import yaml
from tqdm import tqdm

# HTCondor script template
condor_script_template = '''

echo "Landed on $(hostname) in $(pwd)"

echo "Setting up environment"
export VO_CMS_SW_DIR=/cvmfs/cms.cern.ch
source $VO_CMS_SW_DIR/cmsset_default.sh

cmssw-el9 --command-to-run << 'EOF'

echo "Inside Singularity image"
cmsrel CMSSW_14_1_0_pre4
cd CMSSW_14_1_0_pre4/src
cmsenv

echo "Fetching HiggsAnalysis combine"
git clone https://github.com/cms-analysis/HiggsAnalysis-CombinedLimit.git HiggsAnalysis/CombinedLimit
cd $CMSSW_BASE/src/HiggsAnalysis/CombinedLimit
git fetch origin
git checkout v10.0.2

echo "Fetching CombineHarvester"
cd $CMSSW_BASE/src
git clone https://github.com/cms-analysis/CombineHarvester.git CombineHarvester

echo "scramv1"
cd $CMSSW_BASE/src/
scramv1 b clean; scramv1 b -j 10

echo "pwd"
pwd

echo "tar -xvf ../../cards.tar.gz -C ."
tar -xvf ../../cards.tar.gz -C .

echo "ls"
ls

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

xrdcp *.root {redirector}/{condor_out_dir}
'''

# HTCondor submission script
condor_submission_script = '''
universe              = vanilla
request_disk          = 5GB
request_memory        = {mem}
request_cpus          = {cpus}
executable            = {jobdir}/{script}.sh
arguments             = $(ProcId) $(jobid) $(fileid)
should_transfer_files = YES
transfer_input_files  = {transfer_file}
MAX_TRANSFER_INPUT_MB = 500
output                = $(ClusterId).$(ProcId).{outFile}.out
error                 = $(ClusterId).$(ProcId).{outFile}.err
log                   = $(ClusterId).$(ProcId).{outFile}.log
initialdir            = {jobdir}
when_to_transfer_output = ON_EXIT
on_exit_remove        = (ExitBySignal == False) && (ExitCode == 0)
max_retries           = 3
use_x509userproxy     = True
x509userproxy         = /home/submit/{user}/{proxy}
+AccountingGroup      = "analysis.{user}"
Requirements          = ( BOSCOCluster =!= "t3serv008.mit.edu" && BOSCOCluster =!= "ce03.cmsaf.mit.edu" && BOSCOCluster =!= "eofe8.mit.edu")
+DESIRED_Sites        = "T2_AT_Vienna,T2_BE_IIHE,T2_BE_UCL,T2_BR_SPRACE,T2_BR_UERJ,T2_CH_CERN,T2_CH_CERN_AI,T2_CH_CERN_HLT,T2_CH_CERN_Wigner,T2_CH_CSCS,T2_CH_CSCS_HPC,T2_CN_Beijing,T2_DE_DESY,T2_DE_RWTH,T2_EE_Estonia,T2_ES_CIEMAT,T2_ES_IFCA,T2_FI_HIP,T2_FR_CCIN2P3,T2_FR_GRIF_IRFU,T2_FR_GRIF_LLR,T2_FR_IPHC,T2_GR_Ioannina,T2_HU_Budapest,T2_IN_TIFR,T2_IT_Bari,T2_IT_Legnaro,T2_IT_Pisa,T2_IT_Rome,T2_KR_KISTI,T2_MY_SIFIR,T2_MY_UPM_BIRUNI,T2_PK_NCP,T2_PL_Swierk,T2_PL_Warsaw,T2_PT_NCG_Lisbon,T2_RU_IHEP,T2_RU_INR,T2_RU_ITEP,T2_RU_JINR,T2_RU_PNPI,T2_RU_SINP,T2_TH_CUNSTDA,T2_TR_METU,T2_TW_NCHC,T2_UA_KIPT,T2_UK_London_IC,T2_UK_SGrid_Bristol,T2_UK_SGrid_RALPP,T2_US_Caltech,T2_US_Florida,T2_US_Nebraska,T2_US_Purdue,T2_US_UCSD,T2_US_Vanderbilt,T2_US_Wisconsin,T3_CH_CERN_CAF,T3_CH_CERN_DOMA,T3_CH_CERN_HelixNebula,T3_CH_CERN_HelixNebula_REHA,T3_CH_CMSAtHome,T3_CH_Volunteer,T3_US_HEPCloud,T3_US_NERSC,T3_US_OSG,T3_US_PSC,T3_US_SDSC,T3_US_MIT"
+JobFlavour           = "{queue}"
queue 1
'''

# SLURM script template
slurm_script_template = '''#!/bin/bash
#SBATCH --job-name={outFile}
#SBATCH --output={log_dir}{outFile}.out
#SBATCH --error={log_dir}{outFile}.err
#SBATCH --time={time_limit}
#SBATCH --mem={mem}
#SBATCH --partition=submit
#SBATCH --tasks-per-node {cpus}
#SBATCH --oversubscribe

echo "Landed on $(hostname)"

echo "Setting up environment"
export VO_CMS_SW_DIR=/cvmfs/cms.cern.ch
source $VO_CMS_SW_DIR/cmsset_default.sh

cmssw-el9 --bind /ceph,/work,/cvmfs --command-to-run << 'EOF'

# This will all be executed inside the singularity
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

local_script_tempate = """#!/bin/bash

echo "Setting up environment"
export VO_CMS_SW_DIR=/cvmfs/cms.cern.ch
source $VO_CMS_SW_DIR/cmsset_default.sh

cmssw-el9 --bind /ceph,/work,/cvmfs --command-to-run << 'EOF'

# This will all be executed inside the singularity
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

"""

def call_combine(cmd):
    print(" ---- [%] :", cmd)
    p = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    return (out, err)


parser = argparse.ArgumentParser()
parser.add_argument("-a", "--analysis", type=str, required=True, help="YAML file with analysis configuration.")
parser.add_argument(
        "-m", "--method", type=str, default="iterative", choices=['iterative', 'slurm', 'multithread', 'condor'], help="How to execute the code."
)
parser.add_argument("-p"  , "--print_commands"   , action='store_true', help='Print the executed combine commands.')
parser.add_argument("-file"  , "--file", type=str, help='Rerun a list of samples stored in a file.')
parser.add_argument("-i"  , "--input", type=str, required=True, help='Where to find the cards.')
parser.add_argument("-f"  , "--force", action='store_true', help="Force rerunning of limits. By default will not re-run combine if the output .root file exists. Existing limits are moved to a file higgsCombine<sample_name>.overwritten.root ")
parser.add_argument("-M"  , "--combineMethod", type=str, default="HybridNew", choices=['HybridNew', 'HybridNewAuto', 'AsymptoticLimits'], help="Combine method to use.")
parser.add_argument("-o"  , "--combineOptions", type=str, default="", help="Additional options to run the combine command with, e.g. -o ' --fork 20 ' runs the combine command like ' combine ... --fork 20 '.")
parser.add_argument("-d"  , "--dry", action='store_true', help="Dry run, does not exectute any combine command.")
parser.add_argument("-includeAll", "--includeAll", type=str, default='', help="Pass a '-' separated list of strings you want all your samples to include. e.g. generic-mPhi300 will only run samples that contain 'generic' AND 'mPhi300' in the name.")
parser.add_argument("-includeAny", "--includeAny", type=str, default='', help="Pass a '-' separated list of strings you want any of your samples to include. e.g. generic-mPhi300 will only run samples that contain 'generic' OR 'mPhi300' in the name.")
parser.add_argument("-q", "--quantiles", action='store_true', default=False, help="When running '-M HybridNew' or '-M HybridNewAuto', use this option to run the following quantiles (0.025, 0.16, 0.5, 0.84, 0.975) as well as the observed limit, automatically. Equivalent to running this script with '-o '--expectedFromGrid <QUANTILE>'' for all quantiles.") 
parser.add_argument("--cores", type=int, help="Maximum number of cores to run multithread on.", default=10, required=False)
options = parser.parse_args()

# read the analysis.yaml file
with open(options.analysis) as f:
    analysis = yaml.safe_load(f.read())['runcombine']

# change cwd to the input tag: combine will read the cards from here and will make the higgsCombine file here
os.chdir(options.input)
work_dir = os.getcwd()
print("Working in", options.input)
print("Running with", options.method, "method")

# define method-specific variables
if options.method == 'multithread':
    pool = ThreadPool(min(multiprocessing.cpu_count(), options.cores))
    results = []

elif options.method == 'iterative':
    pass

elif options.method == 'slurm':

    # declare and create log dir
    sub_dir =  os.path.basename(options.input.rstrip(os.sep))
    log_dir = '/work/submit/{}/SUEP/logs/{}_{}/'.format(os.environ['USER'], 'slurm_runcombine', sub_dir)
    if not os.path.isdir(log_dir): os.mkdir(log_dir)

elif options.method == 'condor':

    # declare and create log dir
    sub_dir =  os.path.basename(options.input.rstrip(os.sep))
    log_dir = '/work/submit/{}/SUEP/logs/{}_{}/'.format(os.environ['USER'], 'condor_runcombine', sub_dir)
    if not os.path.isdir(log_dir): os.mkdir(log_dir)

    # declare and create condor output dir
    redirector = "root://submit50.mit.edu/"
    condor_out_dir = "/data/group/cms/store/user/{}/SUEP/{}_{}".format(os.environ['USER'], 'condor_runcombine', sub_dir)
    check_dir_command = f"xrdfs {redirector} stat {condor_out_dir}"
    _sample_dir_exists = subprocess.call(check_dir_command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0
    if not _sample_dir_exists:
        exit_code = os.system(f"xrdfs {redirector} mkdir -p {condor_out_dir}")
        if exit_code != 0:
            raise Exception("Failed to create the output directory.")
    else:
        print(f"Output directory {redirector+condor_out_dir} already exists! Will not delete it, but data there might be ovewritten.")

    # tar up the cards for transferring
    if not os.path.isfile('cards.tar.gz'):
        exit_code = os.system("find . -type d -name 'cards*' -exec tar -czvf cards.tar.gz {} +")
        if exit_code != 0:
            raise Exception("Failed to tar up the cards directory.")
    transfer_file = os.path.join(os.getcwd(), 'cards.tar.gz')
    
# Read in the datacards
if options.file != None:
    with open(options.file) as f:
        samples = f.read().splitlines()
    dcards = ["cards-{}".format(s) for s in samples]
else:
    dcards = glob.glob("cards-*")

# select datacards based on the --include options
if options.includeAll != '' and options.includeAny != '':
    raise Exception("Either run with --includeAll or --includeAny or neither, not both")
elif options.includeAll != '':
    dcards = [dc for dc in dcards if all([i in dc for i in options.includeAll.split('-')])]
elif options.includeAny != '':
    dcards = [dc for dc in dcards if any([i in dc for i in options.includeAny.split('-')])]

toProcess = 0
for dc in dcards:

    name= dc.replace("cards-", "")
    
    quantilesToRun = ['']
    if 'HybridNew' in options.combineMethod:
        if options.quantiles and "expectedFromGrid" in options.combineOptions:
                raise Exception("Either run with --expectedFromGrid as a combine option or with --quantiles as a script option, but not both.")
        if options.quantiles:
            quantilesToRun = ['', '0.025', '0.160', '0.500', '0.840', '0.975']
        elif "expectedFromGrid" in options.combineOptions:
            quant = options.combineOptions.split('expectedFromGrid ')[1].split(' ')[0]
            if quant == '-1':
                # deal with the case of observed
                quant = ''
            else:
                # add enough 0's to reach 3 digits after the .
                quant = quant + '0'*(3-len(quant.split('.')[1]))
                #quant = '.quant' + quant
            quantilesToRun = [quant]
                        
    for quant in quantilesToRun:
        
        # don't re run cards, unless running with --force
        quantName = '.quant' + quant if quant != '' else ''
        outFile = "higgsCombine{name}.{method}.mH125{quantName}.root".format(name=name, method=options.combineMethod.replace("Auto",""), quantName=quantName)
        if os.path.isfile(outFile) and not options.force:
            print(" -- skipping :", name, quant)
            continue
        elif os.path.isfile(outFile) and options.force:
            overwriteFile = outFile.replace(".root", ".overwritten.root")
            os.system(f"mv {outFile} {overwriteFile}")
            print(" --making:", name, quant)
        else:
            print(" --making:", name, quant)
        strippedOutFile = outFile.split(".root")[0]
        toProcess += 1

        # Write combine commmands

        rm_command = analysis.get('rm_command', '').format(name=name)
        combine_card_command = analysis.get('combineCards_command', '').format(name=name)
        text2workspace_command = analysis.get('text2workspace_command', '').format(name=name)

        # # remove the old combined cards
        # rm_command = "rm -rf cards-{}/combined.dat".format(name)

        # # make the combined.dat cards -- analysis-specific command
        # combine_card_command = analysis['combineCards'].format(name=name)

        # # converts .dat to .root
        # text2workspace_command = "text2workspace.py -m 125 cards-{name}/combined.dat -o cards-{name}/combined.root".format(name=name)

        # this is the command running combine. Some options are passed through the parser
        if 'HybridNew' in options.combineMethod:
            combine_method = " -M HybridNew --LHCmode LHC-limits "
            if options.quantiles and quant != '':
                 combine_method += f" --expectedFromGrid {quant} "
        elif options.combineMethod == 'AsymptoticLimits':
            combine_method = " -M AsymptoticLimits "
        # combine_command = (
        #     "combine "
        #     " --datacard cards-{name}/combined.root "
        #     " {combine_method}"
        #     " -m 125 --cl 0.95 --name {name}"
        #     " {options}"
        #     " --rAbsAcc 0.000001 --rRelAcc 0.01 "
        #     " --X-rtd MINIMIZER_analytic --X-rtd FAST_VERTICAL_MORPH ".format(
        #         name=name,
        #         combine_method=combine_method,
        #         options=options.combineOptions
        #     )
        # )
        combine_command = analysis.get('combine_command', '').format(name=name, combine_method=combine_method, options=options.combineOptions)
        
        if options.combineMethod == 'HybridNewAuto':
            if 'rMin' in options.combineOptions or 'rMax' in options.combineOptions:
                raise Exception("The HybrdiNewAuto method sets rMin and rMax automatically, incomptible if rMin and rMax passed to the combine options via -o.")
        
            # run the asymptotic command
            pre_combine_command = (
                "combine "
                " --datacard cards-{name}/combined.root "
                " -M AsymptoticLimits "
                " -m 125 --cl 0.95 --name {name}"
                " --rAbsAcc 0.00001 --rRelAcc 0.001 "
                " --X-rtd MINIMIZER_analytic --X-rtd FAST_VERTICAL_MORPH > asymptotic_output-{name}.txt ".format(
                    name=name,
                    options=options.combineOptions
                )
            ) 
            # grab the output from asymptotic 
            grab_boundaries_command = (
                " min_r=$(grep -oP 'r < \K[0-9.]*' asymptotic_output-{name}.txt | sort -n | head -n 1); "
                " max_r=$(grep -oP 'r < \K[0-9.]*' asymptotic_output-{name}.txt | sort -n | tail -n 1); "
                " echo Minimum r value from asymptotic limits: $min_r; "
                " echo Maximum r value from asymptotic limits: $max_r; "
                " min_r=$(echo \"$min_r / 1.0\" | bc -l); "
                " max_r=$(echo \"$max_r * 1.0\" | bc -l); "
                " echo \"Using r lower bound: $min_r \"; "
                " echo \"Using r upper bound: $max_r \"".format(name=name)
            )
            # and use those as boundaries for the toys
            combine_command += " --rMin $min_r --rMax $max_r "
            
            # the command that gets executed is the combination of all the above
            combine_command = pre_combine_command + " ;\n " + grab_boundaries_command + " ;\n " + combine_command

        # Execute and optionally print the commands   
        if options.print_commands:
            print('--- removing old combined datacard:', rm_command)
            print('--- combining datacards:', combine_card_command)
            print('--- text2workspace:', text2workspace_command)
            print('--- combine:', combine_command)

        # if dry run, skip the rest
        if options.dry: continue

        # run the commands!
        if options.method in ['multithread', 'iterative']:
            local_script_content = local_script_tempate.format(
                rm_command=rm_command,
                combine_card_command=combine_card_command,
                text2workspace_command=text2workspace_command,
                combine_command=combine_command,
                outFile=strippedOutFile
            )

            local_script_file = f'/tmp/submit_{strippedOutFile}.sh'
            with open(local_script_file, 'w') as f:
                f.write(local_script_content)

            if options.method == 'multithread':
                results.append(pool.apply_async(call_combine, (f'bash {local_script_file} ; rm {local_script_file}',)))

            elif options.method == 'iterative':
                subprocess.run(['bash', local_script_file])
                #os.remove(local_script_file)

        elif options.method == 'slurm':

            cpus = 1 # default value
            if '--fork' in options.combineOptions: # grab it from fork
                cpus = int(options.combineOptions.split('--fork ')[1].split(' ')[0])

            if options.combineMethod == 'AsymptoticLimits':
                mem_per_cpu = 1
                time_limit = '1:0:0'
            elif 'HybridNew' in options.combineMethod:
                mem_per_cpu = 4
                time_limit = '12:0:0'
            mem = str(mem_per_cpu*cpus)+'GB'

            slurm_script_content = slurm_script_template.format(
                                        rm_command=rm_command,
                                        combine_card_command=combine_card_command,
                                        text2workspace_command=text2workspace_command,
                                        combine_command=combine_command,
                                        work_dir=work_dir,
                                        log_dir=log_dir,
                                        mem=mem,
                                        cpus=cpus,
                                        time_limit=time_limit,
                                        sample=name,
                                        outFile=strippedOutFile)

            # Write the SLURM script to a file
            slurm_script_file = f'{log_dir}submit_{strippedOutFile}.sh'
            with open(slurm_script_file, 'w') as f:
                f.write(slurm_script_content)

            # Submit the SLURM job
            subprocess.run(['sbatch', slurm_script_file])

        elif options.method == 'condor':

            cpus = 1 # default value
            if '--fork' in options.combineOptions: # grab it from fork
                cpus = int(options.combineOptions.split('--fork ')[1].split(' ')[0])

            # set the memory
            if options.combineMethod == 'AsymptoticLimits':
                mem_per_cpu = 1
            elif 'HybridNew' in options.combineMethod:
                mem_per_cpu = 2
            mem = str(mem_per_cpu*cpus)+'GB'

            # Write the condor script to a file
            condor_script_content = condor_script_template.format(
                                        rm_command=rm_command,
                                        combine_card_command=combine_card_command,
                                        text2workspace_command=text2workspace_command,
                                        combine_command=combine_command,
                                        condor_out_dir=condor_out_dir,
                                        redirector=redirector
            )
            condor_script_file = f'{log_dir}submit_{strippedOutFile}.sh'
            with open(condor_script_file, 'w') as f:
                f.write(condor_script_content)

            # Write the condor submission script to a file
            condor_submission_content = condor_submission_script.format(
                                            jobdir=log_dir,
                                            script=f'submit_{strippedOutFile}',
                                            transfer_file=transfer_file,
                                            user=os.environ['USER'],
                                            proxy=f"x509up_u{os.getuid()}",
                                            queue='espresso',
                                            cpus=cpus,
                                            mem=mem,
                                            outFile=strippedOutFile)
            condor_submission_file = f'{log_dir}submit_{strippedOutFile}.sub'
            with open(condor_submission_file, 'w') as f:
                f.write(condor_submission_content)

            # Submit the condor job
            subprocess.run(['condor_submit', condor_submission_file])
                
if options.method == 'multithread':
    pool.close()
    for result in tqdm(results, desc="Processing", unit="job"):
        result.get()
    pool.join()
    print()
    print(" ----------------- ")
    for result in results:
        out, err = result.get()
        print(err.decode('utf-8'))
        print(" ----------------- ")
        print()

print("Processed jobs for", toProcess, "samples.")
