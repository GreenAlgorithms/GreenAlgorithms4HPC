import os
import shutil
from jinja2 import Environment, FileSystemLoader
# from jinja2 import select_autoescape, DebugUndefined, StrictUndefined, Undefined
import datetime
from pprint import pprint
import pandas as pd
import numpy as np
import plotly.express as px

from greenalgorithms4HPC.frontend.helpers import formatText_footprint, formatText_treemonths, formatText_flying

# class SilentUndefined(Undefined): # DEBUGONLY
#     def _fail_with_undefined_error(self, *args, **kwargs):
#         return '!MISSING!'

def formatText_timedelta_short(dt):
    dt_sec = dt.total_seconds()
    hour = 3600
    day = 24*hour
    year = 365*day
    if dt_sec >= year:
        return f"{dt_sec / year:.1f} year{'' if int(dt_sec/year)==1 else 's'}"
    elif dt_sec > 2*day:
        return f"{dt_sec / day:.1f} days"
    elif dt_sec >= hour:
        return f"{dt_sec / hour:.1f} hour{'' if int(dt_sec/hour)==1 else 's'}"
    else:
        return f"{dt_sec:.2f} seconds"

def formatText_cost(cost, cluster_info):
    return f"{cluster_info['energy_cost']['currency']}{cost:,.0f}"

def get_summary_texts(dict_in, cluster_info):
    output = {
        'cpuTime': formatText_timedelta_short(dict_in['cpuTime']),
        'gpuTime': formatText_timedelta_short(dict_in['gpuTime']),
        'carbonFootprint': formatText_footprint(dict_in['carbonFootprint'], use_html=True),
        'carbonFootprint_failedJobs': formatText_footprint(dict_in['carbonFootprint_failedJobs'], use_html=True),
        'carbonFootprint_failedJobs_share': f"{dict_in['carbonFootprint_failedJobs']/dict_in['carbonFootprint']:.2%}",
        'carbonFootprint_wasted_memoryOverallocation': formatText_footprint(dict_in['carbonFootprint']-dict_in['carbonFootprint_memoryNeededOnly'], use_html=True),
        'share_carbonFootprint': f"{dict_in['share_carbonFootprint']:.2%}",
        'trees': formatText_treemonths(dict_in['treeMonths'], splitMonthsYear=False),
        'flying': formatText_flying(dict_in, output_format='dict'),
        'cost': formatText_cost(dict_in['cost'], cluster_info=cluster_info),
        'cost_failedJobs': formatText_cost(dict_in['cost_failedJobs'], cluster_info=cluster_info),
        'cost_wasted_memoryOverallocation': formatText_cost(dict_in['cost']-dict_in['cost_memoryNeededOnly'], cluster_info=cluster_info),
        'n_jobs': f"{dict_in['n_jobs']:,}"
    }

    for key in dict_in:
        if key not in output:
            # print(f"adding {key}")
            output[key] = dict_in[key]

    return output

