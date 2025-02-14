#!/bin/bash

# Loop over all files that match the pattern
for file in cards/combined/ZH/SUEP_*_mD*_T*.*; do
    # Use sed to extract the unique identifier (mD, T, and mode parts) from the filename.
    # This regex captures "combinedWZ_mD{value1}_T{value2}_mode{value3}" and ignores the extension.
    base=$(echo "$file" | sed -E 's/(SUEP_[^.]+_mD[^_]+_T[^_]+)\..*/\1/')

    # extra sanitize: remove .root, .input, .txt
    base=$(echo "$base" | sed -E 's/\.root//')
    base=$(echo "$base" | sed -E 's/\.input//')
    base=$(echo "$base" | sed -E 's/\.txt//')

    # Define the folder name 
    folder="${base}"

    # Replace "Combined/" with "Combined/cards-"
    folder=$(echo "$folder" | sed 's|ZH/|ZH/cards-|')
    
    # Create the folder if it doesn't already exist
    if [ ! -d "$folder" ]; then
        mkdir -p "$folder"
    fi
    
    # Move the file into the appropriate folder
    mv "$file" "$folder"/
done
