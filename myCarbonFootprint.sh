#!/bin/bash

# Cd into the directory where the GA files are located
parent_path=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
cd "$parent_path"

# The only requirement is to start python 3.7 or later
module load miniconda/3
# This loads the necessary packages from the virtualenv
source GA_env/bin/activate
# Check that python3 starts the correct version
python3 GreenAlgorithms_global.py "$@"
