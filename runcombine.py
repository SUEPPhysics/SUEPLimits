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
            #"catCR12016=cards-{name}/shapes-catCR12016.dat "
            #"catCR22016=cards-{name}/shapes-catCR22016.dat "
            #"catCR32016=cards-{name}/shapes-catCR32016.dat "
            #"catSig2016=cards-{name}/shapes-catSig2016.dat "
            #"catCR12017=cards-{name}/shapes-catCR12017.dat "
            #"catCR22017=cards-{name}/shapes-catCR22017.dat "
            #"catCR32017=cards-{name}/shapes-catCR32017.dat "
            #"catSig2017=cards-{name}/shapes-catSig2017.dat "
            #"catCR12018=cards-{name}/shapes-catCR12018.dat "
            #"catCR22018=cards-{name}/shapes-catCR22018.dat "
            #"catCR32018=cards-{name}/shapes-catCR32018.dat "
            "catSig2018=cards-{name}/shapes-catSig2018.dat "
            "> cards-{name}/combined.dat".format(name=name))
    os.system("text2workspace.py -m 125 cards-{name}/combined.dat -o cards-{name}/combined.root".format(name=name))
    command = (
        "combine "
        " -M AsymptoticLimits --datacard cards-{name}/combined.root"
        #" -M FitDiagnostics -datacard cards-{name}/combined.root --plots signalPdfNames='ADD*,Signal' --backgroundPdfNames='*DY*,*WW*,*TOP*,ZZ*,WZ*,VVV'"
        " -m 125 --cl 0.9 --name {name} {options}"
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
