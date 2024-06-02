#!/bin/zsh

# Directory to be emptied
OUTPUT_DIR="output_clips"

# Check if the directory exists
if [[ -d "$OUTPUT_DIR" ]]; then
    # Remove all files in the directory
    rm -rf "${OUTPUT_DIR:?}"/*
    echo "The $OUTPUT_DIR folder has been emptied."
else
    echo "Directory $OUTPUT_DIR does not exist."
fi
