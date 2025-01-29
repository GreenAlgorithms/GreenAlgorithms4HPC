
import argparse
import datetime
import os
import pandas as pd

from backend import main_backend
from frontend import main_frontend
from additional_stats import *  

def create_arguments():
    """
    Command line arguments for the tool.
    :return: argparse object
    """
    parser = argparse.ArgumentParser(description=f'Calculate your carbon footprint on the server.')

    default_endDay = datetime.date.today().strftime("%Y-%m-%d")  # today
    default_startDay = f"{datetime.date.today().year}-01-01"  # start of the year

    ## Timeframe
    parser.add_argument('-S', '--startDay', type=str,
                        help=f'The first day to take into account, as YYYY-MM-DD (default: {default_startDay})',
                        default=default_startDay)
    parser.add_argument('-E', '--endDay', type=str,
                        help='The last day to take into account, as YYYY-MM-DD (default: today)',
                        default=default_endDay)

    ## How to display the report
    parser.add_argument('-o', '--output', type=str,
                        help="How to display the results, one of 'terminal' or 'html' (default: terminal)",
                        default='terminal')
    parser.add_argument('--outputDir', type=str,
                        help="Export path for the output (default: under `output/`). Only used with `--output html`.",
                        default='outputs')

    ## Filter out jobs
    parser.add_argument('--filterCWD', action='store_true',
                        help='Only report on jobs launched from the current location.')
    parser.add_argument('--userCWD', type=str, help=argparse.SUPPRESS)
    parser.add_argument('--filterJobIDs', type=str,
                        help='Comma separated list of Job IDs you want to filter on. (default: "all")',
                        default='all')
    parser.add_argument('--filterAccount', type=str,
                        help='Only consider jobs charged under this account')
    parser.add_argument('--user', type=str,
                        help='Acccount of interest')
    parser.add_argument('--customSuccessStates', type=str, default='',
                        help="Comma-separated list of job states. By default, only jobs that exit with status CD or \
                                 COMPLETED are considered successful (PENDING, RUNNING and REQUEUD are ignored). \
                                 Jobs with states listed here will be considered successful as well (best to list both \
                                 2-letter and full-length codes. Full list of job states: \
                                 https://slurm.schedmd.com/squeue.html#SECTION_JOB-STATE-CODES")

    ## Reporting bugs
    group1 = parser.add_mutually_exclusive_group()
    group1.add_argument('--reportBug', action='store_true',
                        help='In case of a bug, this flag exports the jobs logs so that you/we can investigate further. '
                             'The debug file will be stored in the shared folder where this tool is located (under /outputs), '
                             'to export it to your home folder, user `--reportBugHere`. '
                             'Note that this will write out some basic information about your jobs, such as runtime, '
                             'number of cores and memory usage.'
                        )
    group1.add_argument('--reportBugHere', action='store_true',
                        help='Similar to --reportBug, but exports the output to your home folder.')
    group2 = parser.add_mutually_exclusive_group()
    group2.add_argument('--useCustomLogs', type=str, default='',
                        help='This bypasses the workload manager, and enables you to input a custom log file of your jobs. \
                                 This is mostly meant for debugging, but can be useful in some situations. '
                             'An example of the expected file can be found at `example_files/example_sacctOutput_raw.txt`.')
    # Arguments for debugging only (not visible to users)
    # To ue arbitrary folder for the infrastructure information
    parser.add_argument('--useOtherInfrastuctureInfo', type=str, default='', help=argparse.SUPPRESS)
    # Uses mock aggregated usage data, for offline debugging
    group2.add_argument('--use_mock_agg_data', action='store_true', help=argparse.SUPPRESS)

    args = parser.parse_args()
    return args

