
import math
from greenalgorithms4HPC.frontend.helpers import formatText_footprint, formatText_treemonths, formatText_flying
import pandas as pd
import os


def formatText_driving(dist):
    """
    Format the text to display the driving distance
    :param dist: [float] driving distance, in km
    :return: [str] text to display
    """
    if dist < 10:
        text_driving = f"driving {dist:,.2f} km"
    else:
        text_driving = f"driving {dist:,.0f} km"
    return text_driving

def generate_terminal_view(dict_stats_all, args, cluster_info):

    user_here = dict_stats_all['user']
    dict_stats = dict_stats_all['userActivity'][user_here]
    text_nUsers = f"- user: {user_here} -"

    ## various variables
    clusterName = cluster_info['cluster_name']

    ## energy
    dcOverheads = dict_stats['energy'] - dict_stats['energy_CPUs'] - dict_stats['energy_GPUs'] - dict_stats['energy_memory']

    ## Carbon footprint
    text_footprint = formatText_footprint(dict_stats['carbonFootprint'])
    text_footprint_failedJobs = formatText_footprint(dict_stats['carbonFootprint_failedJobs'])
    text_footprint_wasted_memoryOverallocation = formatText_footprint(dict_stats['carbonFootprint']-dict_stats['carbonFootprint_memoryNeededOnly'])

    ## Context
    text_trees = formatText_treemonths(dict_stats['treeMonths'])
    text_trees_failedJobs = formatText_treemonths(dict_stats['treeMonths_failedJobs'])
    text_trees_wasted_memoryOverallocation = formatText_treemonths(dict_stats['treeMonths']-dict_stats['treeMonths_memoryNeededOnly'])
    text_driving = formatText_driving(dict_stats['driving'])
    text_flying = formatText_flying(dict_stats)

    ### Text filterCWD
    if args.filterWD is None:
        text_filterCWD = ''
    else:
        text_filterCWD = f"\n        (NB: The only jobs considered here are those launched from {args.filterWD})\n"

    ### Text filterJobIDs
    if args.filterJobIDs == 'all':
        text_filterJobIDs = ''
    else:
        text_filterJobIDs = f"\n        (NB: The only jobs considered here are those with job IDs: {args.filterJobIDs})\n"

    ### Text filter Account
    if args.filterAccount is None:
        text_filterAccount = ''
    else:
        text_filterAccount = f"\n        (NB: The only jobs considered here are those charged under {args.filterAccount})\n"

    ### To get the title length right
    title_row1 = f"Carbon footprint on {clusterName}"
    title_row2 = text_nUsers
    title_row3 = f"({args.startDay} / {args.endDay})"
    max_length = max([len(title_row1), len(title_row2), len(title_row3)])

    title_row1_full = f"#  {' '*math.floor((max_length-len(title_row1))/2)}{title_row1}{' '*math.ceil((max_length-len(title_row1))/2)}  #"
    title_row2_full = f"#  {' '*math.floor((max_length-len(title_row2))/2)}{title_row2}{' '*math.ceil((max_length-len(title_row2))/2)}  #"
    title_row3_full = f"#  {' '*math.floor((max_length-len(title_row3))/2)}{title_row3}{' '*math.ceil((max_length-len(title_row3))/2)}  #"

    title = f'''
        {'#'*(max_length+6)}
        #{' '*(max_length+4)}#
        {title_row1_full}
        {title_row2_full}
        {title_row3_full}
        #{' '*(max_length+4)}#
        {'#'*(max_length+6)}
    '''

    return f'''
      {title}
      
              {'-' * (len(text_footprint) + 6)}
             |   {text_footprint}   |
              {'-' * (len(text_footprint) + 6)}
              
    ...This is equivalent to:
         - {text_trees}
         - {text_driving}
         - {text_flying}
         
    ...{dict_stats['failure_rate']:.1%} of the jobs failed, these represent a waste of {text_footprint_failedJobs} ({text_trees_failedJobs}).
    ...On average, the jobs request at least {dict_stats['memoryOverallocationFactor']:,.1f} times the memory needed. By only requesting the memory needed, {text_footprint_wasted_memoryOverallocation} ({text_trees_wasted_memoryOverallocation}) could have been saved.
    {text_filterCWD}{text_filterJobIDs}{text_filterAccount}
    Energy used: {dict_stats['energy']:,.2f} kWh
         - CPUs: {dict_stats['energy_CPUs']:,.2f} kWh ({dict_stats['energy_CPUs'] / dict_stats['energy']:.2%})
         - GPUs: {dict_stats['energy_GPUs']:,.2f} kWh ({dict_stats['energy_GPUs'] / dict_stats['energy']:.2%})
         - Memory: {dict_stats['energy_memory']:,.2f} kWh ({dict_stats['energy_memory'] / dict_stats['energy']:.2%})
         - Data centre overheads: {dcOverheads:,.2f} kWh ({dcOverheads / dict_stats['energy']:.2%})
    Carbon intensity used for the calculations: {cluster_info['CI']:,} gCO2e/kWh
    
    Summary of usage:
    - First/last job recorded on that period: {str(dict_stats['first_job_period'].date())}/{str(dict_stats['last_job_period'].date())}
    - Number of jobs: {dict_stats['n_jobs']:,} ({dict_stats['n_success']:,} completed)
    - Core hours used/charged: {dict_stats['CPUhoursCharged']:,.1f} (CPU), {dict_stats['GPUhoursCharged']:,.1f} (GPU), {dict_stats['CPUhoursCharged']+dict_stats['GPUhoursCharged']:,.1f} (total).
    - Total usage time (i.e. when cores were performing computations):
        - CPU: {str(dict_stats['cpuTime'])} ({dict_stats['cpuTime'].total_seconds()/3600:,.0f} hours)
        - GPU: {str(dict_stats['gpuTime'])} ({dict_stats['gpuTime'].total_seconds()/3600:,.0f} hours)
    - Total wallclock time: {str(dict_stats['wallclockTime'])}
    - Total memory requested: {dict_stats['memoryRequested']:,.0f} GB
    
    Limitations to keep in mind:
         - The workload manager doesn't alway log the exact CPU usage time, and when this information is missing, we assume that all cores are used at 100%.
         - For now, we assume that for GPU jobs, the GPUs are used at 100% (as the information needed for more accurate measurement is not available)
         (this may lead to slightly overestimated carbon footprints, although the order of magnitude is likely to be correct)
         - Conversely, the wasted energy due to memory overallocation may be largely underestimated, as the information needed is not always logged.

    Any bugs, questions, suggestions? Post on GitHub (GreenAlgorithms/GreenAlgorithms4HPC) or email LL582@medschl.cam.ac.uk
    {'-' * 80}
    Calculated using the Green Algorithms framework: www.green-algorithms.org
    Please cite https://onlinelibrary.wiley.com/doi/10.1002/advs.202100707 
    '''

