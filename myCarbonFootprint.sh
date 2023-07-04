#!/bin/bash

## ~~~ TO BE EDITED TO BE TAILORED TO THE CLUSTER ~~~
##
## You only need to edit the module loading line (l.13), make sure you are loading python 3.7 or greater.
##

# store the cwd in case we need to filter on it
userCWD="$(pwd)"

# Cd into the directory where the GA files are located
parent_path=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
cd "$parent_path"

# The only requirement for the module is to start python 3.7 or later
#module load miniconda/3

# Test if the virtualenv GA_env already exists, and if not, creates it.
if [ ! -f GA_env/bin/activate ]; then
  echo "Need to create virtualenv"
  python -m venv GA_env
  source GA_env/bin/activate
  pip3 install -r requirements.txt
else
  echo "Virtualenv: OK"
  source GA_env/bin/activate
fi

# Test if the python version is at least 3.7
version_major=$(python -c 'import sys; print(sys.version_info[0])')
version_minor=$(python -c 'import sys; print(sys.version_info[1])')
if (( $version_major < 3 )); then
  echo "The command python needs to refer to python 3"
  exit 1
fi

if (( $version_minor < 7 )); then
  echo "The command python needs to refer to python3.7 or higher."
  exit 1
fi
echo "Python versions: OK"


# Run the python code and pass on the arguments
#userCWD="/home/ll582/ with space" # DEBUGONLY
python GreenAlgorithms_global.py "$@" --userCWD "$userCWD"
