
## ~~~ TO NOT EDIT ~~~
##
## This script is common to all clusters.
##

import os
import argparse
import yaml
import datetime
import math
import sys
import pandas as pd
import pathlib

from GreenAlgorithms_workloadManager import WorkloadManager


class validity_checks():
    '''
    This class is used to check the validity of the various arguments and objects.
    '''

    def validate_dates(self, args):
        '''
        Validate that `startDay` and `endDay` are in the right format and in the right order.
        :param args: Namespace with the command line arguments submitted by the user.
        '''
        self.startDay = args.startDay
        self.endDay = args.endDay

        for x in [args.startDay, args.endDay]:
            try:
                datetime.datetime.strptime(x, '%Y-%m-%d')
            except ValueError:
                raise ValueError(f"Incorrect date format, should be YYYY-MM-DD but is: {x}")

        foo = datetime.datetime.strptime(args.startDay, '%Y-%m-%d')
        bar = datetime.datetime.strptime(args.endDay, '%Y-%m-%d')
        assert foo <= bar, f"Start date ({args.startDay}) is after the end date ({args.endDay})."

    def check_empty_results(self, df, filterWD=None, filterJobIDs='all', filterAccount=None):
        '''
        This is to check whether any jobs have been run on the period, and stop the script if not.
        :param df: [pd.DataFrame] Usage logs
        :param filterWD: [None or str, default=None] Whether the results are filtered based on working directory.
        :param filterJobIDs: [str] 'all' or comma-seperated list of job IDs
        '''
        if len(df) == 0:
            if filterWD is not None:
                addThat = f' from this directory ({filterWD})'
            else:
                addThat = ''
            if filterJobIDs != 'all':
                addThat += ' and with these jobIDs'
            if filterAccount is not None:
                addThat += ' charged under this account'

            print(f'''

        You haven't run any jobs on that period (from {self.startDay} to {self.endDay}){addThat}.

            ''')
            sys.exit()


class Helpers_GA():

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

    def formatText_footprint(self, footprint_g):
        '''
        Format the text to display the carbon footprint
        :param footprint_g: [float] carbon footprint, in gCO2e
        :return: [str] the text to display
        '''
        if footprint_g < 1e3:
            text_footprint = f"{footprint_g:,.0f} gCO2e"
        elif footprint_g < 1e6:
            text_footprint = f"{footprint_g / 1e3:,.0f} kgCO2e"
        else:
            text_footprint = f"{footprint_g / 1e3:,.0f} TCO2e"
        return text_footprint

    def formatText_treemonths(self, tm_float):
        '''
        Format the text to display the tree months
        :param tm_float: [float] tree-months
        :return: [str] the text to display
        '''
        tm = int(tm_float)
        ty = int(tm / 12)
        if tm < 1:
            text_trees = f"{tm_float:.3f} tree-months"
        elif tm == 1:
            text_trees = f"{tm_float:.1f} tree-month"
        elif tm < 6:
            text_trees = f"{tm_float:.1f} tree-months"
        elif tm <= 24:
            text_trees = f"{tm} tree-months"
        elif tm < 120:
            text_trees = f"{ty} tree-years and {tm - ty * 12} tree-months"
        else:
            text_trees = f"{ty} tree-years"
        return text_trees

    def formatText_driving(self,dist):
        '''
        Format the text to display the driving distance
        :param dist: [float] driving distance, in km
        :return: [str] text to display
        '''
        if dist < 10:
            text_driving = f"driving {dist:,.2f} km"
        else:
            text_driving = f"driving {dist:,.0f} km"
        return text_driving

    def formatText_flying(self, footprint_g, fParams):
        '''
        Format the text to display about flying
        :param footprint_g: [float] carbon footprint, in gCO2e
        :param fParams: [dict] Fixed parameters, from fixed_parameters.yaml
        :return: [str] text to display
        '''
        if footprint_g < 0.5 * fParams['flight_NY_SF']:
            text_flying = f"{footprint_g / fParams['flight_PAR_LON']:,.2f} flights between Paris and London"
        elif footprint_g < 0.5 * fParams['flight_NYC_MEL']:
            text_flying = f"{footprint_g / fParams['flight_NY_SF']:,.2f} flights between New York and San Francisco"
        else:
            text_flying = f"{footprint_g / fParams['flight_NYC_MEL']:,.2f} flights between New York and Melbourne"
        return text_flying

