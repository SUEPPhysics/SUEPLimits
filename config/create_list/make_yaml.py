import os
directory = '/data/submit/pvanstee/SUEP/outputs/'
filenames = os.listdir(directory)
names = [i for i in filenames if ('2017_private_v1_correct.root' in i) and ('GluGluToSUEP' in i)]

for name in names:
   print("\n")
   print(name.split('_TuneCP5')[0]+'_TuneCP5_13TeV-pythia8:')
   print("  files:")
   print("    - /data/submit/pvanstee/SUEP/outputs/{}".format(name))
   # print(("    - /data/submit/pvanstee/SUEP/outputs/{}".format(name)).replace('2016_private_v2_correct','2016apv_private_v0_correct')) # To add 2016apv to 2016 data
   print("  type:")
   print("    signal")

# To run: python make_yaml.py > new_output.txt

