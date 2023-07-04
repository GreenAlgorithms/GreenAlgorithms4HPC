# Green Algorithms for High Performance Computing

⚠️ We are still trialing the system, please get in touch with any bugs you find!

The aim of this code is to implement the Green Algorithms framework (more [here](https://arxiv.org/abs/2007.07610) and on [www.green-algorithms.org](www.green-algorithms.org)) directly on HPC clusters.

**How does it work?** First, it pulls usage statistics from the workload manager's logs and then it estimate the carbon footprint based on this usage.

## How to use it

Now, anyone with access to `the_shared_directory` can run the calculator, 
by running the same command, with various options available:

```
usage: myCarbonFootprint.sh      [-h] [-S STARTDAY] [-E ENDDAY] [--filterCWD]
                                 [--filterJobIDs FILTERJOBIDS]
                                 [--filterAccount FILTERACCOUNT] [--reportBug]
                                 [--reportBugHere]
                                 [--useCustomLogs USECUSTOMLOGS]

Calculate your carbon footprint on CSD3.

optional arguments:
  -h, --help            show this help message and exit
  -S STARTDAY, --startDay STARTDAY
                        The first day to take into account, as YYYY-MM-DD
                        (default: 20XX-01-01 i.e. 01/01 of current year)
  -E ENDDAY, --endDay ENDDAY
                        The last day to take into account, as YYYY-MM-DD
                        (default: today)
  --filterCWD           Only report on jobs launched from the current
                        location.
  --filterJobIDs FILTERJOBIDS
                        Comma seperated list of Job IDs you want to filter on.
  --filterAccount FILTERACCOUNT
                        Only consider jobs charged under this account
  --customSuccessStates CUSTOMSUCCESSSTATES
                        Comma-separated list of job states. By default, only
                        jobs that exit with status CD or COMPLETED are
                        considered succesful (PENDING, RUNNING and REQUEUD are
                        ignored). Jobs with states listed here will be
                        considered successful as well (best to list both
                        2-letter and full-length codes. Full list of job
                        states:
                        https://slurm.schedmd.com/squeue.html#SECTION_JOB-
                        STATE-CODES
  --reportBug           In case of a bug, this flag logs jobs informations so
                        that we can fix it. Note that this will write out some
                        basic information about your jobs, such as runtime,
                        number of cores and memory usage.
  --reportBugHere       Similar to --reportBug, but exports the output to your
                        home folder
  --useCustomLogs USECUSTOMLOGS
                        This bypasses the workload manager, and enables you to
                        input a custom log file of your jobs. This is mostly
                        meant for debugging, but can be useful in some
                        situations. An example of the expected file can be
                        found at `example_files/example_sacctOutput_raw.tsv`.
```

### Limitations to keep in mind

 - The workload manager doesn't alway log the exact CPU usage time, and when this information is missing, we assume that all cores are used at 100%.
 - For now, we assume that GPU jobs only use 1 GPU and the GPU is used at 100% (as the information needed for more accurate measurement is not available)
 (both of these may lead to slightly overestimated carbon footprints, although the order of magnitude is likely to be correct)
 - Conversely, the wasted energy due to memory overallocation may be largely underestimated, as the information needed is not always logged.


### Requirements
- Python 3.7 *(can probably be adjusted to older versions of python fairly easily)*

## How to install it

(Only needs to be installed once on a cluster, check first that someone else hasn't installed it yet!)

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
**You just need to make sure that you create a variable `self.df_agg` similar to the example file [here](example_files/example_output_workloadManager.tsv).
Only the columns with a name ending in X are needed.**

6. Edit `cluster_info.yaml` to plug in the values corresponding to the hardware specs of your cluster. You can find a lot of useful values on the Green Algorithms GitHub: https://github.com/GreenAlgorithms/green-algorithms-tool/tree/master/data

7. Run the script a first time. It will check that the correct version of python is used 
and will create the virtualenv with the required packages, based on `requirements.txt`:
```shell script
the_shared_directory/GreenAlgorithms4HPC/myCarbonFootprint.sh
```

## Debugging
There are some example of intermediary files in [example_files/](example_files/).

For the workload manager part of the code:
- [The raw output](example_files/example_sacctOutput_raw.txt) ([here](example_files/example_sacctOutput_raw_asDF.tsv) as a table) from the `sacct` SLURM command (this is the command pulling all the logs from SLURM), i.e. `WM.logs_raw`, the output of `WM.pull_logs()`.
- [The cleaned output of the workload manager step](example_files/example_output_workloadManager.tsv), i.e. `WM.df_agg`, the output of `WM.clean_logs_df()`. Only the columns with a name ending with X are needed (the other ones are being used by the workload manager script). NB: the `pd.DataFrame` has been converted to a csv to be included here.

## How to update the code:
_More elegant solutions welcome! [Discussion here](https://github.com/Llannelongue/GreenAlgorithms4HPC/issues/1)._

⚠️ Make sure you have saved your custom version of `cluster_info.yaml` and the module loading step of `GreenAlgorithms_global.py`.

- `git reset --hard` To remove local changes to files (hence the need for a backup!)
- `git pull`
- Update `cluster_info.yaml` and `GreenAlgorithms_global.py` with the details needed for your cluster.
- `chmod +x myCarbonFootprint.sh` to make it executable again
- Test `myCarbonFootprint.sh` 
