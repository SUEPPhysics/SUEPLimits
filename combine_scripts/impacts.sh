#!/bin/bash

# Initialize variables for optional parameters
output=""
extra_args=""

# Function to display usage
usage() {
  echo "Usage: $0 <path> [-o <output>] [-e <extra_args>]"
  echo
  echo "Run the impacts tool for a given card-containing directory."
  echo
  echo "Options:"
  echo "  <path>            Required. The directory path to operate in, where combined.root lives."
  echo "  -o <output>       Optional. Specify the output path."
  echo "  -e <extra_args>   Optional. Extra arguments for combineTool.py."
  exit 1
}

# Check if at least one argument (the path) is provided
if [ "$#" -lt 1 ]; then
  usage
fi

# Capture the required path argument
path=$1
shift

# Parse optional flags
while getopts ":o:e:" opt; do
  case ${opt} in
    o )
      output=$OPTARG
      ;;
    e )
      extra_args=$OPTARG
      ;;
    \? )
      echo "Invalid option: -$OPTARG" >&2
      usage
      ;;
    : )
      echo "Option -$OPTARG requires an argument." >&2
      usage
      ;;
  esac
done

# Move to the specified directory
cd "$path" || { echo "Error: Could not navigate to directory '$path'"; exit 1; }

# activate environment
export VO_CMS_SW_DIR=/cvmfs/cms.cern.ch
source $VO_CMS_SW_DIR/cmsset_default.sh
cmsenv

# Run main commands with optional extra arguments
combineTool.py -M Impacts -d combined.root -m 125 --doInitialFit --robustFit 1 $extra_args
combineTool.py -M Impacts -d combined.root -m 125 --robustFit 1 --doFits $extra_args
combineTool.py -M Impacts -d combined.root -m 125 -o impacts.json $extra_args
plotImpacts.py -i impacts.json -o impacts

# Copy impacts.json to the output path if specified
if [ -n "$output" ] && [ -f impacts.pdf ]; then
  echo "Copying impacts.pdf to: "$output""
  cp impacts.pdf "$output"
fi
