#!/bin/bash

cd $1

combine -M FitDiagnostics combined.root -m 200 --rMin -1 --saveShapes --saveWithUncertainties $2
