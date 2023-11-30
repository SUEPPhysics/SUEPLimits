import os
import glob
import multiprocessing
from multiprocessing.pool import ThreadPool
import subprocess
import shlex
import argparse

# HTCondor script template
condor_script_template = '''

echo "Setting up environment"
export VO_CMS_SW_DIR=/cvmfs/cms.cern.ch
source $VO_CMS_SW_DIR/cmsset_default.sh
export SCRAM_ARCH=slc7_amd64_gcc700
cmsrel CMSSW_10_2_13
cd CMSSW_10_2_13/src
cmsenv

echo "Fetching HiggsAnalysis combine"
git clone https://github.com/cms-analysis/HiggsAnalysis-CombinedLimit.git HiggsAnalysis/CombinedLimit
cd $CMSSW_BASE/src/HiggsAnalysis/CombinedLimit
git fetch origin
git checkout v8.0.1

echo "Fetching CombineHarvester"
cd $CMSSW_BASE/src
bash <(curl -s https://raw.githubusercontent.com/cms-analysis/CombineHarvester/master/CombineTools/scripts/sparse-checkout-https.sh)

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

xrdcp *.root root://submit50.mit.edu/{condor_out_dir}/
'''

# HTCondor submission script
condor_submission_script = '''
universe              = vanilla
request_disk          = 5GB
request_memory        = 10GB
request_cpus          = 10
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
+DESIRED_Sites        = "mit_tier2,mit_tier3,T2_AT_Vienna,T2_BE_IIHE,T2_BE_UCL,T2_BR_SPRACE,T2_BR_UERJ,T2_CH_CERN,T2_CH_CERN_AI,T2_CH_CERN_HLT,T2_CH_CERN_Wigner,T2_CH_CSCS,T2_CH_CSCS_HPC,T2_CN_Beijing,T2_DE_DESY,T2_DE_RWTH,T2_EE_Estonia,T2_ES_CIEMAT,T2_ES_IFCA,T2_FI_HIP,T2_FR_CCIN2P3,T2_FR_GRIF_IRFU,T2_FR_GRIF_LLR,T2_FR_IPHC,T2_GR_Ioannina,T2_HU_Budapest,T2_IN_TIFR,T2_IT_Bari,T2_IT_Legnaro,T2_IT_Pisa,T2_IT_Rome,T2_KR_KISTI,T2_MY_SIFIR,T2_MY_UPM_BIRUNI,T2_PK_NCP,T2_PL_Swierk,T2_PL_Warsaw,T2_PT_NCG_Lisbon,T2_RU_IHEP,T2_RU_INR,T2_RU_ITEP,T2_RU_JINR,T2_RU_PNPI,T2_RU_SINP,T2_TH_CUNSTDA,T2_TR_METU,T2_TW_NCHC,T2_UA_KIPT,T2_UK_London_IC,T2_UK_SGrid_Bristol,T2_UK_SGrid_RALPP,T2_US_Caltech,T2_US_Florida,T2_US_Nebraska,T2_US_Purdue,T2_US_UCSD,T2_US_Vanderbilt,T2_US_Wisconsin,T3_CH_CERN_CAF,T3_CH_CERN_DOMA,T3_CH_CERN_HelixNebula,T3_CH_CERN_HelixNebula_REHA,T3_CH_CMSAtHome,T3_CH_Volunteer,T3_US_HEPCloud,T3_US_NERSC,T3_US_OSG,T3_US_PSC,T3_US_SDSC,T3_US_MIT"
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
#SBATCH --oversubscribe

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

# singularity run --bind /cvmfs/,/work/ /cvmfs/cvmfs.cmsaf.mit.edu/submit/work/submit/submit-software/centos/centos7p9 "source ~/.bsahrc; cd {work_dir}; {rm_command}; {combine_card_command}; {text2workspace_command}; {combine_command}"

'''


def call_combine(cmd):
    p = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    return (out, err)


parser = argparse.ArgumentParser()
parser.add_argument(
        "-m", "--method", type=str, default="iterative", choices=['iterative', 'slurm', 'multithread', 'condor'], help="How to execute the code."
)
parser.add_argument("-p"  , "--print_commands"   , action='store_true', help='Print the executed combine commands.')
parser.add_argument("-file"  , "--file", type=str, help='Rerun a list of datacards.')
parser.add_argument("-i"  , "--input", type=str, required=True, help='Where to find the cards.')
parser.add_argument("-f"  , "--force", action='store_true', help="Force rerunning of limits. By default will not re-run combine if the output .root file exists.")
parser.add_argument("-M"  , "--combineMethod", type=str, default="HybridNew", choices=['HybridNew', 'AsymptoticLimits'], help="Combine method to use. Supported: HybridNew, AsymptoticLimits")
parser.add_argument("-o"  , "--combineOptions", type=str, default="", help="Additional options to run the combine command with.")
parser.add_argument("-a"  , "--allQuantiles", action='store_true', help="Run all quantiles for HybridNew. Overrides --combineOptions '-- expectedFromGrid X'.")
parser.add_argument("-d"  , "--dry", action='store_true', help="Dry run. Print the commands but don't run them.")
parser.add_argument("-include", "--include", type=str, default='', help="Pass a '-' separated list of strings you want your samples to include. e.g. generic-mPhi300 will only run samples that contain 'generic' and 'mPhi300' in the name.")
options = parser.parse_args()

# change cwd to the input tag: combine will read the cards from here and will make the higgsCombine file here
os.chdir(options.input)
print("Working in", options.input)
print("Running with", options.method, "method,")

