# Green Algorithms for High Performance Computing

This code can be used to easily implement the Green Algorithms calculator on a cluster. 

More info about the method: [preprint on arXiv](https://arxiv.org/abs/2007.07610) 
and [www.green-algorithms.org](www.green-algorithms.org)

### Requirements
- Python 3.7 

## How to install it

1. Clone this repository in a shared directory on your cluster:
    ```bash
    cd the_shared_directory 
    git clone https://github.com/Llannelongue/GreenAlgorithms4HPC.git
    ```

2. Edit `myCarbonFootprint.sh` to load the module enabling `python3 ...` to load Python 3.7 or greater.

3. Make the bash script executable: 
    ```bash
    chmod +x the_shared_directory/GreenAlgorithms4HPC/myCarbonFootprint.sh
    ```

4. Edit `GreenAlgorithms_workloadManager.py` to tailor it to your workload manager. 
For now, the default code is based on SLURM.

5. Edit `cluster_info.yaml` to plug in the values corresponding to the hardware specs of your cluster.

6. Run the script a first time. It will check that the correct version of python is used 
and will create the virtualenv with the required packages, based on `requirements.txt`:
```shell script
the_shared_directory/GreenAlgorithms4HPC/myCarbonFootprint.sh
```

## How to use it

Now, anyone with access to `the_shared_directory` can run the calculator, 
by running the same command, with various options available:
```
usage: myCarbonFootprint.sh [-h] [-S STARTDAY] [-E ENDDAY] [--filterCWD]
                                 [--reportBug] [--reportBugHere]

Calculate your carbon footprint on YOUR_CLUSTER.

optional arguments:
  -h, --help            show this help message and exit
  -S STARTDAY, --startDay STARTDAY
                        The first day to take into account, as YYYY-MM-DD
                        (default: 2021-01-01)
  -E ENDDAY, --endDay ENDDAY
                        The last day to take into account, as YYYY-MM-DD
                        (default: today)
  --filterCWD           Only report on jobs launched from the current
                        location.
  --reportBug           In case of a bug, this flag logs jobs informations so
                        that we can fix it. Note that this will write out some
                        basic information about your jobs, such as runtime,
                        number of cores and memory usage.
  --reportBugHere       Similar to --reportBug, but exports the output to your
                        home folder
```
