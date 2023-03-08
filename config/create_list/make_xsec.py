with open('2018_eff.txt') as f:
    names = f.readlines()

print("{")

for name in names:
   dataset = name.split(',')[0]
   eff = name.split(',')[1]
   if "mS125" in dataset:
       xsec = 45.2
   elif "mS200" in dataset:
       xsec = 16.9
   elif "mS300" in dataset:
       xsec = 6.59
   elif "mS400" in dataset:
       xsec = 3.16
   elif "mS500" in dataset:
       xsec = 1.71
   elif "mS600" in dataset:
       xsec = 1.00
   elif "mS700" in dataset:
       xsec = 0.621
   elif "mS800" in dataset:
       xsec = 0.402
   elif "mS900" in dataset:
       xsec = 0.269
   elif "mS1000" in dataset:
       xsec = 0.185
   else:
       break
   print('  "{}"'.format(dataset)+': {')
   print('    "br": 1,')
   print('    "kr": {},'.format(eff))
   print('    "xsec": {}'.format(xsec))
   print('  },')
print('}')
