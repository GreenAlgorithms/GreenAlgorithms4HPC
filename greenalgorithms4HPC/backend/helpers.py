
import datetime
import sys
import random
import pandas as pd
import numpy as np

def check_empty_results(df, args):
    """
    This is to check whether any jobs have been run on the period, and stop the script if not.
    :param df: [pd.DataFrame] Usage logs
    :param args:
    """
    if len(df) == 0:
        if args.filterWD is not None:
            addThat = f' from this directory ({args.filterWD})'
        else:
            addThat = ''
        if args.filterJobIDs != 'all':
            addThat += ' and with these jobIDs'
        if args.filterAccount is not None:
            addThat += ' charged under this account'

        print(f'''

    You haven't run any jobs on that period (from {args.startDay} to {args.endDay}){addThat}.

        ''')
        sys.exit()

def simulate_mock_jobs(): # DEBUGONLY
    df_list = []
    n_jobs = random.randint(500,800)
    foo = {
        'WallclockTimeX':[datetime.timedelta(minutes=random.randint(50,700)) for _ in range(n_jobs)],
        'ReqMemX':np.random.randint(4,130, size=n_jobs)*1.,
        'PartitionX':['icelake']*n_jobs,
        'SubmitDatetimeX':[datetime.datetime(day=1,month=5,year=2023) + datetime.timedelta(days=random.randint(1,60)) for _ in range(n_jobs)],
        'StateX':np.random.choice([1,0], p=[.8,.2], size=n_jobs),
        'UIDX':['11111']*n_jobs,
        'UserX':['foo']*n_jobs,
        'PartitionTypeX':['CPU']*n_jobs,
        'TotalCPUtime2useX':[datetime.timedelta(minutes=random.randint(50,5000)) for _ in range(n_jobs)],
        'TotalGPUtime2useX':[datetime.timedelta(seconds=0)]*n_jobs,
    }

    foo_df = pd.DataFrame(foo)
    foo_df['CPUhoursChargedX'] = foo_df.TotalCPUtime2useX / np.timedelta64(1, 'h')
    foo_df['GPUhoursChargedX'] = 0.
    foo_df['NeededMemX'] = foo_df.ReqMemX * np.random.random(n_jobs)
    foo_df['memOverallocationFactorX'] = foo_df.ReqMemX / foo_df.NeededMemX

    df_list.append(foo_df)
    return pd.concat(df_list)