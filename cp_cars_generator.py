import argparse
import copy
import gspread
import random
import numpy as np
import string
import pandas as pd
import re

URL = 'https://docs.google.com/spreadsheets/d/1G_IVcD3l6qV6h6UNixk2zZzwJd_ZpOfU27cRe_lFaMQ/'
FULL_ROSTER_WORKSHEET = '!Detailed Roster from App'
ROSTER_WORKSHEET = '!Roster for Car Grouping'
PAIRINGS_WORKSHEET = '!Required Car Pairings'
FULL_CARSIZE = 4

DATES_COL = 'Canvassing Dates'
DELETE_COLS =[DATES_COL, 'Last Name']
ORIG_COLS = ['First Name', 'Last Name', 'Will Be A Driver', 'Willing To Be Backup Car', 'Affiliation', DATES_COL, 'Half Day Status',
             'Generation', 'BIPOC Status', 'Canvassing Experience']
RENAME_COLS = {'Will Be A Driver':'Driver','Willing To Be Backup Car':'Backup Driver','First Name':'Name'}
MARK = 'X'

pairings_cols = ['Name1', 'Name2']
roster_cols = [RENAME_COLS[x] if x in RENAME_COLS else x for x in ORIG_COLS if x not in DELETE_COLS]

def init():
    gc = gspread.service_account(filename=r'streamlit/common-power-6502fad9d9f3.json')
    sht = gc.open_by_url(URL)

    worksheet_list = [x.title for x in sht.worksheets()]
    if ROSTER_WORKSHEET in worksheet_list or PAIRINGS_WORKSHEET in worksheet_list:
        raise ValueError(f'{ROSTER_WORKSHEET} or {PAIRINGS_WORKSHEET} found. Spreadsheet may have already been initialized. Delete these sheets to enable initialization.')

    assert FULL_ROSTER_WORKSHEET in worksheet_list, f'Worksheet entitled {FULL_ROSTER_WORKSHEET} must exist in spreadsheet and contained roster export from app'
    full_worksheet = sht.worksheet(FULL_ROSTER_WORKSHEET)

    df_full_roster = pd.DataFrame(full_worksheet.get_all_records())
    missing_cols = [x for x in ORIG_COLS if x not in df_full_roster]
    assert len(missing_cols)==0, f'Expected columns are missing from {FULL_ROSTER_WORKSHEET}: {missing_cols}'

    df_roster = df_full_roster[ORIG_COLS]
    df_roster = df_roster.rename(columns=RENAME_COLS)
    df_roster['Name'] = df_roster.apply(lambda x: f"{x['Name']} {x['Last Name']}", axis=1)

    dates = df_roster[DATES_COL].tolist()
    dates = [x.strip().split(' ') for x in dates]
    date_set = set()
    for d in dates:
        date_set.update(d)
    all_dates = list(set(pd.to_datetime(x) for x in date_set))
    all_dates.sort()

    day_cols = []
    for k,d in enumerate(all_dates):
        day_cols.append(f'Day {k+1} ({d.strftime('%a')})')
        df_roster[day_cols[-1]] = df_roster[DATES_COL].apply(lambda x: MARK if d in [pd.to_datetime(x) for x in x.strip().split(' ')] else '')

    df_roster = df_roster.drop(columns=DELETE_COLS)

    pairings_cols.extend(day_cols)
    df_pairings = pd.DataFrame([], columns=pairings_cols)

    worksheet = sht.add_worksheet(ROSTER_WORKSHEET, rows=0, cols=0)
    worksheet.update([df_roster.columns.values.tolist()] + df_roster.values.tolist())

    worksheet = sht.add_worksheet(PAIRINGS_WORKSHEET, rows=0, cols=0)
    worksheet.update([df_pairings.columns.values.tolist()] + df_pairings.values.tolist())

def main():
    gc = gspread.service_account(filename=r'streamlit/common-power-6502fad9d9f3.json')
    sht = gc.open_by_url(URL)

    worksheet_list = [x.title for x in sht.worksheets()]
    assert ROSTER_WORKSHEET in worksheet_list, f'{ROSTER_WORKSHEET} sheet not found. init (-i) must be run'
    assert PAIRINGS_WORKSHEET in worksheet_list, f'{PAIRINGS_WORKSHEET} sheet not found. init (-i) must be run'

    worksheet = sht.worksheet(ROSTER_WORKSHEET)
    df_roster = pd.DataFrame(worksheet.get_all_records())
    worksheet = sht.worksheet(PAIRINGS_WORKSHEET)
    df_pairings = pd.DataFrame(worksheet.get_all_records())

    day_cols = [x for x in df_roster.columns if re.search(r'^Day\s\d+\s', x)]

    missing_cols = [x for x in roster_cols if x not in df_roster]
    assert len(missing_cols)==0, f'Expected columns are missing from {ROSTER_WORKSHEET}: {missing_cols}'
    pairings_cols.extend(day_cols)
    missing_cols = [x for x in pairings_cols if x not in df_pairings]
    assert len(missing_cols)==0, f'Expected columns are missing from {PAIRINGS_WORKSHEET}: {missing_cols}'

    ndays = len(day_cols)
    AGE_CATS = ['Gen Z (1995 - 2012)', 'Millennial (1980 - 1994)', 'Gen X (1965 - 1979)', 'Boomer (1946 - 1964)']
    BIPOC_CATS = ['No', 'Yes']
    DRIVER_CATS = ['No', 'Yes']
    EXPERIENCE_CATS = ['None', 'I have done it once or twice without CP', 'I have done it once or twice with CP', 'I have a lot, but not with CP','I have a lot, and canvassed with CP']

