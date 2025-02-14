import os

WH = {}
ZH = {}

def checkIfEqual(t1, t2):
    precision = 2e-2
    # This is to deal with different precision levels when tagging the models
    if abs(t1[0] - t2[0])*t1[0] > precision: return False
    if abs(t1[1] - t2[1])*t1[1] > precision: return False
    if t2[2] != t1[2]: return False
    return True

for card in os.listdir("WH"):
    # Parse model
    if not ("card" in card): continue
    c, mS, mP, T, mode = card.split("_")
    mS = float(mS.replace("mS",""))
    mP = float(mP.replace("mPhi",""))
    T  = float(T.replace("T",""))
    mode = mode.replace("mode","")
    if not((mP, T, mode) in WH):
        file = "WH/"+ card + "/combined.dat"
        if not os.path.exists(file):
            print("Missing file for card:", file)
        WH[(mP, T, mode)] = file
    else:
        print("Repeated card for WH at tag:", (mP, T, mode))

for card in os.listdir("ZH"):
    # Parse model
    if not("card" in card): continue
    s, mode, mP, T = card.split("_")
    mP = float(mP.replace("mD",""))
    T  = float(T.replace("T","").replace(".txt",""))
    if not((mP, T, mode) in ZH):
        file = "ZH/"+ card + "/" + card.replace("cards-", "") + ".txt"
        if not os.path.exists(file):
            print("Missing file for card:", file)
        ZH[(mP, T, mode)] = file
    else:
        print("Repeated card for ZH at tag:", (mP, T, mode))

comms = []
# First check if there are matches ZH->WH
for tagZ in ZH:

    found = False
    matchW = None
    for tagW in WH:
        if checkIfEqual(tagZ, tagW):
            if matchW:
                print("Repeated match for Z in W:", tagZ, tagW, matchW) 
            else:
                matchW = tagW
    if matchW:
        print("Found match for Z in W:", tagZ, tagW, matchW)
        out_dir = "cards-combinedWZ_mD%1.3f_T%1.3f_mode%s/"%(tagZ[0], tagZ[1], tagZ[2])
        out_file = out_dir +"combinedWZ_mD%1.3f_T%1.3f_mode%s.dat"%(tagZ[0], tagZ[1], tagZ[2])
        if os.path.exists(out_file):
            print("File already exists:", out_file)
            continue
        if not os.path.exists(out_dir):
            os.mkdir(out_dir)
        comms.append(["combineCards.py %s %s > %s"%(ZH[tagZ], WH[matchW], out_file),out_file])
    else:
        print("Missing W card for Z card %s"%(ZH[tagZ]))

print(comms, len(comms))
for c in comms:
    print(c)
    os.system(c[0])
    os.system("echo 'nuisance edit rename * * CMS_EXO24030_tracking CMS_tracking' >> %s"%c[1])
    os.system("echo 'nuisance edit rename * * CMS_EXO23003_tracking CMS_tracking' >> %s"%c[1])
    in1 = open("%s"%c[1], "r")
    out1 = open("tmp.txt", "w")

    for l in in1.readlines():
        if ("shapes" in l) and ("WH" in l):
            toR = l.split(" ")
            toROut = ""
            for w in toR:
                if not("card" in w):
                    toROut += w
                else:
                    toROut += w.split("/")[0] + "/" +"/".join(w.split("/")[2:])
                toROut += " "
            out1.write(toROut)
        else:
            out1.write(l)
    os.system("mv %s %s"%("tmp.txt","%s"%c[1]))

# # #os.system("cp -r WH ZH Combined")
