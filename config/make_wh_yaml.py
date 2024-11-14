"""
Generate yaml files for each year for data, expected, and each signal point for the SUEP ggF analyses.
Configurable parameters are at the top of the file.
2016 and 2016apv signals are combined. Data is assumed to be already combined.

Authors: Pieter van Steenwhegen and Luca Lavezzo
"""

import os
import glob

#### PARAMETERS #########################################################
# input directory
histDirectory = '/ceph/submit/data/user/{}/{}/SUEP/outputs/'.format(os.environ['USER'][0], os.environ['USER'])
signalList = "/home/submit/lavezzo/SUEP/SUEPCoffea_dask/filelist/WH/list_{}_signal_generic.txt"
dataList = "/home/submit/lavezzo/SUEP/SUEPCoffea_dask/filelist/WH/list_{}_Data_WH.txt"
#crwjList = "/home/submit/lavezzo/SUEP/SUEPCoffea_dask/filelist/WH/list_{}_Data_WH.txt"
vrgjList = "/home/submit/lavezzo/SUEP/SUEPCoffea_dask/filelist/WH/list_{}_Data_VRGJ.txt"
# make a dictionary, keys are years, values are histogram tags
signalTags = {
    '2018': 'WH_11_2_signals_limits_2018',
}
dataTags = {
    '2018': 'WH_11_14_data_limits_2018',
}
# crwjTags = {
#     '2018': 'WH_CRWJ_limits_10_24',
# }
vrgjTags = {
    '2018': 'WH_VRGJ_limits_10_24',
}
combine2016 = True
#########################################################################

def get_file_list(year, tag, file_list_path, hist_directory):
    file_list = []
    tag_files = glob.glob(hist_directory + '/' + tag + '/*' + '.root')
    with open(file_list_path.format(year), 'r') as f:
        samples = f.read().splitlines()
    samples = [s.split("/")[-1].replace(".root", "") for s in samples]
    missing_samples = []
    for s in samples:
        s_file = hist_directory + '/' + tag + '/' + s + '.root'
        if s_file in tag_files:
            file_list.append(s_file)
        else:
            missing_samples.append(s)
            print(" --- Missing:", s_file)
    if missing_samples:
        print("WARNING: {} samples missing in {} with tag {}.".format(len(missing_samples), year, tag))
    return file_list

def generate_yaml(year, data_file_list, crwj_file_list, vrgj_file_list, signal_file_list, tag):
    output = 'era: {year}\n\n'.format(year=year)

    # SR
    data_obs = 'WJHSdata:\n  files:\n'
    for f in data_file_list:
        data_obs += '    - {f}\n'.format(f=f)
    data_obs += '  type:\n    data\n  color: 895\n\n'
    output += data_obs
    output += data_obs.replace("WJHSdata:", "WJHSexpected:")

    # CRWJ
    # crwj = 'WJLSdata:\n  files:\n'
    # for f in crwj_file_list:
    #     crwj += '    - {f}\n'.format(f=f)
    # crwj += '  type:\n    data\n  color: 797\n\n'
    # output += crwj
    # output += crwj.replace("WJLSdata:", "WJLSexpected:")

    # VRGJlowS
    # vrgjlow = 'GJLSdata:\n  files:\n'
    # for f in vrgj_file_list:
    #     vrgjlow += '    - {f}\n'.format(f=f)
    # vrgjlow += '  type:\n    data\n  color: 797\n\n'
    # output += vrgjlow
    # output += vrgjlow.replace("GJLSdata:", "GJLSexpected:")

    # VRGJhighS
    vrgjhigh = 'GJHSdata:\n  files:\n'
    for f in vrgj_file_list:
        vrgjhigh += '    - {f}\n'.format(f=f)
    vrgjhigh += '  type:\n    data\n  color: 797\n\n'
    output += vrgjhigh
    output += vrgjhigh.replace("GJHSdata:", "GJHSexpected:")
    
    # signals
    for f in signal_file_list:
        sample = f.split('/')[-1].replace(".root", "").replace("_"+tag, "")
        process = sample
        files = '- {f}\n  sample: {sample}\n'.format(f=f, sample=sample)
        output += "{process}:\n  files:\n    {files}  type:\n    signal\n\n".format(process=process, files=files)
    outfile = 'WH_inputs_{}.yaml'.format(year)

    with open(outfile, 'w') as f:
        f.write(output)
    print("Wrote", outfile)

def main():
    signal_filelists = {}
    data_filelists = {}
    crwj_filelists = {}
    vrgj_filelists = {}

    for year, tag in signalTags.items():
        signal_filelists[year] = get_file_list(year, tag, signalList, histDirectory)
    for year, tag in dataTags.items():
        data_filelists[year] = get_file_list(year, tag, dataList, histDirectory)
    # for year, tag in crwjTags.items():
    #     crwj_filelists[year] = get_file_list(year, tag, crwjList, histDirectory)
    for year, tag in vrgjTags.items():
        vrgj_filelists[year] = get_file_list(year, tag, vrgjList, histDirectory)

    for year, tag in signalTags.items():
        generate_yaml(year, data_filelists[year], [], vrgj_filelists[year], signal_filelists[year], tag)

if __name__ == "__main__":
    main()
