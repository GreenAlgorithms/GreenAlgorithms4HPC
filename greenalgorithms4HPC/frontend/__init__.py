
import yaml
import os

from greenalgorithms4HPC.frontend.terminal_output import generate_terminal_view
from greenalgorithms4HPC.frontend.dashboard_output import dashboard_html

def main_frontend(dict_stats, args):
    ### Load cluster specific info
    with open(os.path.join(args.path_infrastucture_info, 'cluster_info.yaml'), "r") as stream:
        try:
            cluster_info = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

    if args.output == 'terminal':
        print("Generating terminal view... ", end="")
        terminal_view = generate_terminal_view(dict_stats, args, cluster_info)
        print("Done\n")
        print(terminal_view)
    elif args.output == 'html':
        print("Generating html... ", end="")
        dashboard = dashboard_html(
            dict_stats=dict_stats,
            args=args,
            cluster_info=cluster_info,
        )
        report_path = dashboard.generate()
        print(f"done: {report_path}")

    else:
        raise ValueError("Wrong output format")


if __name__ == "__main__":

    #### This is used for testing only ####

    from collections import namedtuple
    from backend import main_backend

    argStruct = namedtuple('argStruct',
                           'startDay endDay use_mock_agg_data user output useCustomLogs customSuccessStates filterWD filterJobIDs filterAccount reportBug reportBugHere path_infrastucture_info')
    args = argStruct(
        startDay='2022-01-01',
        endDay='2023-06-30',
        use_mock_agg_data=True,
        user='ll582',
        output='html',
        useCustomLogs=None,
        customSuccessStates='',
        filterWD=None,
        filterJobIDs='all',
        filterAccount=None,
        reportBug=False,
        reportBugHere=False,
        path_infrastucture_info="clustersData/CSD3",
    )
    with open(os.path.join(args.path_infrastucture_info, 'cluster_info.yaml'), "r") as stream:
        try:
            cluster_info = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

    extracted_data = main_backend(args)

    # generate_dashboard_html(dict_stats=extracted_data, args=args, cluster_info=cluster_info, dict_deptGroupsUsers=dict_deptGroupsUsers, dict_users=dict_users)

    main_frontend(dict_stats=extracted_data,args=args)