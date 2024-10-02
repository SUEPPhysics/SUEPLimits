cd $1

combineTool.py -M Impacts -d combined.root -m 125 --doInitialFit --robustFit 1 $2
combineTool.py -M Impacts -d combined.root -m 125 --robustFit 1 --doFits $2
combineTool.py -M Impacts -d combined.root -m 125 --o impacts.json $2
plotImpacts.py -i impacts.json -o impacts
