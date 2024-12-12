#!/bin/bash
#SBATCH --job-name=green-alma
#SBATCH --output=green-alma.out
#SBATCH --error=green-alma.err
#SBATCH --partition=compute
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --time=01:00:00
#SBATCH --mem-per-cpu=4000

source ~/.bashrc

userCWD="$(pwd)"

# echo $userCWD

cd /data/scratch/shared/RSE/GreenAlgorithms4HPC/

mamba activate /data/scratch/shared/RSE/GreenAlgorithms4HPC/GA_env_mamba
python3 /data/scratch/shared/RSE/GreenAlgorithms4HPC/__init__.py --userCWD "$userCWD" --user "$1" --startDay "$2" --endDay "$3"
mamba deactivate