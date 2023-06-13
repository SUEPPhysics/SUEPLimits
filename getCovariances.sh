#!/bin/bash
#Usage: sh getCovariances.sh [DATACARD NAME] [What to use as data: d (data), t0 (background only Asimov), t1 (s+b Asimov)]  [OUTPUT shortname] [EXTRA INPUT]

DATACARD=$1
ASIMOV=$2
OUTPUT=$3
EXTRA=$4
HERE="$PWD/"

if [ "$DATACARD" = "" ]; then
   echo "You need to provide a datacard!!"
   exit
fi

if [ "$ASIMOV" = "" ]; then
   echo "Defaulting to data. Are you sure this is what you want to do?"
   ASIMOV=""
   PREFIX="d"
fi

if [ "$ASIMOV" = "d" ]; then
   echo "Using data"
   ASIMOV=""
   PREFIX="d"
fi

if [ "$ASIMOV" = "t0" ]; then
   echo "Using background-only Asimov dataset"
   ASIMOV=" -t -1 --expectSignal 0 --rMin -10"
   PREFIX="t0"
fi

if [ "$ASIMOV" = "t1" ]; then
   echo "Using signal + background Asimov dataset"
   ASIMOV=" -t -1 --expectSignal 1 "
   PREFIX="t1"
fi

if [ "$OUTPUT" = "" ]; then
   OUTPUT="./"   
fi

if [[ "$DATACARD" != *"root"* ]]; then
   echo "Preliminary: convert to rootspace"
   echo "---------------------------------"
   text2workspace.py $HERE/${DATACARD}
   DATACARD="${DATACARD//.txt/.root}"
   echo "Card is $DATACARD"
fi


cd $OUTPUT


echo "---------------------------------"
echo "---------------------------------"

combine -M FitDiagnostics $ASIMOV $HERE/$DATACARD $EXTRA --forceRecreateNLL  --saveWithUncertainties --saveOverallShapes --numToysForShapes 200 --plots

mv fitDiagnostics.root fitDiagnostics_$PREFIX.root
mv higgsCombineTest.FitDiagnostics.mH120.root higgsCombineTest.FitDiagnostics.mH120_$PREFIX.root
mv covariance_fit_b.png covariance_fit_b_$PREFIX.png
mv covariance_fit_s.png covariance_fit_s_$PREFIX.png
mkdir ./$PREFIX_dists/
mv *fit_s.png ./$PREFIX_dists/
mv *fit_b.png ./$PREFIX_dists/
cp $HERE/$DATACARD ./
cd $HERE