class unitTests():
    def __init__(self, df):
        self.df = df

    def coreHoursPerMonth(self, years):
        print(f'\n### Core-hours charged per month (CPU / GPU (Total)) ###\n')
        today = datetime.date.today()
        for year in range(years[0], min(years[1], today.year)+1):
            print(year)
            if year == today.year:
                max_month = today.month
            else:
                max_month = 12
            for month in range(1,max_month+1):
                df_month = self.df.loc[(self.df.SubmitDatetimeX.dt.month == month)&(self.df.SubmitDatetimeX.dt.year == year)]
                month_name = datetime.date(year,month,1).strftime("%b")
                CPU_ch = df_month.loc[df_month.PartitionTypeX == 'CPU'].CoreHoursChargedX.sum()
                GPU_ch = df_month.loc[df_month.PartitionTypeX == 'GPU'].CoreHoursChargedX.sum()
                print(f'\t- {month_name}: {CPU_ch:,.2f}/{GPU_ch:,.2f} ({CPU_ch+GPU_ch:,.2f})')

class GreenAlgorithms(Helpers_GA):

    def __init__(self, df, args, cluster_info, fParams):
        self.df = df
        self.args = args
        self.cluster_info = cluster_info
        self.fParams = fParams

    def calculate_footprint(self):
        '''
        Calculate the carbon footprint of each job
        '''
        ### Calculate energies
        self.df = self.df.apply(self.calculate_energies, axis = 1)

        ### Calculate footprints
        for suffix in ['', '_memoryNeededOnly']:
            self.df[f'carbonFootprint{suffix}'] = self.df[f'energy{suffix}'] * self.cluster_info['CI']

    def generate_report(self):
        '''
        Generate the report to display in the command line
        '''
        # Footprint
        footprint_g = self.df.carbonFootprint.sum()
        text_footprint = self.formatText_footprint(footprint_g)

        footprint_realVmem = self.df.carbonFootprint.sum() - self.df.carbonFootprint_memoryNeededOnly.sum()
        text_footprint_memoryNeededOnly = self.formatText_footprint(footprint_realVmem)

        # Failed jobs
        assert set(self.df.StateX) <= {0,1}
        df_failedJobs = self.df.loc[self.df.StateX == 0]
        footprint_g_failed = df_failedJobs.carbonFootprint.sum()
        text_footprint_failed = self.formatText_footprint(footprint_g_failed)

        # Equivalence tree months
        tm_float = footprint_g / self.fParams['tree_month']
        text_trees = self.formatText_treemonths(tm_float)

        # Context driving
        driving_EU = footprint_g / self.fParams['passengerCar_EU_perkm']
        text_driving = self.formatText_driving(driving_EU)

        # Context flying
        text_flying = self.formatText_flying(footprint_g, self.fParams)

        ### Text filterCWD
        if self.args.filterWD is None:
            text_filterCWD = ''
        else:
            text_filterCWD = f"\n        (NB: The only jobs considered here are those launched from {self.args.filterWD})\n"

        ### Text filterJobIDs
        if self.args.filterJobIDs == 'all':
            text_filterJobIDs = ''
        else:
            text_filterJobIDs = f"\n        (NB: The only jobs considered here are those with job IDs: {self.args.filterJobIDs})\n"

        ### Text filter Account
        if self.args.filterAccount is None:
            text_filterAccount = ''
        else:
            text_filterAccount = f"\n        (NB: The only jobs considered here are those charged under {self.args.filterAccount})\n"

        ### Calculate core-hours charged
        CPU_ch = self.df.loc[self.df.PartitionTypeX == 'CPU'].CoreHoursChargedX.sum()
        GPU_ch = self.df.loc[self.df.PartitionTypeX == 'GPU'].CoreHoursChargedX.sum()

        ### about cluster name
        clusterName = cluster_info['cluster_name']

        ### Energy overheads
        totalEnergy = self.df.energy.sum()
        dcOverheads = totalEnergy - self.df.energy_CPUs.sum() - self.df.energy_GPUs.sum() - self.df.energy_memory.sum()

        self.report = f'''
          ############################{'#'*len(clusterName)}###
          #                           {' '*len(clusterName)}  #
          #  Your carbon footprint on {clusterName}  #
          #  {' '*(math.floor(len(clusterName)/2))}({self.args.startDay} / {self.args.endDay}){' '*(math.ceil(len(clusterName)/2))}  #
          #                           {' '*len(clusterName)}  #
          ############################{'#'*len(clusterName)}###

                  {'-' * (len(text_footprint) + 6)}
                 |   {text_footprint}   |
                  {'-' * (len(text_footprint) + 6)}

        ...This is equivalent to:
             - {text_trees}
             - {text_driving}
             - {text_flying}

        ...{len(df_failedJobs)/len(self.df):.1%} of your jobs failed, which represents a waste of {text_footprint_failed} ({footprint_g_failed / self.fParams['tree_month']:,.2f} tree-months).
        ...On average, you request at least {self.df.memOverallocationFactorX.mean():.1f} times the memory you need. By only requesting the memory you needed, you could have saved {text_footprint_memoryNeededOnly} ({footprint_realVmem / self.fParams['tree_month']:,.2f} tree-months).
        {text_filterCWD}{text_filterJobIDs}{text_filterAccount}
        Energy used: {totalEnergy:,.2f} kWh
             - CPUs: {self.df.energy_CPUs.sum():,.2f} kWh ({round(self.df.energy_CPUs.sum() / totalEnergy, 2):.0%})
             - GPUs: {self.df.energy_GPUs.sum():,.2f} kWh ({round(self.df.energy_GPUs.sum() / totalEnergy, 2):.0%})
             - Memory: {self.df.energy_memory.sum():,.2f} kWh ({round(self.df.energy_memory.sum() / totalEnergy, 2):.0%})
             - Data centre overheads: {dcOverheads:,.2f} kWh ({round(dcOverheads / totalEnergy, 2):.0%})
        Carbon intensity used for the calculations: {self.cluster_info['CI']} gCO2e/kWh

        Summary of your usage: 
             - First/last job recorded on that period: {str(self.df.SubmitDatetimeX.min().date())}/{str(self.df.SubmitDatetimeX.max().date())}
             - Number of jobs: {len(self.df):,} ({len(self.df.loc[self.df.StateX == 1]):,} completed)
             - Core hours used/charged: {CPU_ch:,.1f} (CPU), {GPU_ch:,.1f} (GPU), {CPU_ch+GPU_ch:,.1f} (total).
             - Total usage time (i.e. when cores were performing computations):
                - CPU: {str(self.df.TotalCPUtime2useX.sum())}
                - GPU: {str(self.df.TotalGPUtime2useX.sum())}
             - Total wallclock time: {str(self.df.WallclockTimeX.sum())}
             - Total memory requested: {self.df.ReqMemX.sum():,.0f} GB
        
        Limitations to keep in mind:
             - The workload manager doesn't alway log the exact CPU usage time, and when this information is missing, we assume that all cores are used at 100%.
             - For now, we assume that GPU jobs only use 1 GPU and the GPU is used at 100% (as the information needed for more accurate measurement is not available)
             (both of these may lead to slightly overestimated carbon footprints, although the order of magnitude is likely to be correct)
             - Conversely, the wasted energy due to memory overallocation may be largely underestimated, as the information needed is not always logged.

        Any bugs, questions, suggestions? Email LL582@medschl.cam.ac.uk
        {'-' * 80}
        Calculated using the Green Algorithms framework: www.green-algorithms.org
        Please cite https://onlinelibrary.wiley.com/doi/10.1002/advs.202100707 
        '''

