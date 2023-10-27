"""
Generate yaml files for each year for data, expected, and each signal point for the SUEP ggF analyses.
Configurable parameters are at the top of the file.

Authors: Pieter van Steenwhegen and Luca Lavezzo
"""


import os
import sys
import glob

#### PARAMETERS #########################################################
# input directory
histDirectory = '/data/submit/{}/SUEP/outputs/'.format(os.environ['USER'])
# make a dictionary, keys are years, values are hitsogram tags
signalTags = {
    '2016': 'approval_2016',
    '2016apv': 'approval_2016apv',
    '2017': 'approval_2017',
    '2018': 'approval',
}
dataTags = {
    '2016': 'unblind',
    '2017': 'unblind',
    '2018': 'unblind',
}
channel = 'offline'
dataLabel = 'JetHT_A02'
#########################################################################

existing_files = os.listdir(histDirectory)
missing_files = []

signalFilelists = {}
for year, tag in signalTags.items():
    signalFilelists[year] = [ histFile for histFile in existing_files if histFile.endswith(tag+'.root')]

dataFilelists = {}
for year, tag in dataTags.items():
    dataFilelists[year] = [ histFile for histFile in existing_files if histFile.endswith(tag+'.root')]

# print out missing samples
if len(missing_files) > 0:
    print("WARNING: {} files missing.".format(len(missing_files)))
    for s in missing_files:
        print("-- Missing", s)

for year, tag in signalTags.items():

    # 2016apv we merge with 2016
    if year == '2016apv':
        continue

    # form data list
    output = ""
    output += 'data:\n'
    output += '  files:\n'
    for f in dataFilelists[year]:
        output += '    - /{histDirectory}/{f}\n'.format(histDirectory=histDirectory, f=f)
    output += '  type:\n'
    output += '    data\n'
    output += '  color: 895\n\n'

    # expected uses data, so we just copy!
    output += output.replace("data:", "expected:")

    # form signal list
    for f in signalFilelists[year]:

        name = f.split('/')[-1].split('_TuneCP5')[0]+'_TuneCP5_13TeV-pythia8'

        files = '- {histDirectory}/{f}\n'.format(histDirectory=histDirectory, f=f)
        if f.replace(signalTags['2016'], signalTags['2016apv']) in signalFilelists['2016apv']:
            files += '    - {histDirectory}/{f}\n'.format(histDirectory=histDirectory, f=f.replace(signalTags['2016'], signalTags['2016apv']))

        output += (
        "{name}:\n"
        "  files:\n"
        "    {files}"
        "  type:\n"
        "    signal\n\n"

        ).format(name=name, files=files, user=os.environ['USER'])

    # write out the output
    outfile = 'SUEP_test_{}.yaml'.format(year)
    with open(outfile, 'w') as f:
        f.write(output)
    print("Wrote", outfile)
