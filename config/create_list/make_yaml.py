import os
names = os.listdir("/uscms/home/mreid/nobackup/sueps/analysis/SUEPs/scouting/plotter/combineHist")
print(names)
def gettemp2(temp):
  temp2 = temp.replace("p",".")
  temp3 = temp.split("p")[1]
  add_0 = 3- len(temp3)
  temp2 = temp2+"0"*add_0
  return temp2
for name in names:
   if "QCD" in name or "Data" in name:
    continue
   print("\n")
   form = name.split('_')
#sig1000_T8p00_phi8.000_2018.root
   print("GluGluToSUEP_HT400_%s_mS%s.000_mPhi%s_T%s_modegeneric:"%(form[1],form[0][3:],form[2][3:],gettemp2(form[1][1:])))
   print("  files:")
   print("    - ~/nobackup/sueps/analysis/SUEPs/scouting/plotter/combineHist/{}".format(name))
   print("  type:")
   print("    signal")