def find_group(req_group0, vols, group):
    for k in vols:
        cur_group = set(np.setdiff1d(req_group0[:,k].nonzero(),k))
        cur_group = cur_group - group
        group.add(k)

        group = find_group(req_group0, cur_group, group)

    return group

def _get_rem(num_vols):
    return (FULL_CARSIZE - (num_vols % FULL_CARSIZE) ) % FULL_CARSIZE

def get_num_cars(num_vols):
    # # of carsize-1 cars + # of carsize cars
    rem = _get_rem(num_vols)
    return int(rem + (num_vols-rem*(FULL_CARSIZE-1)) / FULL_CARSIZE)

def groupname(day):
    return f"CarGroup{day}"

def get_car_sizes(num_vols):
    rem = _get_rem(num_vols)
    num_cars = get_num_cars(num_vols)
    carsizes = [FULL_CARSIZE-1 if k<rem else FULL_CARSIZE for k in range(num_cars)]
    assert sum(carsizes)==num_vols
    return carsizes

def sim_volunteers(num_vols):
    REQ_PAIR_RATE = 0.1

    TRIP_DATES = ['10/18/2025', '10/19/2025', '10/20/2025', '10/21/2025']

    age = np.random.randint(0, len(AGE_CATS), num_vols)
    is_bipoc = np.random.rand(num_vols)>0.66
    experience = np.random.randint(0, len(EXPERIENCE_CATS), num_vols)

    age = [AGE_CATS[k] for k in age]
    is_bipoc = [BIPOC_CATS[k] for k in is_bipoc]
    experience = [EXPERIENCE_CATS[k] for k in experience]

    len_name = 7
    letters = string.ascii_lowercase
    name = [''.join(random.choice(letters) for i in range(len_name)) for _ in range(num_vols)]

    attendance_rate = 0.9
    attendance = np.random.rand(num_vols,ndays)<attendance_rate

    # Get drivers
    num_attendees = attendance.sum(axis=0)
    min_num_drivers = [get_num_cars(x) for x in num_attendees]

    # Initialize
    is_driver = np.random.rand(num_vols) < min_num_drivers[0] / num_attendees[0]

    for day in range(ndays):
        num_drivers = is_driver[attendance[:,day]].sum()
        while num_drivers < min_num_drivers[day]:
            # Need more drivers on this day
            for r in range(num_vols):
                if attendance[r,day] and not is_driver[r]:
                    is_driver[r] = np.random.rand() <  (min_num_drivers[day]-num_drivers) / num_attendees[day]

            num_drivers = is_driver[attendance[:,day]].sum()

    is_driver = [DRIVER_CATS[k] for k in is_driver]

    # Create people who must be in the same car together
    req_group = np.eye(num_vols)
    for k in range(num_vols-1):
        if req_group[:,k].sum()<FULL_CARSIZE-1 and random.random()<REQ_PAIR_RATE:
            mate = random.randint(k+1, num_vols-1)
            
            curgroup = list(find_group(req_group, [k,mate], set()))
            for j in curgroup:
                req_group[curgroup,j] = 1

    assert np.all(req_group==req_group.T)

    pairs = []
    for k in range(num_vols):
        group = np.setdiff1d(req_group[:,k].nonzero(),k)
        if len(group)>0:
            pairs.append(','.join([name[i] for i in group]))
        else:
            pairs.append('')

    dates = []
    for k in attendance:
        d = [TRIP_DATES[j] for j,x in enumerate(k) if x]
        dates.append(' '.join(d))

    df = {'Name':name, 'Generation':age, 'BIPOC Status':is_bipoc, 'Will Be A Driver':is_driver, 'requests':pairs, 'Canvassing Dates':dates,
        'Canvassing Experience':experience}
    # for day in range(ndays):
    #     df[f'attendance{day}'] = attendance[:,day]

    return pd.DataFrame(df)


