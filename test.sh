#!/bin/bash

## ~~~ TO BE EDITED TO BE TAILORED TO THE CLUSTER ~~~
##
## You only need to edit the module loading line (l.13), make sure you are loading python 3.7 or greater.
##

# Cd into the directory where the GA files are located
parent_path=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
cd "$parent_path"

# The only requirement for the module is to start python 3.7 or later
module load miniconda/3

# Test if the python version is at least 3.7
version_major=$(python3 -c 'import sys; print(sys.version_info[0])')
version_minor=$(python3 -c 'import sys; print(sys.version_info[1])')
if (( $version_major < 3 )); then
  echo "The command python3 needs to refer to python 3"
  exit 1
fi

if (( $version_minor < 7 )); then
  echo "The command python3 needs to refer to python3.7 or higher."
  exit 1
fi

echo "Python versions: OK"

# Test if the virtualenv GA_env already exists, and if not, creates it.
if [ ! -f GA_env/bin/activate ]; then
  echo "Need to create virtualenv"
  python3 -m venv GA_env
  source GA_env/bin/activate
  pip3 install -r requirements.txt
else
  echo "Virtualenv OK"
  source GA_env/bin/activate
fi

# Check that python3 starts the correct version
python3 GreenAlgorithms_global.py "$@"





if [ ! -f GA_env/bin/activate ]; then echo "no"; else echo "yes"; fi