# define method-specific variables
if options.method == 'multithread':
    pool = ThreadPool(multiprocessing.cpu_count())
    results = []
elif options.method == 'iterative':
    print("Make sure you have the correct CMSSW environment set up! i.e. run cmsenv before running this script.")
elif options.method == 'slurm':
    work_dir = os.getcwd()
    log_dir = '/work/submit/{}/SUEP/logs/{}_{}/'.format(os.environ['USER'], 'slurm_runcombine', options.input)
    if not os.path.isdir(log_dir): os.mkdir(log_dir)
elif options.method == 'condor':
    work_dir =os.getcwd()
    log_dir = '/work/submit/{}/SUEP/logs/{}_{}/'.format(os.environ['USER'], 'condor_runcombine', options.input)
    condor_out_dir = "/store/user/{}/SUEP/{}_{}/".format(os.environ['USER'], 'condor_runcombine', options.input)
    out_dir = '/data/submit/cms/store/user/{}/SUEP/{}_{}/'.format(os.environ['USER'], 'condor_runcombine', options.input)
    if not os.path.isdir(log_dir): os.mkdir(log_dir)
    if not os.path.isdir(out_dir): os.mkdir(out_dir)
    
    # tar up the cards for transferring, if using condor
    if not os.path.isfile('cards.tar.gz'):
        os.system("find . -type d -name 'cards*' -exec tar -czvf cards.tar.gz {} +")
    transfer_file = os.path.join(os.getcwd(), 'cards.tar.gz')
    
# Read in the datacards
if options.file != None:
    with open(options.file) as f:
        samples = f.read().splitlines()
    dcards = ["cards-{}".format(s) for s in samples]
else:
    dcards = glob.glob("cards-*")

# select datacards based on the --include options
if options.include != '':
    dcards = [dc for dc in dcards if all([i in dc for i in options.include.split('-')])]

toProcess = 0
for dc in dcards:

    name= dc.replace("cards-", "")
    if "SUEP" not in name:
        continue

    # don't re run cards, unless running with --force
    outFile = "higgsCombine{name}.{method}.mH125.root".format(name=name, method=options.combineMethod)
    # deal with HybridNew naming scheme
    if options.combineMethod == 'HybridNew':
        if "expectedFromGrid" in options.combineOptions:
            quant = options.combineOptions.split('expectedFromGrid ')[1].split(' ')[0]
            if quant == '-1':
                # deal with the case of observed
                quant = ''
            else:
                # add enough 0's to reach 3 digits after the .
                quant = quant + '0'*(3-len(quant.split('.')[1]))
                quant = '.quant' + quant
            outFile = "higgsCombine{name}.{method}.mH125{quant}.root".format(name=name, method=options.combineMethod, quant=quant)
    
    if os.path.isfile(outFile) and not options.force:
        print(" -- skipping :", name)
        continue
    else:
        print(" --making:", name)
    strippedOutFile = outFile.split(".root")[0]
    
    toProcess += 1

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
        " --rAbsAcc 0.00001 --rRelAcc 0.001 "
        " --X-rtd MINIMIZER_analytic --X-rtd FAST_VERTICAL_MORPH ".format(
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

    # if dry run, skip the rest
    if options.dry: continue
    
    # run the commands!
    if options.method == 'multithread':
        os.system(rm_command)
        os.system(combine_card_command)
        os.system(text2workspace_command)
        results.append(pool.apply_async(call_combine, (combine_command,)))

    elif options.method == 'slurm':

        if options.combineMethod == 'AsymptoticLimits':
            mem = '1GB'
            time_limit = '1:0:0'
        elif options.combineMethod == 'HybridNew':
            mem = '4GB'
            time_limit = '12:0:0'

        slurm_script_content = slurm_script_template.format(
                                    rm_command=rm_command,
                                    combine_card_command=combine_card_command,
                                    text2workspace_command=text2workspace_command,
                                    combine_command=combine_command,
                                    work_dir=work_dir,
                                    log_dir=log_dir,
                                    mem=mem,
                                    time_limit=time_limit,
                                    sample=name,
                                    outFile=strippedOutFile)

        # Write the SLURM script to a file
        slurm_script_file = f'{log_dir}submit_{strippedOutFile}.sh'
        with open(slurm_script_file, 'w') as f:
            f.write(slurm_script_content)

        # Submit the SLURM job
        subprocess.run(['sbatch', slurm_script_file])

    elif options.method == 'iterative':
        subprocess.run('cmsenv', shell=True)
        subprocess.run(rm_command, shell=True)
        subprocess.run(combine_card_command, shell=True)
        subprocess.run(text2workspace_command, shell=True)
        subprocess.run(combine_command, shell=True)

    elif options.method == 'condor':
        
        # Write the condor script to a file
        condor_script_content = condor_script_template.format(
                                    rm_command=rm_command,
                                    combine_card_command=combine_card_command,
                                    text2workspace_command=text2workspace_command,
                                    combine_command=combine_command,
                                    condor_out_dir=condor_out_dir)
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
                                        outFile=strippedOutFile)
        condor_submission_file = f'{log_dir}submit_{strippedOutFile}.sub'
        with open(condor_submission_file, 'w') as f:
            f.write(condor_submission_content)

        # Submit the condor job
        subprocess.run(['condor_submit', condor_submission_file])
                
if options.method == 'multithread':
    pool.close()
    pool.join()

    for result in results:
        out, err = result.get()
        if "error" in str(err).lower():
            print(str(err))
            print(" ----------------- ")
            print()

print("Processed jobs for", toProcess, "samples.")
