
import subprocess

import pandas as pd
from io import BytesIO
import datetime
import os
import numpy as np


class Helpers_WM():

    def __init__(self, cluster_info):
        self.cluster_info = cluster_info

    def convert_to_GB(self, memory, unit):
        """
        Converts data quantity into GB.
        :param memory: [float] quantity to convert
        :param unit: [str] unit of `memory`, has to be one of ['M', 'G', 'K']
        :return: [float] memory in GB.
        """
        assert unit in ['M', 'G', 'K']
        if unit == 'M':
            memory /= 1e3
        elif unit == 'K':
            memory /= 1e6
        return memory

    def calc_ReqMem(self, x):
        """
        Calculates the total memory required when submitting the job.
        :param x: [pd.Series] one row of sacct output.
        :return: [float] total required memory, in GB.
        """
        mem_raw, n_nodes, n_cores = x['ReqMem'], x['NNodes'], x['NCPUS']

        if pd.isnull(mem_raw):
            unit = 'G'
            memory = 0
        elif mem_raw[-1] == 'n':
            unit = mem_raw[-2]
            memory = float(mem_raw[:-2]) * n_nodes
        elif mem_raw[-1] == 'c':
            unit = mem_raw[-2]
            memory = float(mem_raw[:-2]) * n_cores
        elif mem_raw[-1] in ['M', 'G', 'K']:
            unit = mem_raw[-1]
            memory = float(mem_raw[:-1])
        else:
            raise ValueError(f"Can't parse memory value: {mem_raw}. Please raise issue on GitHub.")

        return self.convert_to_GB(memory, unit)

    def clean_RSS(self, x):
        """
        Cleans the RSS value in sacct output.
        :param x: [NaN or str] the RSS value, either NaN or of the form '2745K'
        (optionally, just a number, we then use default_unit_RSS from cluster_info.yaml as unit).
        :return: [float] RSS value, in GB.
        """
        if pd.isnull(x.MaxRSS):
            # NB if no info on MaxRSS, we assume all memory was used
            memory = -1
        elif x.MaxRSS == '0':
            memory = 0
        else:
            assert type(x.MaxRSS) == str
            # Special case for the situation where MaxRSS is of the form '154264' without a unit.
            if x.MaxRSS[-1].isalpha():
                memory = self.convert_to_GB(float(x.MaxRSS[:-1]), x.MaxRSS[-1])
            else:
                assert 'default_unit_RSS' in self.cluster_info, "Some values of MaxRSS don't have a unit. Please specify a default_unit_RSS in cluster_info.yaml"
                memory = self.convert_to_GB(float(x.MaxRSS), self.cluster_info['default_unit_RSS'])

        return memory

    def cleam_UsedMem(self, x):
        """
        Cleans the UsedMemory column
        :param x:
        :return: [float]
        """
        # NB when MaxRSS didn't store any values, we assume that "memory used = memory requested"
        return x.ReqMemX if x.UsedMem_ == -1 else x.UsedMem_

    def clean_partition(self, x):
        """
        Cleans the partition field, by replacing NaNs with empty string and selecting just one partition per job.
        :param x: [str] partition or comma-seperated list of partitions
        :return: [str] one partition or empty string
        """
        if pd.isnull(x.Partition):
            return ''

        L_partitions = x.Partition.split(',')
        if (x.WallclockTimeX.total_seconds() > 0) & (len(L_partitions) > 1):
            # Multiple partitions logged is only an issue for jobs that never started,
            # for the others, only the used partition is logged
            print(f"\n-!- WARNING: Multiple partitions logged on a job than ran: {x.JobID} - {x.Partition} (using the first one)\n")
        return L_partitions[0]

    def set_partitionType(self, x):
        assert x in self.cluster_info['partitions'], f"\n-!- Unknown partition: {x} -!-\n"
        return self.cluster_info['partitions'][x]['type']

    def parse_timedelta(self, x):
        """
        Parse a string representing a duration into a `datetime.timedelta` object.
        :param x: [str] Duration, as '[DD-HH:MM:]SS[.MS]'
        :return: [datetime.timedelta] Timedelta object
        """
        # Parse number of days
        day_split = x.split('-')
        if len(day_split) == 2:
            n_days = int(day_split[0])
            HHMMSSms = day_split[1]
        else:
            n_days = 0
            HHMMSSms = x

        # Parse ms
        ms_split = HHMMSSms.split('.')
        if len(ms_split) == 2:
            n_ms = int(ms_split[1])
            HHMMSS = ms_split[0]
        else:
            n_ms = 0
            HHMMSS = HHMMSSms

        # Parse HH,MM,SS
        last_split = HHMMSS.split(':')
        if len(last_split) == 3:
            to_add = []
        elif len(last_split) == 2:
            to_add = ['00']
        elif len(last_split) == 1:
            to_add = ['00', '00']
        else:
            raise ValueError(f"Can't parse {x}")
        n_h, n_m, n_s = list(map(int, to_add + last_split))

        return datetime.timedelta(
            days=n_days, hours=n_h, minutes=n_m, seconds=n_s, milliseconds=n_ms
        )

    def calc_realMemNeeded(self, x, granularity_memory_request):
        """
        Calculate the minimum memory needed.
        This is calculated as the smallest multiple of `granularity_memory_request` that is greater than maxRSS.
        :param x: [pd.Series] one row of sacct output.
        :param  granularity_memory_request: [float or int] level of granularity available when requesting memory on this cluster
        :return: [float] minimum memory needed, in GB.
        """
        foo = (int(x.UsedMem2_ / granularity_memory_request) + 1) * granularity_memory_request
        return foo if x.ReqMemX < x.UsedMem2_ else min(x.ReqMemX, foo)

    def calc_memory_overallocation(self, x):
        # This is in case ReqMem is wrong or too low
        return 1. if x.ReqMemX < x.NeededMemX else x.ReqMemX / x.NeededMemX

    def calc_CPUusage2use(self, x):
        if x.TotalCPUtime_.total_seconds() == 0:
            # This is when the workload manager actually didn't store real usage
            # NB: when TotalCPU=0, we assume usage factor = 100% for all CPU cores
            return x.CPUwallclocktime_

        assert x.TotalCPUtime_ <= x.CPUwallclocktime_
        return x.TotalCPUtime_

    def calc_GPUusage2use(self, x):
        if x.PartitionTypeX != 'GPU':
            return datetime.timedelta(0)
        if x.WallclockTimeX.total_seconds() > 0:
            assert x.NGPUS_ != 0
        return x.WallclockTimeX * x.NGPUS_  # NB assuming usage factor of 100% for GPUs

    def calc_coreHoursCharged(self, x):
        '''
        Split CPU and GPU core hours charged, depending on the partition.
        :param x:
        :return: [(float, float)]
        '''
        if x.PartitionTypeX == 'CPU':
            return x.CPUwallclocktime_ / np.timedelta64(1, 'h'), 0.
        else:
            return 0., x.WallclockTimeX * x.NGPUS_ / np.timedelta64(1, 'h')

    def clean_State(self, x, customSuccessStates_list):
        """
        Standardise the job's state, coding with {-1,0,1}
        :param x: [str] "State" field from sacct output
        :return: [int] in [-1,0,1]
        """
        # Codes are found here: https://slurm.schedmd.com/squeue.html#SECTION_JOB-STATE-CODES
        # self.args.customSuccessStates = 'TO,TIMEOUT'
        success_codes = ['CD', 'COMPLETED']
        running_codes = ['PD', 'PENDING', 'R', 'RUNNING', 'RQ', 'REQUEUED']
        if x in success_codes:
            codeState = 1
        elif x in customSuccessStates_list:
            # we allocate a lower value here so that when aggregating by jobID, the whole job keeps the flag
            # Otherwise a "cancelled" job could take over with StateX=0 for example
            codeState = -1
        else:
            codeState = 0

        if x in running_codes:
            # running jobs are the lowest to be removed all the time
            # (if one of the subprocess is still running, the job gets ignored regardless of --customSuccessStates
            codeState = -2

        return codeState

    def get_parent_jobID(self, x):
        """
        Get the parent job ID in case of array jobs
        :param x: [str] JobID of the form 123456789_0 (with or without '_0')
        :return: [str] Parent ID 123456789
        """
        foo = x.split('_')
        assert len(foo) <= 2, f"Can't parse the job ID: {x}"
        return foo[0]


