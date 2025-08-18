
import os
import yaml
import pandas as pd
import numpy as np

from greenalgorithms4HPC.backend.helpers import check_empty_results, simulate_mock_jobs
from greenalgorithms4HPC.backend.slurm_extract import WorkloadManager

# print("Working dir1: ", os.getcwd()) # DEBUGONLY

class GA_tools():

    def __init__(self, cluster_info, fParams):
        self.cluster_info = cluster_info
        self.fParams = fParams

    def calculate_energies(self, row):
        '''
        Calculate the energy usaged based on the job's paramaters
        :param row: [pd.Series] one row of usage statistics, corresponding to one job
        :return: [pd.Series] the same statistics with the energies added
        '''
        ### CPU and GPU
        partition_info = self.cluster_info['partitions'][row.PartitionX]
        if row.PartitionTypeX == 'CPU':
            TDP2use4CPU = partition_info['TDP']
            TDP2use4GPU = 0
        else:
            TDP2use4CPU = partition_info['TDP_CPU']
            TDP2use4GPU = partition_info['TDP']

        row['energy_CPUs'] = row.TotalCPUtime2useX.total_seconds() / 3600 * TDP2use4CPU / 1000  # in kWh

        row['energy_GPUs'] = row.TotalGPUtime2useX.total_seconds() / 3600 * TDP2use4GPU / 1000  # in kWh

        ### memory
        for suffix, memory2use in zip(['','_memoryNeededOnly'], [row.ReqMemX,row.NeededMemX]):
            row[f'energy_memory{suffix}'] = row.WallclockTimeX.total_seconds()/3600 * memory2use * self.fParams['power_memory_perGB'] /1000 # in kWh
            row[f'energy{suffix}'] = (row.energy_CPUs +  row.energy_GPUs + row[f'energy_memory{suffix}']) * self.cluster_info['PUE'] # in kWh

        return row

    def calculate_carbonFootprint(self, df, col_energy):
        return df[col_energy] * self.cluster_info['CI']


def extract_data(args, cluster_info):

    if args.use_mock_agg_data: # DEBUGONLY

        if args.reportBug | args.reportBugHere:
            print("\n(!) --reportBug and --reportBugHere are ignored when --useCustomLogs is present\n")

        # df2 = simulate_mock_jobs()
        # df2.to_pickle("testData/df_agg_X_mockMultiUsers_1.pkl")

        # foo = 'testData/df_agg_test_3.pkl'
        foo = 'testData/df_agg_X_1.pkl'
        print(f"Overriding df_agg with `{foo}`")
        return pd.read_pickle(foo)


    ### Pull usage statistics from the workload manager
    WM = WorkloadManager(args, cluster_info)
    WM.pull_logs()

    ### Log the output for debugging
    if args.reportBug | args.reportBugHere:
        if args.reportBug:
            # Create an error_logs subfolder in the output dir
            errorLogsDir = os.path.join(args.outputDir2use['path'], 'error_logs')
            os.makedirs(errorLogsDir)
            log_path = os.path.join(errorLogsDir, f'sacctOutput.csv')
        else:
            # i.e. args.reportBugHere is True
            log_path = f"{args.userCWD}/sacctOutput_{args.outputDir2use['timestamp']}.csv"

        with open(log_path, 'wb') as f:
            f.write(WM.logs_raw)
        print(f"\nSLURM statistics logged for debuging: {log_path}\n")

    ### Turn usage logs into DataFrame
    WM.convert2dataframe()
    check_empty_results(WM.logs_df, args)

    # And clean
    WM.clean_logs_df()
    # Check if there are any jobs during the period from this directory and with these jobIDs
    check_empty_results(WM.df_agg, args)

    # Check that there is only one user's data
    if len(set(WM.df_agg_X.UserX)) > 1:
        raise ValueError(f"More than one user's logs was included: {set(WM.df_agg_X.UserX)}")

    # WM.df_agg_X.to_pickle("testData/df_agg_X_1.pkl") # DEBUGONLY used to test different steps offline

    return WM.df_agg_X

def enrich_data(df, fParams, GA):

    ### energy
    df = df.apply(GA.calculate_energies, axis=1)

    df['energy_failedJobs'] = np.where(df.StateX == 0, df.energy, 0)

    ### carbon footprint
    for suffix in ['', '_memoryNeededOnly', '_failedJobs']:
        df[f'carbonFootprint{suffix}'] = GA.calculate_carbonFootprint(df, f'energy{suffix}')
        # Context metrics (part 1)
        df[f'treeMonths{suffix}'] = df[f'carbonFootprint{suffix}'] / fParams['tree_month']
        df[f'cost{suffix}'] = df[f'energy{suffix}'] * fParams['electricity_cost'] # TODO use realtime electricity costs

    ### Context metrics (part 2)
    df['driving'] = df.carbonFootprint / fParams['passengerCar_EU_perkm']
    df['flying_NY_SF'] = df.carbonFootprint / fParams['flight_NY_SF']
    df['flying_PAR_LON'] = df.carbonFootprint / fParams['flight_PAR_LON']
    df['flying_NYC_MEL'] = df.carbonFootprint / fParams['flight_NYC_MEL']

    return df

