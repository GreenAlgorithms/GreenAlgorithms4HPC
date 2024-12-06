#!/bin/bash

### FILE FOR MAMBA ENVIRONMENT SET UP ON ALMA ###

source ~/.bashrc
mamba create --prefix /data/scratch/shared/RSE/envs/GA_env python=3.10 pandas numpy pyyaml jinja2 plotly 
mamba activate /data/scratch/shared/RSE/envs/GA_env
# python -c "import pandas"
# python -c "import numpy"
# python -c "import pyyaml"
# python -c "import jinja2"
# python -c "import plotly"
mamba deactivate

