import os
directory = '/data/submit/{}/SUEP/outputs/'.format(os.environ['USER'])
filenames = os.listdir(directory)
names_2016 = [i for i in filenames if ('Impacts_2016.root' in i) and ('GluGluToSUEP' in i) and ('generic' in i)]
names_2016apv = [i for i in filenames if ('Impacts_2016apv.root' in i) and ('GluGluToSUEP' in i) and ('generic' in i)]


for name in names_2016:
    print("\n")
    print(name.split('_TuneCP5')[0]+'_TuneCP5_13TeV-pythia8:')
    print("  files:")
    print("    - /data/submit/{}/SUEP/outputs/{}".format(os.environ['USER'], name))
    if name.replace('Impacts_2016', 'Impacts_2016apv') in names_2016apv:
        print("    - /data/submit/{}/SUEP/outputs/{}".format(os.environ['USER'], name.replace('Impacts_2016', 'Impacts_2016apv')))
    # print(("    - /data/submit/pvanstee/SUEP/outputs/{}".format(name)).replace('2016_private_v2_correct','2016apv_private_v0_correct')) # To add 2016apv to 2016 data
    print("  type:")
    print("    signal")

# To run: python make_yaml.py > new_output.txt
