def formatText_footprint(footprint_g, use_html=False):
    '''
    Format the text to display the carbon footprint
    :param footprint_g: [float] carbon footprint, in gCO2e
    :return: [str] the text to display
    '''
    if use_html:
        co2e = "CO<sub>2</sub>e"
    else:
        co2e = "CO2e"
    if footprint_g < 1e3:
        text_footprint = f"{footprint_g:,.0f} g{co2e}"
    elif footprint_g < 1e6:
        text_footprint = f"{footprint_g / 1e3:,.0f} kg{co2e}"
    else:
        text_footprint = f"{footprint_g / 1e3:,.0f} T{co2e}"
    return text_footprint

def formatText_treemonths(tm_float, splitMonthsYear=True):
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
        if splitMonthsYear:
            text_trees = f"{ty} tree-years and {tm - ty * 12} tree-months"
        else:
            text_trees = f"{ty} tree-years"
    else:
        text_trees = f"{tm_float/12:.1f} tree-years"
    return text_trees

def formatText_flying(dict_stats, output_format='single_str'):
    """
    Format the text to display about flying
    :param dict_stats:
    :param output_format:
    :return: [str] or [(float,str)] text to display
    """
    if output_format not in ['single_str', 'dict']:
        raise ValueError()

    if dict_stats['flying_NY_SF'] < 0.5:
        value = round(dict_stats['flying_PAR_LON'], 2)
        if output_format == 'single_str':
            output_flying = f"{value:,} flights between Paris and London"
        else:
            output_flying = {'number': value, 'trip': 'Paris - London'}
    elif dict_stats['flying_NYC_MEL'] < 0.5:
        value = round(dict_stats['flying_NY_SF'], 2)
        if output_format == 'single_str':
            output_flying = f"{value:,} flights between New York and San Francisco"
        else:
            output_flying = {'number': value, 'trip': 'New York - San Francisco'}
    else:
        value = round(dict_stats['flying_NYC_MEL'], 2)
        if output_format == 'single_str':
            output_flying = f"{value:,} flights between New York and Melbourne"
        else:
            output_flying = {'number': value, 'trip': 'New York - Melbourne'}
    return output_flying