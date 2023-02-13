import os
import glob
import multiprocessing
from multiprocessing.pool import ThreadPool
import subprocess
import shlex

combine_options = " --rMin=0, --cminFallbackAlgo Minuit2,Migrad,0:0.05  --X-rtd MINIMIZER_analytic --X-rtd FAST_VERTICAL_MORPH"

dcards = glob.glob("cards-*")


def call_combine(cmd):
    p = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    return (out, err)

pool = ThreadPool(multiprocessing.cpu_count())
results = []

for dc in dcards:
    print(" -- making :", dc)
    name= dc.replace("cards-", "")
    if "SUEP" not in name:
        continue
    print(" --- name : ", name)
    os.system("rm -rf cards-{}/combined.dat".format(name))
    os.system(
            "combineCards.py -S "
            #"catcrA2016=cards-{name}/shapes-cat_crA2016.dat "
            #"catcrB2016=cards-{name}/shapes-cat_crB2016.dat "
            #"catcrC2016=cards-{name}/shapes-cat_crC2016.dat "
            #"catcrD2016=cards-{name}/shapes-cat_crD2016.dat "
            #"catcrE2016=cards-{name}/shapes-cat_crE2016.dat "
            #"catcrF2016=cards-{name}/shapes-cat_crF2016.dat "
            #"catcrG2016=cards-{name}/shapes-cat_crG2016.dat "
            #"catcrH2016=cards-{name}/shapes-cat_crH2016.dat "
            #"catSig2016=cards-{name}/shapes-catSig2016.dat "
            #"catcrA2017=cards-{name}/shapes-cat_crA2017.dat "
            #"catcrB2017=cards-{name}/shapes-cat_crB2017.dat "
            #"catcrC2017=cards-{name}/shapes-cat_crC2017.dat "
            #"catcrD2017=cards-{name}/shapes-cat_crD2017.dat "
            #"catcrE2017=cards-{name}/shapes-cat_crE2017.dat "
            #"catcrF2017=cards-{name}/shapes-cat_crF2017.dat "
            #"catcrG2017=cards-{name}/shapes-cat_crG2017.dat "
            #"catcrH2017=cards-{name}/shapes-cat_crH2017.dat "
            #"catSig2017=cards-{name}/shapes-catSig2017.dat "
            "catcrA2018=cards-{name}/shapes-cat_crA2018.dat "
            "catcrB2018=cards-{name}/shapes-cat_crB2018.dat "
            "catcrC2018=cards-{name}/shapes-cat_crC2018.dat "
            "catcrD2018=cards-{name}/shapes-cat_crD2018.dat "
            "catcrE2018=cards-{name}/shapes-cat_crE2018.dat "
            "catcrF2018=cards-{name}/shapes-cat_crF2018.dat "
            "catcrG2018=cards-{name}/shapes-cat_crG2018.dat "
            "catcrH2018=cards-{name}/shapes-cat_crH2018.dat "
            "catSig2018=cards-{name}/shapes-catSig2018.dat "
            "> cards-{name}/combined.dat".format(name=name))
    os.system("text2workspace.py -m 125 cards-{name}/combined.dat -o cards-{name}/combined.root".format(name=name))
    command = (
        "combine "
        " -M AsymptoticLimits --datacard cards-{name}/combined.root"
        #" -M FitDiagnostics -datacard cards-{name}/combined.root --plots signalPdfNames='ADD*,Signal' --backgroundPdfNames='*DY*,*WW*,*TOP*,ZZ*,WZ*,VVV'"
        " -m 125 --cl 0.95 --name {name} {options}"
        ##" --rMin=0 --cminFallbackAlgo Minuit2,Migrad,0:0.05"
        " --X-rtd MINIMIZER_analytic --X-rtd FAST_VERTICAL_MORPH".format(
            name=name,
            options="" #"--rMax=10" if "ADD" in name else "--rMax=10"
        )
    )
    results.append(pool.apply_async(call_combine, (command,)))

pool.close()
pool.join()

for result in results:
    out, err = result.get()
    if "error" in str(err).lower():
        print(str(err))
        print(" ----------------- ")
        print()
