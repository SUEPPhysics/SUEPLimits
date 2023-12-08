"""
Script to do any of the following:

1. Monitor the completion of the cards.
    Checks that for sample in the config/<yaml_file>, every sample has all the cards in the 
    local directory/tag.

2. Monitor the completion of the limits produced via combine, and verify that the they are not corrupted.
    Will check that for each cards-SAMPLE/ subdirectory under the directory/tag --tag, the correspodning 
    limit files have been produced successfully.

3. Move the limit files from the remote directory, where condor places the outputs, to the local directory/tag.

Author: Luca Lavezzo
Date: November, 2023
"""

import os
import json
import uproot
import datetime
import argparse
import yaml
import logging

def main ():

    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument("-c", "--checkMissingCards", action='store_true')
    parser.add_argument("-l", "--checkMissingLimits", action='store_true')
    parser.add_argument("-d", "--deleteCorruptedLimits", action='store_true', help="Deletes empty or corrupted limit files. Must be run with --checkMissingLimits")
    parser.add_argument("-M", "--combineMethod", type=str, required=False, choices=["HybridNew", "AsymptoticLimits"], default='HybridNew', help="Which limit files to look for. Must be run with --checkMissingLimits.")
    parser.add_argument("-m", "--moveLimits", action='store_true')
    parser.add_argument("-r", "--remoteDir", type=str, required=False, default='', help="Where to move the limits from. Must be run with --move.")
    parser.add_argument("-t", "--tag", type=str, help="Production tag (and name of local directory) where the cards and limits are stored)", required=True, default='')
    parser.add_argument("-dry", "--dry", action='store_true', help="Don't delete any limit files.")
    parser.add_argument("-v", "--verbose", action='store_true', help="Increase output verbosity")
    args = parser.parse_args()

    # set verbosity level
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    # some checks
    if not args.checkMissingLimits and not args.checkMissingCards and not args.moveLimits:
        raise ValueError("Please specify at least one of --checkMissingCards, --checkMissingLimits, or --moveLimits.")
    if args.moveLimits and args.remoteDir == '':
        raise ValueError("Please specify remote directory with -r when asking to move files.")
    if args.deleteCorruptedLimits and not args.checkMissingLimits:
        raise ValueError("Please specify --checkMissingLimits when asking to delete corrupted limits.")
    if (args.moveLimits and not args.remoteDir) or (not args.moveLimits and args.remoteDir):
        raise ValueError("Please specify both --moveLimits and --remoteDir or neither.")

    # set directories
    remoteLimitDir = args.remoteDir
    limitDir = args.tag

    logging.info("monitor.py will run the following modes:")
    if args.checkMissingCards: logging.info("--checkMissingCards")
    if args.moveLimits: logging.info("--moveLimits")
    if args.checkMissingLimits: logging.info("--checkMissingLimits")

    if args.checkMissingCards:

        logging.info('')
        logging.info("-"*50)
        logging.info("--checkMissingCards")
        logging.info("Checking for missing cards in the local directory.")
        logging.info("Local directory: " + limitDir)
        logging.info('')

        bins  = ['Bin1Sig','Bin2Sig',
                'Bin3Sig','Bin4Sig',
                'Bin0crF','Bin1crF','Bin2crF',
                'Bin3crF','Bin4crF',
                'cat_crA','cat_crB','cat_crC','cat_crD','cat_crE','cat_crG','cat_crH']
        config_file = "config/SUEP_inputs_{}.yaml"
        years = ['2016', '2017', '2018']
        config_file = "config/SUEP_inputs_{}.yaml"

        missingCardsSamples = []
        for year in years:
            with open(config_file.format(year)) as f: 
                inputs = yaml.safe_load(f.read())
            for sample in inputs.keys():
                if "SUEP" not in sample: continue
                for bin_name in bins: 
                    for eof in ['dat','root']:
                        path = '{}/cards-{}/shapes-{}{}.{}'.format(limitDir, sample, bin_name, year, eof)
                        if not os.path.exists(path) or os.path.getsize(path) == 0: 
                            logging.debug("--missing:", path)
                            missingCardsSamples.append(sample)
                            continue
        
        missingCardsSamples = list(set(missingCardsSamples))

        logging.info(f"Found {len(missingCardsSamples)} samples with missing cards.")
        if len(missingCardsSamples) > 0 and args.verbose:
            logging.debug()
            logging.debug("The following samples have one or more missing cards:")
            for sample in set(missingCardsSamples):
                logging.debug(sample)

        # write out missing samples to file
        now = datetime.datetime.now()
        outCardsFile = 'missingCards_'+now.strftime("%Y-%m-%d_%H-%M-%S")+'.txt'
        logging.info("Outputting results to " +  outCardsFile)
        with open(outCardsFile, 'w') as f:  
            for item in missingCardsSamples:
                f.write("%s\n" % item)

    if args.moveLimits:

        logging.info('')
        logging.info("-"*50)
        logging.info("--moveLimits")
        logging.info("Moving limit files from the remote directory to the local directory")
        logging.info("Checking each .root limit file for corruption and deleting corrupted files. Might take a little longer...")
        logging.info("Remote directory: " + remoteLimitDir)
        logging.info("Local directory: " + limitDir)
        logging.info('')

        nMoved = 0
        nDeleted = 0

        for outFile in os.listdir(remoteLimitDir):

            # check if corresponding file is missing in outDir, if so, cp it there
            if not os.path.isfile(os.path.join(limitDir,outFile)):
                logging.debug(outFile)
                remoteFile = os.path.join(remoteLimitDir,outFile)
                try:
                    f = uproot.open(remoteFile)
                    if len(f['limit']['limit'].array()) == expected_length:
                        nMoved +=1 
                        os.system('cp '+remoteFile+' '+limitDir)
                    else:
                        # raise error if we find empty limits!
                        raise ValueError
                except:
                    nDeleted += 1
                    logging.debug("\t --> Limit not found in the file " +  remoteFile + " deleting...")
                    if not args.dry: os.system('rm '+remoteFile)

        logging.info('')
        if nDeleted > 0: logging.info(f"Deleted {nDeleted} bad limit files from the remote directory.")
        logging.info(f"Moved {nMoved} new limit files.")

    if args.checkMissingLimits:

        logging.info('')
        logging.info("-"*50)
        logging.info("--checkMissingLimits")
        logging.info("Checking for missing limits in the local directory.")
        logging.info("Local directory: " + limitDir)
        if args.deleteCorruptedLimits:
            logging.info("Checking each .root limit file for corruption and deleting corrupted files. Might take a little longer...")
        logging.info('')

        nMissingLimits = 0
        nBadLimit = 0
        nTotalLimits = 0
        missingLimits = []
        limit = args.combineMethod
        expected_length = 1 if limit == 'HybridNew' else 6    # size of the limit array in the root file

        all_samples = []
        # list all subdirectories of the limitDir, these are the samples we will check
        # for completion of the limits
        for subdir in os.listdir(limitDir):
            if os.path.isdir(os.path.join(limitDir,subdir)):
                if "cards-" in subdir:
                    all_samples.append(subdir.replace("cards-",""))

        for sample in all_samples:

            # the quantiles are only needed for running toys with HybridNew
            if limit == 'AsymptoticLimits':
                quants = [""]
            elif limit == 'HybridNew':
                quants = ['', '.quant0.500', '.quant0.160', '.quant0.840', '.quant0.975', '.quant0.025']

            # check if file higgsCombine{sample}.HybridNew.mH125.root exists
            for quant in quants:
                nTotalLimits += 1

                f = f"higgsCombine{sample}.{limit}.mH125{quant}.root"
                fname = os.path.join(limitDir,f)
                if not os.path.isfile(fname):
                    nMissingLimits +=1
                    missingLimits.append(fname)

                # if request, check corrupted files by loading them with uproot.
                # deletes the file if it finds it corrupted
                elif args.deleteCorruptedLimits:
                    f = uproot.open(fname)
                    try:
                        if len(f['limit']['limit'].array()) == expected_length:
                            continue
                        else:
                            # raise error if we find empty limits!
                            raise ValueError
                    except:
                        logging.debug("\t --> Limit not found in the file " + fname + " deleting...")
                        if not args.dry: 
                            #os.system('rm '+fname)
                            os.system('mv '+fname+' '+fname.replace('.root','.corrupted.root'))
                        nBadLimit += 1
                        nMissingLimits += 1
                        missingLimits.append(fname)

        logging.info('')
        logging.info(f"Files Completion Rate: {round((nTotalLimits-nMissingLimits)*100/nTotalLimits,2)}%")
        logging.info(f"Still to process {nMissingLimits} out of {nTotalLimits} limit files.")
        if args.deleteCorruptedLimits: logging.info(f"Found and deleted {nBadLimit} bad limit files from the local directory.")

        # write out missing samples to file
        now = datetime.datetime.now()
        outLimitFile = 'missingLimits_'+now.strftime("%Y-%m-%d_%H-%M-%S")+'.txt'
        logging.info("Outputting results to " + outLimitFile)
        with open(outLimitFile, 'w') as f:  
            for item in missingLimits:
                f.write("%s\n" % item)

if __name__ == "__main__":
    main()