def gen_car_groups(filename, day=None):

    df_all = pd.read_excel(filename)

    df_all['age'] = df_all['Generation'].apply(lambda x: AGE_CATS.index(x))
    df_all['bipoc'] = df_all['BIPOC Status'].apply(lambda x: BIPOC_CATS.index(x))
    df_all['experience'] = df_all['Canvassing Experience'].apply(lambda x: EXPERIENCE_CATS.index(x if pd.notnull(x) else 'None'))
    df_all['driver'] = df_all['Will Be A Driver']=='Yes'

    df_all['Canvassing Dates'] = df_all['Canvassing Dates'].apply(lambda x: [pd.to_datetime(y) for y in x.split(' ')])

    dts = set()
    for x in df_all['Canvassing Dates'].tolist():
        dts.update(x)
    dts = list(dts)
    dts.sort()

    # Determine day
    if day == None:
        for d in range(ndays):
            if groupname(d) not in df_all:
                day = d
                break
    else:
        for d in range(day):
            if groupname(d) not in df_all:
                raise ValueError(f'Day {day} requested but carpools for previous day {d} have not been created')

    if day>0:
        raise NotImplementedError("Need to handle case for ")

    today = dts[day]
    df = df_all[df_all[f'attendance{day}']].reset_index()

    num_vols = len(df)

    prev_pair = np.zeros((num_vols,num_vols))
    for d in range(day):
        for i in df.index:
            carnum = df.loc[i, groupname[d]]
            idx = df[groupname[d]] == carnum

    req_group = np.zeros((num_vols,num_vols), dtype=bool)
    req_col = []
    for k in df.index:
        val = []
        if df.loc[k,'requests'] and pd.notnull(df.loc[k,'requests']):
            for req in df.loc[k,'requests'].split(','):
                if (m:=(df['Name']==req)).any():
                    m = m[m].index[0]
                    req_group[k,m] = req_group[m,k] = True
                    val.append(m)

        req_col.append(val)

    df['req'] = req_col

    num_cars = get_num_cars(num_vols)
    carsizes = get_car_sizes(num_vols)

    EMPTY = -1

    # Create base car groups
    car_groups0 = [np.ones(x, dtype=int)*EMPTY for x in carsizes]

    # First add drivers
    potential_drivers = df[df['driver']]
    available0 = list(df.index)
    # TODO: Update drivers based on previous drivers
    car = 0
    k = 0
    while car < num_cars:
        if potential_drivers.index[k] in available0:
            car_groups0[car][0] = potential_drivers.index[k]
            available0.remove(car_groups0[car][0])

            if len(potential_drivers.iloc[k]['req']):
                assert len(potential_drivers.iloc[k]['req'])+1 <= carsizes[k]
                for j in range(len(potential_drivers.iloc[k]['req'])):
                    car_groups0[car][j+1] = potential_drivers.iloc[k]['req'][j]
                    available0.remove(car_groups0[car][j+1])

            car+=1
        k+=1
        
    ntrials = 100
    min_score = 1e6
    for n in range(ntrials):
        # Fill in cars
        car_groups = copy.deepcopy(car_groups0)
        available = copy.deepcopy(available0)
        random.shuffle(available)
        for car in range(num_cars):
            rider = 0
            while rider < carsizes[car]:
                if car_groups[car][rider]==EMPTY:
                    for a in available:
                        if len(df.loc[a, 'req']) < carsizes[car]-rider:
                            # There is room in the car
                            car_groups[car][rider] = a
                            available.remove(a)
                            for r in df.loc[a, 'req']:
                                rider+=1
                                car_groups[car][rider] = r
                                available.remove(r)
                            break
                    else:
                        raise ValueError("Unable to fill car")
                    
                rider+=1

        score = 0
        BIPOC_WEIGHT = 1
        AGE_WEIGHT = 0.5
        PREV_WEIGHT = 3
        for k in range(len(car_groups)):
            car = car_groups[k]
            bipoc_score = abs((df.loc[car,'bipoc']*2-1).sum()) 
            bipoc_score-=carsizes[k]%2

            age_score = df.loc[car,'age'].duplicated().sum()

            idx = car[None]*prev_pair.shape[1] + car[:,None]
            prev_score = prev_pair.flatten()[idx].sum()

            score+=BIPOC_WEIGHT * bipoc_score + AGE_WEIGHT * age_score + PREV_WEIGHT * prev_score

        if score < min_score:
            best_group = car_groups
            min_score = score


    a = 1

if __name__=='__main__':
    parser = argparse.ArgumentParser(
                    prog='CP Cars Generator',
                    description='Populates Google Sheet with Car Groups Based on Optimization')
    parser.add_argument('-i', '--init', action='store_true') 

    args = parser.parse_args()

    if args.init:
        init()
    else:
        main()
    
    # filename = 'volunteers.xlsx'

    # if not os.path.exists(filename):
    #     df_all = sim_volunteers(20)
    #     df_all.to_excel(filename, index=False)

    # gen_car_groups(filename)