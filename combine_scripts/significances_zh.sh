#!/bin/bash

#####################        run significances for ZH given a directory, in which every point corresponds to a file like SUEP_generic_mD8.0_T5.66.txt.root  (or just the .txt file on which you can first run text2workspace.py)
#####################        and save the output in that directory to be grabbed by significance_vh/wh.ipynb

# Function to display usage
usage() {
  echo "Usage: $0 <directory> [-e <extra_args>]"
  echo
  echo "Run combine for every .root datacard in the specified directory."
  echo
  echo "Options:"
  echo "  <directory>         Required. Directory containing .root datacard files."
  echo "  -e <extra_args>     Optional. Extra arguments for combineTool.py."
  exit 1
}

# Check if at least one argument (the directory) is provided
if [ "$#" -lt 1 ]; then
  usage
fi

# Capture the required directory argument
parent_dir=$1
datacard_dir=$1
shift

# Parse optional flags
extra_args=""
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

# Activate the CMS environment
echo "Activating environment."
export VO_CMS_SW_DIR=/cvmfs/cms.cern.ch
source $VO_CMS_SW_DIR/cmsset_default.sh
cmsenv


# Loop over all .root files in the given directory
for datacard in "$datacard_dir"/*.txt.root; do
  # Check if the glob finds any file
  if [ ! -f "$datacard" ]; then
    echo "No .root files found in $datacard_dir"
    exit 1
  fi

  echo "Processing file: $datacard"
  path=$(dirname "$datacard")
  card_name=$(basename "$datacard")
  
  # Move to the directory containing the datacard
  echo "Navigating to directory $path."
  cd "$path"

  # Run text2workspace if .root cards not available
  #echo "Running text2workspace: text2workspace.py $card_name -o $card_name.root"
  #text2workspace.py "$card_name" -o "$card_name.root"

  # Run combine command
  echo "Running combine: combine -M Significance $card_name --name ${card_name%.txt.root} $extra_args"
  combine -M Significance "$card_name" --name "${card_name%.txt.root}" $extra_args
  
  # cd - > /dev/null
done