def main(args, cluster_info, fParams):
    '''
    The main steps of what we're doing here
    :param args: [Namespace] command line arguments from the user
    :param cluster_info: [dict] info about the cluster, from cluster_info.yaml
    :param fParams: [dict] Fixed parameters, from fixed_parameters.yaml
    '''
    ### Check input
    validator = validity_checks()
    validator.validate_dates(args)

    ### Pull usage statistics from the workload manager
    WM = WorkloadManager(args, cluster_info)
    WM.pull_logs()

    ### Log the output for debugging
    scripts_dir = os.path.dirname(os.path.realpath(__file__))
    if args.reportBug | args.reportBugHere:
        log_name = str(datetime.datetime.now().timestamp()).replace(".", "_")

        if args.reportBug:
            log_path = os.path.join(scripts_dir, 'error_logs', f'sacctOutput_{log_name}.csv')
            # Logging into a seperate dir to write-protect the main one (not in place for now)
            # log_path = os.path.join(pathlib.Path(scripts_dir).parent.absolute(), 'GreenAlgorithms4HPC_errorLogs', f'sacctOutput_{log_name}.csv')
        elif args.reportBugHere:
            log_path = f'{args.userCWD}/sacctOutput_{log_name}.csv'

        os.makedirs(os.path.dirname(log_path), exist_ok=True) # Create error_logs dir if needed
        with open(log_path, 'wb') as f:
            f.write(WM.logs_raw)
        print(f"\nSLURM statistics logged for debuging: {log_path}\n")

    ### Turn usage logs into DataFrame
    WM.convert2dataframe()
    # Save an example of the WM output
    # WM.logs_df.iloc[1:3, :].to_csv('example_files/example_sacctOutput_raw_asDF.tsv', sep='\t', index=False)

    # Check if there are any jobs during the period
    validator.check_empty_results(WM.logs_df)

    ### Clean the usage logs
    WM.clean_logs_df()
    # Save an example of the WM output
    # WM.df_agg.iloc[1:3, :].to_csv('example_files/example_output_workloadManager.tsv', sep='\t')

    # Check if there are any jobs during the period from this directory and with these jobIDs
    validator.check_empty_results(WM.df_agg, filterWD=args.filterWD, filterJobIDs=args.filterJobIDs, filterAccount=args.filterAccount)

    ### Calculate energy usage and footprints
    GA = GreenAlgorithms(df=WM.df_agg, args=args, cluster_info=cluster_info, fParams=fParams)
    GA.calculate_footprint()
    GA.generate_report()
    print(GA.report)

    if args.runTests != '':
        tester = unitTests(WM.df_agg)
        if args.runTests == 'coreHoursPerMonth':
            tester.coreHoursPerMonth(years=(2019,2022))



