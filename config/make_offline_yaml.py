"""
Generate yaml files for each year for data, expected, and each signal point for the SUEP ggF analyses.
Configurable parameters are at the top of the file.
2016 and 2016apv signals are combined. Data is assumed to be already combined.

Authors: Pieter van Steenwhegen and Luca Lavezzo
"""


import os
import sys
import glob

#### PARAMETERS #########################################################
# input directory
histDirectory = '/data/submit/{}/SUEP/outputs/'.format(os.environ['USER'])
# signalList = "/home/submit/lavezzo/SUEP/SUEPCoffea_dask/filelist/Offline/list_{}_full_signal_offline.txt"
signalList = "/home/submit/lavezzo/SUEP/SUEPCoffea_dask/filelist/WH/list_{}_ttHsignal_private.txt"
dataList = "/home/submit/lavezzo/SUEP/SUEPCoffea_dask/filelist/Offline/list_{}_JetHT_A02_offline.txt"
# make a dictionary, keys are years, values are histogram tags
# signalTags = {
#     '2016': 'approval_2016',
#     '2016apv': 'approval_2016apv',
#     '2017': 'approval_2017',
#     '2018': 'approval',
# }
signalTags = {
    '2016': 'ggF_limits_ttH',
    '2016apv': 'ggF_limits_ttH',
    '2017': 'ggF_limits_ttH',
    '2018': 'ggF_limits_ttH',
}
dataTags = {
    '2016apv': 'fix_JEC_final',
    '2016': 'fix_JEC_final',
    '2017': 'fix_JEC_final',
    '2018': 'fix_JEC_final',
}
combine2016 = True
#########################################################################

# make a dictionary, keys are years, values are lists of files
signalFilelists = {}
dataFilelists = {}
for year, tag in signalTags.items():

    signalFilelists[year] = []

    # get all histogram files for this year in the dir
    tag_files = glob.glob(histDirectory + '*' + tag + '.root')

    # use the signalList and dataList to get a list of samples we expect to have histograms
    with open(signalList.format(year), 'r') as f:
        signalSamples = f.read().splitlines()
    signalSamples = [s.split("/")[-1].replace(".root", "") for s in signalSamples]

    # for each sample we need, check if the histogram file exists
    missing_samples = []
    for s in signalSamples:
        s_file = histDirectory +  s + '_' + tag + '.root'
        if s_file in tag_files:
            signalFilelists[year].append(s_file)
        else:
            missing_samples.append(s)
            print(" --- Missing:", s_file)

    # print out missing samples
    if len(missing_samples) > 0:
        print("WARNING: {} samples missing in {} with tag {}.".format(len(missing_samples), year, tag))

for year, tag in dataTags.items():

    dataFilelists[year] = []

    # get all histogram files for this year in the dir
    tag_files = glob.glob(histDirectory + '*' + tag + '*.root')

    # use the dataList and dataList to get a list of samples we expect to have histograms
    with open(dataList.format(year), 'r') as f:
        dataSamples = f.read().splitlines()
    dataSamples = [d.split("/")[-1].replace(".root", "") for d in dataSamples]

    # for each sample we need, check if the histogram file exists
    missing_samples = []
    for d in dataSamples:
        d_file = histDirectory + d.split("/")[-1] + '_' + tag + '.root'
        if d_file in tag_files:
            dataFilelists[year].append(d_file)
        else:
            missing_samples.append(d)
            print(" --- Missing:", d_file)

    # print out missing samples
    if len(missing_samples) > 0:
        print("WARNING: {} samples missing in {} with tag {}.".format(len(missing_samples), year, tag))

for year, tag in signalTags.items():

    output = ""
    output += 'era: {year}\n\n'.format(year=year)

    # form data list
    data_obs = ''
    data_obs += 'data:\n'
    data_obs += '  files:\n'
    for f in dataFilelists[year]:
        data_obs += '    - {f}\n'.format(f=f)
    data_obs += '  type:\n'
    data_obs += '    data\n'
    data_obs += '  color: 895\n\n'

    # expected uses data, so we just copy!
    output += data_obs
    output += data_obs.replace("data:", "expected:")

    # form signal list
    for f in signalFilelists[year]:

        sample = f.split('/')[-1].replace(".root", "").replace("_"+tag, "")
        sample = sample.replace("13TeV", "13TeV-pythia8")
        process = sample.split("_UL")[0]

        files = '- {f}\n'.format(f=f)
        
        files += '  sample: {sample}\n'.format(sample=sample)

        output += (
        "{process}:\n"
        "  files:\n"
        "    {files}"
        "  type:\n"
        "    signal\n\n"
        ).format(process=process, files=files)

    # write out the output
    outfile = 'ttHSUEP_inputs_{}.yaml'.format(year)
    with open(outfile, 'w') as f:
        f.write(output)
    print("Wrote", outfile)