class WorkloadManager(Helpers_WM):

    def __init__(self, args, cluster_info):
        """
        Methods related to the Workload manager
        :param args: [Namespace] input from the user
        :param cluster_info: [dict] information about this specific cluster.
        """
        super().__init__(cluster_info=cluster_info)
        self.args = args

        self.logs_df = None
        self.df_agg_0 = None
        self.df_agg = None
        self.df_agg_X = None

    def pull_logs(self):
        """
        Run the command line to pull usage from the workload manager.
        More: https://slurm.schedmd.com/sacct.html
        """
        if self.args.useCustomLogs == '':
            bash_com = [
                "sacct",
                "--starttime",
                self.args.startDay,  # format YYYY-MM-DD
                "--endtime",
                self.args.endDay,  # format YYYY-MM-DD
                "--format",
                "UID,User,JobID,JobName,Submit,Elapsed,Partition,NNodes,NCPUS,TotalCPU,CPUTime,ReqMem,MaxRSS,WorkDir,State,Account,AllocTres",
                "-P"
            ]

            # logs = subprocess.run(bash_com, capture_output=True) # this line is the new way, but doesn't work with python 3.6 or earlier. line below is the legacy way. https://stackoverflow.com/questions/4760215/running-shell-command-and-capturing-the-output
            logs = subprocess.run(bash_com, stdout=subprocess.PIPE)
            self.logs_raw = logs.stdout
        else:
            foo = "Overriding logs_raw with: "
            foundIt = False
            for sacctFileLocation in ['', 'testData', 'error_logs']:
                if not foundIt:
                    try:
                        with open(os.path.join(sacctFileLocation, self.args.useCustomLogs), 'rb') as f:
                            self.logs_raw = f.read()
                        foo += f"{sacctFileLocation}/{self.args.useCustomLogs}"
                        foundIt = True
                    except:
                        pass
            if not foundIt:
                raise FileNotFoundError(f"Couldn't find {self.args.useCustomLogs} \n "
                                        f"It should be either be in the testData/ or error_logs/ subdirectories, or the full path should be provided by --useCustomLogs.")
            print(foo)

    def convert2dataframe(self):
        """
        Convert raw logs output into a pandas dataframe.
        """
        logs_df = pd.read_csv(BytesIO(self.logs_raw), sep="|", dtype='str')
        for x in ['NNodes', 'NCPUS']:
            logs_df[x] = logs_df[x].astype('int64')

        self.logs_df = logs_df

    def clean_logs_df(self):
        """
        Clean the different fields of the usage logs.
        NB: the name of the columns ending with X need to be conserved, as they are used by the main script.
        """
        # self.logs_df_raw = self.logs_df.copy() # DEBUGONLY Save a copy of uncleaned raw for debugging mainly

        ### Calculate real memory usage
        self.logs_df['ReqMemX'] = self.logs_df.apply(self.calc_ReqMem, axis=1)

        ### Clean MaxRSS
        self.logs_df['UsedMem_'] = self.logs_df.apply(self.clean_RSS, axis=1)

        ### Parse wallclock time
        self.logs_df['WallclockTimeX'] = self.logs_df['Elapsed'].apply(self.parse_timedelta)

        ### Parse total CPU time
        # This is the total CPU used time, accross all cores.
        # But it is not reliably logged
        self.logs_df['TotalCPUtime_'] = self.logs_df['TotalCPU'].apply(self.parse_timedelta)

        ### Parse core-wallclock time
        # This is the maximum time cores could use, if used at 100% (Elapsed time * CPU count)
        if 'CPUTime' in self.logs_df.columns:
            self.logs_df['CPUwallclocktime_'] = self.logs_df['CPUTime'].apply(self.parse_timedelta)
        else:
            print('Using old logs, "CPUTime" information not available.')  # TODO: remove this after a while
            self.logs_df['CPUwallclocktime_'] = self.logs_df.WallclockTimeX * self.logs_df.NCPUS

        ### Number of GPUs
        # TODO double check that it includes multiple GPUs correctly
        if 'AllocTRES' in self.logs_df.columns:
            self.logs_df['NGPUS_'] = self.logs_df.AllocTRES.str.extract(r'((?<=gres\/gpu=)\d+)', expand=False).fillna(
                0).astype('int64')
        else:
            print('Using old logs, "AllocTRES" information not available.')  # TODO: remove this after a while
            self.logs_df['NGPUS_'] = 0

        ### Clean partition
        # Make sure it's either a partition name, or a comma-separated list of partitions
        self.logs_df['PartitionX'] = self.logs_df.apply(self.clean_partition, axis=1)

        ### Parse submit datetime
        self.logs_df['SubmitDatetimeX'] = self.logs_df.Submit.apply(
            lambda x: datetime.datetime.strptime(x, "%Y-%m-%dT%H:%M:%S"))

        ### Number of CPUs
        # e.g. here there is no cleaning necessary, so I just standardise the column name
        self.logs_df['NCPUS_'] = self.logs_df.NCPUS

        ### Number of nodes
        self.logs_df['NNodes_'] = self.logs_df.NNodes

        ### Job name
        self.logs_df['JobName_'] = self.logs_df.JobName

        ### Working directory
        self.logs_df['WorkingDir_'] = self.logs_df.WorkDir

        ### Username and UID
        self.logs_df['UIDX'] = self.logs_df.UID
        self.logs_df['UserX'] = self.logs_df.User

        ### State
        customSuccessStates_list = self.args.customSuccessStates.split(',')
        self.logs_df['StateX'] = self.logs_df.State.apply(self.clean_State,
                                                          customSuccessStates_list=customSuccessStates_list)

        ### Pull jobID
        self.logs_df['single_jobID'] = self.logs_df.JobID.apply(lambda x: x.split('.')[0])

        ### Account
        if 'Account' in self.logs_df.columns:
            self.logs_df['Account_'] = self.logs_df.Account
        else:
            print('Using old logs, "Account" information not available.')  # TODO: remove this after a while
            self.logs_df['Account_'] = ''

        ### Aggregate per jobID
        self.df_agg_0 = self.logs_df.groupby('single_jobID').agg({
            'TotalCPUtime_': 'max',
            'CPUwallclocktime_': 'max',
            'WallclockTimeX': 'max',
            'ReqMemX': 'max',
            'UsedMem_': 'max',
            'NCPUS_': 'max',
            'NGPUS_': 'max',
            'NNodes_': 'max',
            'PartitionX': lambda x: ''.join(x),
            'JobName_': 'first',
            'SubmitDatetimeX': 'min',
            'WorkingDir_': 'first',
            'StateX': 'min',
            'Account_': 'first',
            'UIDX': 'first',
            'UserX': 'first',
        })

        ### Remove jobs that are still running or currently queued
        self.df_agg = self.df_agg_0.loc[self.df_agg_0.StateX != -2]

        ### Turn StateX==-2 into 1
        self.df_agg.loc[self.df_agg.StateX == -1, 'StateX'] = 1

        ### Replace UsedMem_=-1 with memory requested (for when MaxRSS=NaN)
        self.df_agg['UsedMem2_'] = self.df_agg.apply(self.cleam_UsedMem, axis=1)

        ### Label as CPU or GPU partition
        self.df_agg['PartitionTypeX'] = self.df_agg.PartitionX.apply(self.set_partitionType)

        # Just used to clean up with old logs:
        if 'AllocTRES' not in self.logs_df.columns:
            self.df_agg.loc[self.df_agg.PartitionTypeX == 'GPU', 'NGPUS_'] = 1  # TODO remove after a while

        # Sanity check (no GPU logged for CPU partitions and vice versa)
        assert (self.df_agg.loc[self.df_agg.PartitionTypeX == 'CPU'].NGPUS_ == 0).all()
        foo = self.df_agg.loc[(self.df_agg.PartitionTypeX == 'GPU') & (self.df_agg.NGPUS_ == 0)]
        assert (foo.WallclockTimeX.dt.total_seconds() == 0).all()  # Cancelled GPU jobs won't have any GPUs allocated if they didn't start

        ## Check that there is no missing UID/User
        if self.df_agg.UIDX.isnull().sum() > 0:
            print(f"(!) WARNING: {self.df_agg.UIDX.isnull().sum()} jobs have missing UIDs")
        if self.df_agg.UserX.isnull().sum() > 0:
            print(f"(!) WARNING: {self.df_agg.UserX.isnull().sum()} jobs have missing Usernames")

        ### add the usage time to use for calculations
        self.df_agg['TotalCPUtime2useX'] = self.df_agg.apply(self.calc_CPUusage2use, axis=1)
        self.df_agg['TotalGPUtime2useX'] = self.df_agg.apply(self.calc_GPUusage2use, axis=1)

        ### Calculate core-hours charged
        self.df_agg[['CPUhoursChargedX', 'GPUhoursChargedX']] = self.df_agg.apply(self.calc_coreHoursCharged, axis=1, result_type='expand')

        ### Calculate real memory need
        self.df_agg['NeededMemX'] = self.df_agg.apply(
            self.calc_realMemNeeded,
            granularity_memory_request=self.cluster_info['granularity_memory_request'],
            axis=1)

        ### Add memory waste information
        self.df_agg['memOverallocationFactorX'] = self.df_agg.apply(self.calc_memory_overallocation, axis=1)

        # foo = self.df_agg[['TotalCPUtime_', 'CPUwallclocktime_', 'WallclockTimeX', 'NCPUS_', 'CoreHoursChargedCPUX',
        #                    'CoreHoursChargedGPUX', 'TotalCPUtime2useX', 'TotalGPUtime2useX']] # DEBUGONLY

        ### Filter on working directory
        if self.args.filterWD is not None:
            # FIXME: Doesn't work with symbolic links
            self.df_agg = self.df_agg.loc[self.df_agg.WorkingDir_ == self.args.filterWD]
            # print(f'Filtered out {len(self.df_agg)-len(self.df_agg):,} rows (filterCWD={self.args.filterWD})') # DEBUGONLY

        ### Filter on Job ID
        self.df_agg.reset_index(inplace=True)
        self.df_agg['parentJobID'] = self.df_agg.single_jobID.apply(self.get_parent_jobID)

        if self.args.filterJobIDs != 'all':
            list_jobs2keep = self.args.filterJobIDs.split(',')
            self.df_agg = self.df_agg.loc[self.df_agg.parentJobID.isin(list_jobs2keep)]

        ### Filter on Account
        if self.args.filterAccount is not None:
            self.df_agg = self.df_agg.loc[self.df_agg.Account_ == self.args.filterAccount]

        self.df_agg_X = self.df_agg[[x for x in self.df_agg.columns if x[-1] == 'X']]