if __name__ == "__main__":
    # TODO: add unit tests that can run automatically
    ### Load cluster specific info
    with open("cluster_info.yaml", "r") as stream:
        try:
            cluster_info = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

    ### Load fixed parameters
    with open("fixed_parameters.yaml", "r") as stream:
        try:
            fParams = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

    ### Create argument parser
    parser = argparse.ArgumentParser(description=f'Calculate your carbon footprint on {cluster_info["cluster_name"]}.')

    default_endDay = datetime.date.today().strftime("%Y-%m-%d")  # today
    default_startDay = f"{datetime.date.today().year}-01-01" # start of the year

    parser.add_argument('-S', '--startDay', type=str,
                        help=f'The first day to take into account, as YYYY-MM-DD (default: {default_startDay})',
                        default=default_startDay)
    parser.add_argument('-E', '--endDay', type=str,
                        help='The last day to take into account, as YYYY-MM-DD (default: today)',
                        default=default_endDay)
    parser.add_argument('--filterCWD', action='store_true',
                        help='Only report on jobs launched from the current location.')
    parser.add_argument('--userCWD', type=str, help=argparse.SUPPRESS)
    parser.add_argument('--filterJobIDs', type=str,
                        help='Comma seperated list of Job IDs you want to filter on.',
                        default='all')
    parser.add_argument('--filterAccount', type=str,
                        help='Only consider jobs charged under this account')
    parser.add_argument('--reportBug', action='store_true', help='In case of a bug, this flag logs jobs informations so that we can fix it. \
        Note that this will write out some basic information about your jobs, such as runtime, number of cores and memory usage.')
    parser.add_argument('--reportBugHere', action='store_true',
                        help='Similar to --reportBug, but exports the output to your home folder')
    parser.add_argument('--useCustomLogs', type=str, default='',
                        help='This bypasses the workload manager, and enables you to input a custom log file of your jobs. \
                             This is mostly meant for debugging, but can be useful in some situations. '
                             'An example of the expected file can be found at `example_files/example_sacctOutput_raw.txt`.')
    # Arguments for debugging
    parser.add_argument('--useOtherClusterInfo', type=str, default='', help=argparse.SUPPRESS)
    parser.add_argument('--runTests', type=str, default='', help=argparse.SUPPRESS)

    args = parser.parse_args()

    # For debuging, load custom cluster info
    if args.useOtherClusterInfo != '':
        print(f"Overriding cluster_info with: {args.useOtherClusterInfo}")
        with open(os.path.join('clustersData', args.useOtherClusterInfo), "r") as stream:
            try:
                cluster_info = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)

    ### Set the WD to filter on, if needed
    if args.filterCWD:
        args.filterWD = args.userCWD
        print("\nNB: --filterCWD doesn't work with symbolic links (yet!)\n")
    else:
        args.filterWD = None

    ### Run main
    main(args, cluster_info, fParams)

