#!/bin/bash

#####################        run significances for WH given a directory, in which every point corresponds to a "cards-*" directory with a combined.root file,
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

# Loop over each subdirectory in the parent directory
for dir in "$parent_dir"/cards-*/; do
    # Extract the sample name from the directory name (strip trailing slash)
    sample=$(basename "$dir")
    echo "Processing sample: $sample in directory $dir"
    
    # Enter the subdirectory
    cd "$dir" || { echo "Cannot cd into $dir, skipping..."; continue; }
    
    # Check that combined.root exists
    if [ ! -f combined.root ]; then
      echo "File combined.root not found in $dir, skipping..."
      cd - > /dev/null
      continue
    fi
    
    echo "Running combine -M Significance combined.root $extra_args"
    combine -M Significance combined.root $extra_args
    
    # Return to the parent directory (suppress directory change message)
    cd - > /dev/null
done