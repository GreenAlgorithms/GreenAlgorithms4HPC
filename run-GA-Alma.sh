#!/bin/bash

source ~/.bashrc

userCWD="$(pwd)"

cd /data/rds/DIT/SCICOM/SCRSE/shared/apps/GreenAlgorithms4HPC/

mamba activate /data/rds/DIT/SCICOM/SCRSE/shared/conda/GA_env
python3 /data/rds/DIT/SCICOM/SCRSE/shared/apps/GreenAlgorithms4HPC/__init__.py "$@" --userCWD "$userCWD"
mamba deactivate