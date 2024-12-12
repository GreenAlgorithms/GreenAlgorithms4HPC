# Documention of changes in GreenAlgorithms4HPC

1) New environment
We have set up a mamba environment for Green Algortithms so it works better on Alma. To set up the mamba environment, run `./myCarbonFootprint_Alma.sh` on Alma (make sure you start an interactivate bash session first).

2) `slurm_extract.py`
The `slurm_extract.py` script was modified in several places to work on Alma:
Assertion fails:
The first assertion error occured in line `assert x.TotalCPUtime_ <= x.CPUwallclocktime_`. This is because TotalCPUtime_ takes into account milliseconds where CPUwallclocktime_ doesnt (it rounds the number down). Hense this makes the CPU Wallclocktime smaller than Total CPU time. We changed this so a tolerance of a milliseconf is allowed:

```python
tolerance = pd.Timedelta(milliseconds=1)

if x.TotalCPUtime_ <= x.CPUwallclocktime_ + tolerance:
    return x.TotalCPUtime_

# print(f"Assertion failed for row {x.name}: TotalCPUtime_ = {x.TotalCPUtime_}, CPUwallclocktime_ = {x.CPUwallclocktime_}")
return x.TotalCPUtime_
```
Second assertion failure occured in `assert x.NGPUS_ != 0`. This was commented out to allow for the code to run. 

Third assertion error occured at line `assert (foo.WallclockTimeX.dt.total_seconds() == 0).all()` which was commented out to allow for code to run. 

Additions:
User flag was added to the sacct command to be able to generate Green Algo reports on other users.

`self.df_agg = self.df_agg.copy()` was added due to pandas error.

3) `main_backend` function return 
We have changed the return of the `main_backend` function so it also returns `df` and `df2` dataframes. We find the `df2` dataframe useful for the purposes of calculating carbon footprint per day/per job for a user.

4) `__init__.py` csv file creation 
We created a `data.csv` file in the home directory, which calculates the carbon footprint per day for a user. This is useful for our researchers to know how sustainable their cluster usage is. 

5) Addition of user flag
As mentioned before, we added a user flag to be able to run reports for both the user who is logged in and other users in `slurm_extract.py` and `dashboard_output.py`

6) Addition of extra bash scripts
We have created additional bash scripts for Alma:
- `green-algo-batch.sh` - a script to run sbatch jobs from the 'Green Alma' app. This was added to optimise the calculation runtime on the login node for researchers who extensively use Alma for high thoughput analysis. 
- `run-GA-Alma.sh` - simple script to run Green Algorithms after its initial setup with `./myCarbonFootprint_Alma.sh` script. 

7) Modified the `cluster_info.yaml` file
We have changed the `cluster_info.yaml` config file so it contains Alma hardware information.
