#!/bin/bash

### FILE FOR MAMBA ENVIRONMENT SET UP ON ALMA ###

source ~/.bashrc
mamba create --prefix /data/rds/DIT/SCICOM/SCRSE/shared/conda/GA_env python=3.10 pandas numpy pyyaml jinja2 plotly 
mamba activate /data/rds/DIT/SCICOM/SCRSE/shared/conda/GA_env
mamba deactivate

