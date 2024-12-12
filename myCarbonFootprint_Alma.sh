#!/bin/bash

### FILE FOR MAMBA ENVIRONMENT SET UP ON ALMA ###

source ~/.bashrc
mamba create --prefix /data/scratch/shared/RSE/envs/GA_env python=3.10 pandas numpy pyyaml jinja2 plotly 
mamba activate /data/scratch/shared/RSE/envs/GA_env
mamba deactivate