def summarise_data(df, args):
    agg_functions_from_raw = {
        'n_jobs': ('UserX', 'count'),
        'first_job_period': ('SubmitDatetimeX', 'min'),
        'last_job_period': ('SubmitDatetimeX', 'max'),
        'energy': ('energy', 'sum'),
        'energy_CPUs': ('energy_CPUs', 'sum'),
        'energy_GPUs': ('energy_GPUs', 'sum'),
        'energy_memory': ('energy_memory', 'sum'),
        'carbonFootprint': ('carbonFootprint', 'sum'),
        'carbonFootprint_memoryNeededOnly': ('carbonFootprint_memoryNeededOnly', 'sum'),
        'carbonFootprint_failedJobs': ('carbonFootprint_failedJobs', 'sum'),
        'cpuTime': ('TotalCPUtime2useX', 'sum'),
        'gpuTime': ('TotalGPUtime2useX', 'sum'),
        'wallclockTime': ('WallclockTimeX', 'sum'),
        'CPUhoursCharged': ('CPUhoursChargedX', 'sum'),
        'GPUhoursCharged': ('GPUhoursChargedX', 'sum'),
        'memoryRequested': ('ReqMemX', 'sum'),
        'memoryOverallocationFactor': ('memOverallocationFactorX', 'mean'),
        'n_success': ('StateX', 'sum'),
        'treeMonths': ('treeMonths', 'sum'),
        'treeMonths_memoryNeededOnly': ('treeMonths_memoryNeededOnly', 'sum'),
        'treeMonths_failedJobs': ('treeMonths_failedJobs', 'sum'),
        'driving': ('driving', 'sum'),
        'flying_NY_SF': ('flying_NY_SF', 'sum'),
        'flying_PAR_LON': ('flying_PAR_LON', 'sum'),
        'flying_NYC_MEL': ('flying_NYC_MEL', 'sum'),
        'cost': ('cost', 'sum'),
        'cost_failedJobs': ('cost_failedJobs', 'sum'),
        'cost_memoryNeededOnly': ('cost_memoryNeededOnly', 'sum'),
    }

    # This is to aggregate already aggregated dataset (so names are a bit different)
    agg_functions_further = agg_functions_from_raw.copy()
    agg_functions_further['n_jobs'] = ('n_jobs', 'sum')
    agg_functions_further['first_job_period'] = ('first_job_period', 'min')
    agg_functions_further['last_job_period'] = ('last_job_period', 'max')
    agg_functions_further['cpuTime'] = ('cpuTime', 'sum')
    agg_functions_further['gpuTime'] = ('gpuTime', 'sum')
    agg_functions_further['wallclockTime'] = ('wallclockTime', 'sum')
    agg_functions_further['CPUhoursCharged'] = ('CPUhoursCharged', 'sum')
    agg_functions_further['GPUhoursCharged'] = ('GPUhoursCharged', 'sum')
    agg_functions_further['memoryRequested'] = ('memoryRequested', 'sum')
    agg_functions_further['memoryOverallocationFactor'] = ('memoryOverallocationFactor', 'mean') # NB: not strictly correct to do a mean of mean, but ok
    agg_functions_further['n_success'] = ('n_success', 'sum')

    def agg_jobs(data, agg_names=None):
        """

        :param data:
        :param agg_names: if None, then the whole dataset is aggregated
        :return:
        """
        agg_names2 = agg_names if agg_names else lambda _:True
        if 'UserX' in data.columns:
            timeseries = data.groupby(agg_names2).agg(**agg_functions_from_raw)
        else:
            timeseries = data.groupby(agg_names2).agg(**agg_functions_further)

        timeseries.reset_index(inplace=True, drop=(agg_names is None))
        timeseries['success_rate'] = timeseries.n_success / timeseries.n_jobs
        timeseries['failure_rate'] = 1 - timeseries.success_rate
        timeseries['share_carbonFootprint'] = timeseries.carbonFootprint / timeseries.carbonFootprint.sum()

        return timeseries

    df['SubmitDate'] = df.SubmitDatetimeX.dt.date  # TODO do it with real start time rather than submit day

    df_userdaily = agg_jobs(df, ['SubmitDate'])
    df_overallStats = agg_jobs(df_userdaily)
    dict_overallStats = df_overallStats.iloc[0, :].to_dict()
    userID = df.UserX[0]

    output = {
        "userDaily": df_userdaily,
        'userActivity': {userID: dict_overallStats},
        "user": userID
    }

    # Some job-level statistics to plot distributions
    memoryOverallocationFactors = df.groupby('UserX')['memOverallocationFactorX'].apply(list).to_dict()
    memoryOverallocationFactors['overall'] = df.memOverallocationFactorX.to_numpy()
    output['memoryOverallocationFactors'] = memoryOverallocationFactors

    return output


def main_backend(args):
    '''

    :param args:
    :return:
    '''
    ### Load cluster specific info
    with open(os.path.join(args.path_infrastucture_info, 'cluster_info.yaml'), "r") as stream:
        try:
            cluster_info = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

    ### Load fixed parameters
    with open(os.path.join(args.path_infrastucture_info,"fixed_parameters.yaml"), "r") as stream:
        try:
            fParams = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

    GA = GA_tools(cluster_info, fParams)

    df = extract_data(args, cluster_info=cluster_info)
    df2 = enrich_data(df, fParams=fParams, GA=GA)
    summary_stats = summarise_data(df2, args=args)

    return summary_stats

if __name__ == "__main__":

    #### This is used for testing only ####

    from collections import namedtuple
    argStruct = namedtuple('argStruct',
                           'startDay endDay use_mock_agg_data useCustomLogs customSuccessStates filterWD filterJobIDs filterAccount reportBug reportBugHere path_infrastucture_info')
    args = argStruct(
        startDay='2022-01-01',
        endDay='2023-06-30',
        useCustomLogs=None,
        use_mock_agg_data=True,
        customSuccessStates='',
        filterWD=None,
        filterJobIDs='all',
        filterAccount=None,
        reportBug=False,
        reportBugHere=False,
        path_infrastucture_info="clustersData/CSD3",
    )

    main_backend(args)