class dashboard_html:
    def __init__(self, dict_stats, args, cluster_info):
        self.dict_stats = dict_stats
        self.args = args
        self.cluster_info = cluster_info

        self.context = {
            'last_updated': datetime.datetime.now().strftime("%A %d %b %Y, %H:%M"),
            'startDay': args.startDay,
            'endDay': args.endDay,
            'institution': cluster_info['institution'],
            'cluster_name': cluster_info['cluster_name'],
            'PUE': cluster_info['PUE'],
            'CI': cluster_info['CI'],
            'energy_cost_perkWh': cluster_info['energy_cost'],
            'texts_intro': cluster_info['texts_intro'],
        }

        self.template_plotly = "plotly_white"
        self.custom_colours = {
            'area': '#a6cee3'
        }
        self.height_plotly = 350

        self.user_here = dict_stats['user']

        self.outputDir = args.outputDir2use['path']
        self.plotsDir = os.path.join(self.outputDir, 'plots')
        os.makedirs(self.plotsDir)

    def _user_context(self):
        ####################################
        # User-specific part of the report #
        ####################################

        self.context['user'] = {'userID': self.user_here}

        self.context['usersActivity'] = {
            self.user_here: get_summary_texts(
                self.dict_stats['userActivity'][self.user_here],
                cluster_info=self.cluster_info
            )
        }

        ### User's overall metrics

        df_userDaily_here = self.dict_stats['userDaily']

        # Daily carbon footprint
        fig_userDailyCarbonFootprint = px.area(
            df_userDaily_here, x='SubmitDate', y="carbonFootprint",
            labels=dict(SubmitDate='', carbonFootprint='Carbon footprint (gCO2e)'),
            title="Daily carbon footprint",
            template=self.template_plotly,
            color_discrete_sequence=[self.custom_colours['area']]
        )
        fig_userDailyCarbonFootprint.update_layout(height=self.height_plotly)
        fig_userDailyCarbonFootprint.write_html(
            os.path.join(self.plotsDir, "plotly_thisuserDailyCarbonFootprint.html"),
            include_plotlyjs='cdn'
        )

        # Daily number of jobs
        fig_userDailyNjobs = px.area(
            df_userDaily_here, x='SubmitDate', y="n_jobs",
            labels=dict(SubmitDate='', n_jobs='Number of jobs started'),
            title="Number of jobs started",
            template=self.template_plotly,
            color_discrete_sequence=[self.custom_colours['area']]
        )
        fig_userDailyNjobs.update_layout(height=self.height_plotly)
        fig_userDailyNjobs.write_html(
            os.path.join(self.plotsDir, "plotly_thisuserDailyNjobs.html"),
            include_plotlyjs='cdn'
        )

        # Daily CPU time
        fig_userDailyCpuTime = px.area(
            df_userDaily_here, x='SubmitDate', y="CPUhoursCharged",
            labels=dict(SubmitDate='', CPUhoursCharged='CPU core-hours'),
            title="CPU core hours",
            template=self.template_plotly,
            color_discrete_sequence=[self.custom_colours['area']]
        )
        fig_userDailyCpuTime.update_layout(height=self.height_plotly)
        fig_userDailyCpuTime.write_html(
            os.path.join(self.plotsDir, "plotly_thisuserDailyCpuTime.html"),
            include_plotlyjs='cdn'
        )

        # Daily Memory requested
        fig_userDailyCpuTime = px.area(
            df_userDaily_here, x='SubmitDate', y="memoryRequested",
            labels=dict(SubmitDate='', memoryRequested='Memory requested (GB)'),
            title="Memory requested",
            template=self.template_plotly,
            color_discrete_sequence=[self.custom_colours['area']]
        )
        fig_userDailyCpuTime.update_layout(height=self.height_plotly)
        fig_userDailyCpuTime.write_html(
            os.path.join(self.plotsDir, "plotly_thisuserDailyMemoryRequested.html"),
            include_plotlyjs='cdn'
        )

        # Total success rate
        n_success = self.dict_stats['userActivity'][self.user_here]['n_success']
        n_failure = self.dict_stats['userActivity'][self.user_here]['n_jobs'] - self.dict_stats['userActivity'][self.user_here]['n_success']
        foo = pd.DataFrame({
            'Status': ['Success', 'Failure'],
            'Number of jobs': [n_success, n_failure]
        })
        fig_userSuccessRate = px.pie(
            foo, values='Number of jobs', names='Status', color='Status',
            color_discrete_map={'Success':"#A9DFBF", 'Failure': "#F5B7B1"},
            template=self.template_plotly,
            hole=.6,
        )
        fig_userSuccessRate.update_layout(height=self.height_plotly)
        fig_userSuccessRate.write_html(
            os.path.join(self.plotsDir, "plotly_thisuserSuccessRate.html"),
            include_plotlyjs='cdn'
        )

        # Daily success rate
        fig_userDailySuccessRate = px.area(
            pd.melt(df_userDaily_here, id_vars='SubmitDate', value_vars=['failure_rate', 'success_rate']),
            x='SubmitDate', y="value", color='variable',
            color_discrete_map={'failure_rate': "#F5B7B1", 'success_rate': "#A9DFBF"},
            labels=dict(SubmitDate='', value='% of failed jobs (in red)', variable=""),
            # title="",
            template=self.template_plotly
        )
        fig_userDailySuccessRate.update_layout(height=self.height_plotly, showlegend=False)
        fig_userDailySuccessRate.write_html(
            os.path.join(self.plotsDir, "plotly_thisuserDailySuccessRate.html"),
            include_plotlyjs='cdn'
        )

        # Memory efficiency
        fig_userMemoryEfficiency = px.histogram(
            np.reciprocal(self.dict_stats['memoryOverallocationFactors'][self.user_here]) * 100,
            labels=dict(value="Memory efficiency (%)"),
            template=self.template_plotly,
            color_discrete_sequence=[self.custom_colours['area']]
        )
        fig_userMemoryEfficiency.update_layout(
            bargap=0.2,
            yaxis_title="Number of jobs",
            showlegend=False,
            height=self.height_plotly
        )
        fig_userMemoryEfficiency.write_html(
            os.path.join(self.plotsDir, "plotly_thisuserMemoryEfficiency.html"),
            include_plotlyjs='cdn'
        )

    def generate(self):

        self.context['include_user_context'] = True

        self._user_context()

        environment = Environment(
            loader=FileSystemLoader(['frontend/templates/', self.plotsDir]),
            # autoescape=select_autoescape(),
            # undefined=SilentUndefined  # StrictUndefined is mostly for testing, SilenUndefined to ignore missing ones
        )

        j2_template = environment.get_template('report_blank.html')
        j2_rendered = j2_template.render(self.context)

        ## Export
        # print(os.getcwd())
        report_path = os.path.join(self.outputDir, f"report_{self.user_here}.html")
        with open(report_path, 'w') as file:
            file.write(j2_rendered)
        # Also copy across the styles.css
        shutil.copy("frontend/templates/styles.css", self.outputDir)

        return report_path

        # FIXME the pdf export doesn't really work...sticking with html for now
        # Follows guidelines from https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#command-line
        # from weasyprint import HTML, CSS
        #
        # css = CSS(string=''' @page {size: 53.34cm 167.86 cm;} ''')
        # HTML("outputs/report_rendered.html").write_pdf("outputs/report_rendered.pdf", stylesheets=[css])