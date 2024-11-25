#!/bin/bash

### FILE FOR MAMBA ENVIRONMENT SET UP ON ALMA ###

source ~/.bashrc

mamba create --prefix /data/scratch/shared/RSE/GreenAlgorithms4HPC/GA_env_mamba python=3.10 -y
mamba activate mamba activate /data/scratch/shared/RSE/GreenAlgorithms4HPC/GA_env_mamba
pip3 install -r requirements.txt
mamba deactivate
echo "Mamba env: OK"

