def calc_cost(row):
    # print(row.columns)
    if type(row['AllocTRES']) == float:
        return 0
    else:
        alloc_tres = row['AllocTRES'].split(',')
        n_elements = len(alloc_tres)
        billing = alloc_tres[0].split('=')[0]
        if billing == 'billing':
            n_bills = int(alloc_tres[0].split('=')[1])
        cost = 0
        for n in range(1, n_elements):
            resource = alloc_tres[n].split('=')[0]
            if resource == 'cpu':
                # row['PartitionTypeX'] = 'CPU'
                cost = (5 * n_bills * row['CPUtime (hours)']) / 100
            elif resource == 'gres/gpu':
                # row['PartitionTypeX'] = 'GPU'
                cost = (240 * n_bills * row['CPUtime (hours)']) / 100
        return cost

def calc_CPU(row):
    try:
        time_without_ms = row['TotalCPU'].split('.')[0]
        time_h_m_d = time_without_ms.split(':')
        d,h,m,s = 0,0,0,0
        if len(time_h_m_d) == 4:
            d,h,m,s = time_h_m_d[0],time_h_m_d[1],time_h_m_d[2],time_h_m_d[3]
        elif len(time_h_m_d) == 3:
            h,m,s = time_h_m_d[0],time_h_m_d[1],time_h_m_d[2]
        elif len(time_h_m_d) == 2:
            m,s = time_h_m_d[0],time_h_m_d[1]
        elif len(time_h_m_d) == 1:
            s = time_h_m_d[0]
        hours = (int(d)*86400 + int(h)*3600 + int(m)*60 + int(s)) / 3600
        # print(row['TotalCPU'],hours)
        return hours
    except:
        return 0
    
def calc_CPUtime(row):
    time_h_m_d = row['CPUTime'].split(':')
    h,m,s = time_h_m_d[0],time_h_m_d[1],time_h_m_d[2]
    d = 0
    try: 
        int(h)
    except:
        d = h.split('-')[0]
        h = h.split('-')[1]
    hours = (int(d)*86400 + int(h)*3600 + int(m)*60 + int(s)) / 3600
    # print(row['TotalCPU'],hours)
    return hours

def calc_efficiency(row):
        if row['CPUtime (hours)'] != 0:
            return row['TotalCPU (hours)'] / row['CPUtime (hours)']
        else: 
            return 0