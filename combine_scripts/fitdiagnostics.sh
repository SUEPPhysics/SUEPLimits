#!/bin/bash

# Initialize variables for optional parameters
extra_args=""

# Function to display usage
usage() {
  echo "Usage: $0 <path> [-e <extra_args>]"
  echo
  echo "Run the impacts tool for a given card-containing directory."
  echo
  echo "Options:"
  echo "  <datacard>            Required. The datacard.root."
  echo "  -e <extra_args>   Optional. Extra arguments for combine."
  exit 1
}

# Check if at least one argument (the datacard) is provided
if [ "$#" -lt 1 ]; then
  usage
fi

# Capture the required datacard argument
datacard=$1
shift

# Parse optional flags
while getopts "e:" opt; do
  case ${opt} in
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

# activate environment
echo "Activating environment."
export VO_CMS_SW_DIR=/cvmfs/cms.cern.ch
source $VO_CMS_SW_DIR/cmsset_default.sh
cmsenv

# Move to the specified directory
path=$(dirname $datacard)
card=$(basename $datacard)
echo "Navigating to directory $path."
cd $path

# Run main commands
echo "Running combine."
echo "combine -M FitDiagnostics $card -m 200 --saveShapes --saveWithUncertainties $extra_args"
combine -M FitDiagnostics $card -m 200 --saveShapes --saveWithUncertainties $extra_args