class validate_args():
    """
    Class used to validate all the arguments provided.
    """
    # TODO add validation
    # TODO test these

    def _validate_dates(self, args):
        """
        Validates that `startDay` and `endDay` are in the right format and in the right order.
        """
        for x in [args.startDay, args.endDay]:
            try:
                datetime.datetime.strptime(x, '%Y-%m-%d')
            except ValueError:
                raise ValueError(f"Incorrect date format, should be YYYY-MM-DD but is: {x}")

        foo = datetime.datetime.strptime(args.startDay, '%Y-%m-%d')
        bar = datetime.datetime.strptime(args.endDay, '%Y-%m-%d')
        if foo > bar:
            raise ValueError(f"Start date ({args.startDay}) is after the end date ({args.endDay}).")

    def _validate_output(self, args):
        """
        Validates that --output is one of the accepted options.
        """
        list_options = ['terminal', 'html']
        if args.output not in list_options:
            raise ValueError(f"output argument invalid. Is {args.output} but should be one of {list_options}")


    def all(self, args):
        self._validate_dates(args)
        self._validate_output(args)

if __name__ == "__main__":
    # print("Working dir0: ", os.getcwd()) # DEBUGONLY

    args = create_arguments()

    ## Decide which infrastructure info to use
    if args.useOtherInfrastuctureInfo != '':
        args.path_infrastucture_info = args.useOtherInfrastuctureInfo
        print(f"Overriding infrastructure info with: {args.path_infrastucture_info}")
    else:
        args.path_infrastucture_info = 'data'

    ## Organise the unique output directory (used for output report and logs export for debugging)
    ## creating a uniquely named subdirectory in whatever
    # Decide if an output directory is needed at all
    if (args.output in ['html']) | args.reportBug | args.reportBugHere:
        timestamp = datetime.datetime.now().strftime('%Y%m%d-%H%M-%S%f')
        args.outputDir2use = {
            'timestamp': timestamp,
            'path': os.path.join(args.outputDir, f"outputs_{timestamp}")
        }

        # Create directory
        os.makedirs(args.outputDir2use["path"])

    else:
        # no output is created
        args.outputDir2use = None

    ### Set the WD to filter on, if needed
    if args.filterCWD:
        args.filterWD = args.userCWD
        print("\nNB: --filterCWD doesn't work with symbolic links (yet!)\n")
    else:
        args.filterWD = None

    ### Validate input
    validate_args().all(args)

    ### Run backend to get data
    df, df2, extracted_data = main_backend(args)

    main_frontend(extracted_data, args)

    # print(df.columns)
    # print(df2.columns)

    df2['SubmitDate'] = df2['SubmitDatetimeX'].dt.date

    df2['TotalCPU (hours)'] = df2.apply(calc_used_CPU_hours, axis=1)
    df2['CPUtime (hours)'] = df2.apply(calc_allocated_CPU_hours, axis=1)
    df2['Efficientcy (TotalCPU / CPUtime hours)'] = df2.apply(calc_efficiency, axis=1)
    df2['Cost (Pounds)'] = df2.apply(calc_cost, axis=1)

    df2.to_csv(f"{args.userCWD}/{args.user}_all_data.csv", index=False)

    common_groupby = {
    'UserX': 'first',
    'carbonFootprint': 'sum',
    'carbonFootprint_failedJobs': 'sum',
    'cost_failedJobs': 'sum',
    'Cost (Pounds)': 'sum',
    'Efficientcy (TotalCPU / CPUtime hours)': 'mean'
}

    groupby_dict = common_groupby.copy()

    groupby_dict2 = {
        **common_groupby,
        'AllocTRES': 'first',
        'PartitionX': 'first'
    }

    result_submitdate = df2.groupby('SubmitDate').agg(groupby_dict).reset_index()
    # print("result_submitdate", result_submitdate)
    result_submitdate.to_csv(f"{args.userCWD}/{args.user}_submitdate_data.csv", index=False)

    result_jobname = df2.groupby('JobName').agg(groupby_dict2).reset_index()
    # print("result_jobname", result_jobname)
    result_jobname.to_csv(f"{args.userCWD}/{args.user}_jobname_data.csv", index=False)