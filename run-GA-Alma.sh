#!/bin/bash

source ~/.bashrc

userCWD="$(pwd)"

cd /data/scratch/shared/RSE/GreenAlgorithms4HPC/

mamba activate /data/scratch/shared/RSE/envs/GA_env
python3 /data/scratch/shared/RSE/GreenAlgorithms4HPC/__init__.py "$@" --userCWD "$userCWD"
mamba deactivate