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
    args = parser.parse_args()

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

    if args.checkMissingCards:

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
                            print("--missing:", path)
                            missingCardsSamples.append(sample)
                            continue
        
        print("Found", len(missingCardsSamples), "samples with missing cards.")
        if len(missingCardsSamples) > 0:
            print()
            print("The following samples have one or more missing cards:")
            for sample in set(missingCardsSamples):
                print(sample)

        # write out missing samples to file
        now = datetime.datetime.now()
        outCardsFile = 'missingCards_'+now.strftime("%Y-%m-%d_%H-%M-%S")+'.txt'
        print("Outputting results to", outCardsFile)
        with open(outCardsFile, 'w') as f:  
            for item in missingCardsSamples:
                f.write("%s\n" % item)

    if args.moveLimits:

        nMoved = 0
        nDeleted = 0

        for outFile in os.listdir(remoteLimitDir):

            # check if corresponding file is missing in outDir, if so, cp it there
            if not os.path.isfile(os.path.join(limitDir,outFile)):
                print(outFile)
                remoteFile = os.path.join(remoteLimitDir,outFile)
                f = uproot.open(remoteFile)
                try:
                    if len(f['limit']['limit'].array()) > 0:
                        nMoved +=1 
                        os.system('cp '+remoteFile+' '+limitDir)
                    else:
                        # raise error if we find empty limits!
                        raise ValueError
                except:
                    nDeleted += 1
                    print("\t --> Limit not found in the file", remoteFile, "deleting...")
                    if not args.dry: os.system('rm '+remoteFile)

        print()
        if nDeleted > 0: print("Deleted", nDeleted, "bad limit files from the remote directory.")
        print("Moved", nMoved, "new limit files.")

    if args.checkMissingLimits:

        if args.deleteCorruptedLimits:
            print("Checking each .root limit file for corruption and deleting corrupted files. Might take a little longer...")

        nMissingLimits = 0
        nBadLimit = 0
        nTotalLimits = 0
        missingLimits = []
        limit = args.combineMethod

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
                        if len(f['limit']['limit'].array()) > 0:
                            continue
                        else:
                            # raise error if we find empty limits!
                            raise ValueError
                    except:
                        print("\t --> Limit not found in the file", fname, "deleting...")
                        if not args.dry: os.system('rm '+fname)
                        nBadLimit += 1
                        nMissingLimits += 1
                        missingLimits.append(fname)

        print()
        print("Files Completion Rate: {}%".format(round((nTotalLimits-nMissingLimits)*100/nTotalLimits,2)))
        print("Still to process", nMissingLimits, "out of", nTotalLimits, "limit files.")
        if args.deleteCorruptedLimits: print("Found and deleted", nBadLimit, "bad limit files from the local directory.")

        # write out missing samples to file
        now = datetime.datetime.now()
        outLimitFile = 'missingLimits_'+now.strftime("%Y-%m-%d_%H-%M-%S")+'.txt'
        print("Outputting results to", outLimitFile)
        with open(outLimitFile, 'w') as f:  
            for item in missingLimits:
                f.write("%s\n" % item)

if __name__ == "__main__":
    main()
