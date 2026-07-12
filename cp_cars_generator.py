import argparse
import copy
import math
import gspread
import random
import numpy as np
import pandas as pd
import re

URL = 'https://docs.google.com/spreadsheets/d/1G_IVcD3l6qV6h6UNixk2zZzwJd_ZpOfU27cRe_lFaMQ/'
FULL_ROSTER_WORKSHEET = '!Detailed Roster from App'
ROSTER_WORKSHEET = '!Roster for Car Grouping'
PAIRINGS_WORKSHEET = '!Required Car Pairings'
CAR_GROUP_WORKSHEET = '!Car Group {}'
DETAILED_CAR_GROUP_WORKSHEET = '!Detailed Car Group {}'
FULL_CAR_SIZE = 4
EMPTY = -1

BIPOC_WEIGHT = 1
AGE_WEIGHT = 1
EXP_WEIGHT = 1
PREV_WEIGHT = 3

DATES_COL = 'Canvassing Dates'
DELETE_COLS =[DATES_COL, 'Last Name']
ORIG_COLS = ['First Name', 'Last Name', 'Will Be A Driver', 'Willing To Be Backup Car', 'Affiliation', DATES_COL, 'Half Day Status',
             'Generation', 'BIPOC Status', 'Canvassing Experience']
RENAME_COLS = {'Will Be A Driver':'Driver','Willing To Be Backup Car':'Backup Driver','First Name':'Name'}
MARK = 'X'
PAIR_COL = 'Pair (Yes/No)'
SEPARATE_COL = 'Separate Car'
NAME1_COL = 'Name1'
NAME2_COL = 'Name2'

pairings_cols = [NAME1_COL, NAME2_COL, PAIR_COL, SEPARATE_COL]
roster_cols = [RENAME_COLS[x] if x in RENAME_COLS else x for x in ORIG_COLS if x not in DELETE_COLS]

def update_sheet(sht, name, df, worksheet_list):
    if name in worksheet_list:
        worksheet = sht.worksheet(name)
        worksheet.clear()
    else:
        worksheet = sht.add_worksheet(name, rows=0, cols=0)

    data = [[int(x) if isinstance(x, np.int64) else x for x in y] for y in df.values.tolist()]
    worksheet.update([df.columns.values.tolist()] + data)

def get_sheet(sht, name):
    worksheet = sht.worksheet(name)
    return pd.DataFrame(worksheet.get_all_records())

def init():
    gc = gspread.service_account(filename=r'streamlit/common-power-6502fad9d9f3.json')
    sht = gc.open_by_url(URL)

    worksheet_list = [x.title for x in sht.worksheets()]
    if ROSTER_WORKSHEET in worksheet_list or PAIRINGS_WORKSHEET in worksheet_list:
        raise ValueError(f'{ROSTER_WORKSHEET} or {PAIRINGS_WORKSHEET} found. Spreadsheet may have already been initialized. Delete these sheets to enable initialization.')

    assert FULL_ROSTER_WORKSHEET in worksheet_list, f'Worksheet entitled {FULL_ROSTER_WORKSHEET} must exist in spreadsheet and contained roster export from app'

    df_full_roster = get_sheet(sht, FULL_ROSTER_WORKSHEET)
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

    update_sheet(sht, ROSTER_WORKSHEET, df_roster, worksheet_list)
    update_sheet(sht, PAIRINGS_WORKSHEET, df_pairings, worksheet_list)

def main(mode):
    gc = gspread.service_account(filename=r'streamlit/common-power-6502fad9d9f3.json')
    sht = gc.open_by_url(URL)

    worksheet_list = [x.title for x in sht.worksheets()]
    assert ROSTER_WORKSHEET in worksheet_list, f'{ROSTER_WORKSHEET} sheet not found. init (-i) must be run'
    assert PAIRINGS_WORKSHEET in worksheet_list, f'{PAIRINGS_WORKSHEET} sheet not found. init (-i) must be run'

    df_roster = get_sheet(sht, ROSTER_WORKSHEET)
    df_pairings = get_sheet(sht, PAIRINGS_WORKSHEET)

    day_cols = [x for x in df_roster.columns if re.search(r'^Day\s\d+\s', x)]

    missing_cols = [x for x in roster_cols if x not in df_roster]
    assert len(missing_cols)==0, f'Expected columns are missing from {ROSTER_WORKSHEET}: {missing_cols}'
    pairings_cols.extend(day_cols)
    missing_cols = [x for x in pairings_cols if x not in df_pairings]
    assert len(missing_cols)==0, f'Expected columns are missing from {PAIRINGS_WORKSHEET}: {missing_cols}'

    ndays = len(day_cols)
    day = set_day(mode, worksheet_list, ndays)

    day_col = [x for x in df_roster.columns if x.startswith(f'Day {day}')][0]
    df_roster = df_roster[df_roster[day_col].str.lower()==MARK.lower()].reset_index(drop=True)
    df_pairings = df_pairings[df_pairings[day_col].str.lower()==MARK.lower()].reset_index(drop=True)
    df_pairings = df_pairings[df_pairings[NAME1_COL].isin(df_roster['Name']) & df_pairings[NAME2_COL].isin(df_roster['Name'])]

    age_cats = df_roster['Generation'].unique()
    gen_start_years = [int(re.search(r'\((\d+)\s\-', x).groups(0)[0]) for x in age_cats]
    age_cats = [x for _, x in sorted(zip(gen_start_years, age_cats))]  # Sort by year
    # Reduce number of age categories to 3 (or fewer)
    gen_labels, new_age_cats = combine_age_groups(df_roster['Generation'], age_cats)

    # Convert to index values
    df_roster['age'] = gen_labels.apply(lambda x: new_age_cats.index(x))
    df_roster['bipoc'] = df_roster['BIPOC Status'].apply(lambda x: list(df_roster['BIPOC Status'].unique()).index(x))
    df_roster['experience'] = combine_experience_groups(df_roster['Canvassing Experience'], day)
    df_roster['driver'] = (df_roster['Driver'].str.lower()=='yes') | df_roster['Driver'].str.contains(str(day)) | (df_roster['Driver']==day)

    car_groups = gen_car_groups(df_roster, df_pairings, day, sht)

    # TODO: Resort sheets so that highest priority are on the left???
    # TODO: Add key sheet that tells what each sheet is including what ! is???
    # TODO: In app, include ability to modify pairings

    nrows = max([len(x) for x in car_groups])
    out = {}
    for k, car in enumerate(car_groups):
        out[f'Car {k+1}'] = [df_roster.loc[car[k], 'Name'] if k<len(car) else "" for k in range(nrows)]
        out[f'Gen {k+1}'] = [df_roster.loc[car[k], 'age'] if k<len(car) else "" for k in range(nrows)]
        out[f'BIPOC {k+1}'] = [df_roster.loc[car[k], 'bipoc'] if k<len(car) else "" for k in range(nrows)]
        out[f'Exp {k+1}'] = [df_roster.loc[car[k], 'experience'] if k<len(car) else "" for k in range(nrows)]

    index = ['Driver' if k==0 else k+1 for k in range(nrows)]
    df_out = pd.DataFrame(out, index=index)

    # sheet = DETAILED_CAR_GROUP_WORKSHEET.format(day)
    # update_sheet(sht, sheet, df_out.reset_index(), worksheet_list)

    sheet = CAR_GROUP_WORKSHEET.format(day)
    df_out_min = df_out[[x for x in df_out.columns if x.startswith('Car')]].reset_index()
    cols = list(df_out_min.columns)
    cols[0] = ''
    df_out_min.columns = cols
    update_sheet(sht, sheet, df_out_min, worksheet_list)


def set_day(mode, worksheet_list, ndays):
    group_created = pd.Series([CAR_GROUP_WORKSHEET.format(k+1) in worksheet_list for k in range(ndays)])

    if mode=='next':
        day = group_created[group_created].index[-1]+2 if group_created.any() else 1  # +2 = next day + convert to 1-based
    elif mode=='overwrite':
        assert group_created.any(), 'Car group cannot be overwritten if no car groups have been created'
        day = group_created[group_created].index[-1]+1
    else:
        raise ValueError(f'Unknown day parameter: {day}')
    
    assert group_created[:day-1].all(), f'Attempting to generate car groups for day {day} but not all car groups have been made before day {day}'
    assert day<=ndays, 'Car group requested for a day beyond the number of days in the trip'
    return day


def combine_experience_groups(exp_labels, day):
    # People will have increased experience as the trip continues

    with_cp = exp_labels.str.contains('with CP') & (~exp_labels.str.contains('not with CP'))
    a_lot = exp_labels.str.contains('a lot')
    labels = (with_cp & a_lot).astype('int')
    if day<3:
        # Maximize likelihood that groups vary in experience
        if with_cp.mean()<0.5:
            # 2= Lots of CP experience
            # 1= Some CP experience OR lots of canvas experience
            # 0= Little canvass experience
            labels+=1
            labels[~with_cp & ~a_lot] = 0
        elif labels.mean()<0.5:
            # 2= Lots of CP experience
            # 1= Some CP experience
            # 0= No CP experience
            labels+=1
            labels[~with_cp] = 0
    elif day==3:
        # 1= CP experience or lots of canvass experience
        # 0= Little canvass experience
        labels = with_cp | a_lot
    else:
        labels = labels | (~labels)  # Everyone is the same

    return labels


def combine_age_groups(gen_labels, age_cats):
    ngroups = 3
    if len(age_cats)<=ngroups:
        return gen_labels, age_cats
    
    new_age_cats = []
    start = 0
    group_size = math.ceil(len(age_cats)/ngroups)
    for g in range(ngroups):
        cur_group_size = group_size if start+group_size+(ngroups-len(new_age_cats)-1)*(group_size-1)<=len(age_cats) else group_size-1
        for k in range(start+1, start+cur_group_size):
            gen_labels[gen_labels==age_cats[k]] = age_cats[start]
        new_age_cats.append(age_cats[start])
        start+=cur_group_size
        
    return gen_labels, new_age_cats

def find_group(req_group0, vols, group):
    for k in vols:
        cur_group = set(np.setdiff1d(req_group0[:,k].nonzero(),k))
        cur_group = cur_group - group
        group.add(k)

        group = find_group(req_group0, cur_group, group)

    return group

def _get_rem(num_vols):
    return (FULL_CAR_SIZE - (num_vols % FULL_CAR_SIZE) ) % FULL_CAR_SIZE

def get_num_cars(num_vols):
    # # of carsize-1 cars + # of carsize cars
    rem = _get_rem(num_vols)
    return int(rem + (num_vols-rem*(FULL_CAR_SIZE-1)) / FULL_CAR_SIZE)

def groupname(day):
    return f"CarGroup{day}"

def get_car_sizes(num_vols0, must_be_in_same_car, separate_car):
    carsizes0 = []
    for m,s in zip(must_be_in_same_car, separate_car):
        if len(m)>=FULL_CAR_SIZE or s:
            carsizes0.append(len(m))

    num_vols = num_vols0 - sum(carsizes0)

    num_cars = math.ceil(num_vols / FULL_CAR_SIZE)
    carsizes = [FULL_CAR_SIZE for _ in range(num_cars)]

    for k in range(sum(carsizes) - num_vols):
        carsizes[k % num_cars]-=1

    assert sum(carsizes)==num_vols

    # TODO: Assuming must_pair and do_not_pair don't make problem impossible
    
    carsizes = carsizes0+carsizes
    assert sum(carsizes)==num_vols0
    return carsizes


def get_pairs(df_pairings):
    must_pair = []
    separate_car = []
    do_not_pair = []
    for k in df_pairings.index:
        is_pair = df_pairings.loc[k, PAIR_COL].lower()=='yes'
        groups = must_pair if is_pair else do_not_pair
        is_separate = df_pairings.loc[k, SEPARATE_COL].lower()==MARK.lower() if is_pair else False
        added = None
        remove = []
        for j, g in enumerate(groups):            
            if df_pairings.loc[k, NAME1_COL] in g or df_pairings.loc[k, NAME2_COL] in g:
                if added != None:
                    groups[added].update(g)
                    separate_car[added] |= separate_car[j]
                    remove.append(j)
                else:
                    added = j
                    g.add(df_pairings.loc[k, NAME1_COL])
                    g.add(df_pairings.loc[k, NAME2_COL])
                    if is_pair:
                        separate_car[j] |= is_separate

        if added == None:
            groups.append(set([df_pairings.loc[k, NAME1_COL], df_pairings.loc[k, NAME2_COL]]))
            if is_pair:
                separate_car.append(is_separate)
            
        for g in remove:
            groups.pop(g)
            if is_pair:
                separate_car.pop(g)

    # Ensure that must_pair and do_not_pair do not conflict
    for m in must_pair:
        for d in do_not_pair:
            assert len(m&d)<2, 'There exists at least one case where a group that must be paired and group that must NOT be paired cannot both be satisfied'

    return must_pair, separate_car, do_not_pair


def gen_car_groups(df_roster, df_pairings, day, sht):

    assert df_pairings[PAIR_COL].str.lower().isin(['yes','no']).all(), 'All rows in Pair (Yes/No) column of Required Car Pairings sheet must be either Yes or No'

    num_vols = len(df_roster)

    prev_pair = np.zeros((num_vols,num_vols))
    for d in range(day-1):
        df_past = get_sheet(sht, CAR_GROUP_WORKSHEET.format(d+1))
        car_cols = [x for x in df_past.columns if x.startswith('Car')]
        # Populate prev_pair
        for c in car_cols:
            matches = df_roster['Name'].isin(df_past[c])
            for i in matches[matches].index:
                for j in matches[matches].index:
                    if i!=j:
                        prev_pair[i,j]+=1

    must_be_in_same_car, separate_car, do_not_pair = get_pairs(df_pairings)

    must_be_in_same_car =  [x for _, x in sorted(zip([len(y) for y in must_be_in_same_car], must_be_in_same_car), reverse=True)]
    do_not_pair =  [x for _, x in sorted(zip([len(y) for y in do_not_pair], do_not_pair), reverse=True)]

    # Convert names to indices in must_be_in_same_car
    must_be_in_same_car = [[df_roster['Name'][df_roster['Name'] == y].index[0] for y in x] for x in must_be_in_same_car]
    do_not_pair = [[df_roster['Name'][df_roster['Name'] == y].index[0] for y in x] for x in do_not_pair]

    carsizes = get_car_sizes(num_vols, must_be_in_same_car, separate_car)
    carsizes.sort(reverse=True)

    # Create base car groups
    car_groups0 = [np.ones(x, dtype=int)*EMPTY for x in carsizes]

    # Add separate car groups
    available0 = list(df_roster.index)
    num_cars_avail = len(car_groups0)
    drop = []
    for j, (m,s) in enumerate(zip(must_be_in_same_car, separate_car)):
        if s or len(m)>=FULL_CAR_SIZE:
            # Find car of this size that is empty
            drop.append(j)
            car = [x for x in car_groups0 if len(x)==len(m) and x[0]==EMPTY][0]
            num_cars_avail-=1

            # Find a driver. Driver must be first.
            drivers = df_roster.loc[m, 'driver']
            if not drivers.any():
                drivers = df_roster.loc[m, 'Backup Driver'].str.lower()=='yes'
                if not drivers.any():
                    raise ValueError('No one in car is a driver!')
            drivers = drivers[drivers].index
            car[0] = drivers[0]
            available0.remove(drivers[0])
            m.remove(drivers[0])
            for k in range(len(m)):
                car[k+1] = m[k]
                available0.remove(m[k])

    must_be_in_same_car = [x for k, x in enumerate(must_be_in_same_car) if k not in drop]

    # TODO: Add config
    # TODO: Add test for more code

    # First add drivers
    potential_drivers = df_roster.loc[available0]['driver']
    potential_drivers = list(potential_drivers[potential_drivers].index)
    # Ensure that drivers are not being grouped together
    for g in must_be_in_same_car:
        in_group = [x for x in potential_drivers if x in g]
        if len(in_group)>1:
            random.shuffle(in_group)  # First one will be kept
            potential_drivers = [x for x in potential_drivers if x not in in_group[1:]]

    if len(potential_drivers)<num_cars_avail:
        # Need to add some backup drivers
        backups = df_roster.loc[available0]['Backup Driver'].str.lower()=='yes'
        backups = backups[backups].index

        backups = list(set(backups) - set(potential_drivers)) # Ensure no overlap
        # Ensure that drivers are not being grouped together
        for g in must_be_in_same_car:
            in_group = [x for x in backups if x in g]
            in_group_drivers = [x for x in potential_drivers if x in g]
            if len(in_group_drivers)>0:
                backups = [x for x in backups if x not in in_group]
            elif len(in_group)>1:
                random.shuffle(in_group)  # First one will be kept
                backups = [x for x in backups if x not in in_group[1:]]

        random.shuffle(backups)
        potential_drivers.extend(backups[:num_cars_avail - len(potential_drivers)])


    ntrials = 100
    min_score = 1e6
    for _ in range(ntrials):
        car_groups = rand_car_groups(car_groups0, available0, potential_drivers, must_be_in_same_car, do_not_pair, df_roster['experience'])

        score = 0
        for k in range(len(car_groups)):
            car = car_groups[k]

            bipoc_score = df_roster.loc[car,'bipoc'].duplicated().sum()
            age_score = df_roster.loc[car,'age'].duplicated().sum()
            exp_score = df_roster.loc[car,'experience'].duplicated().sum()

            idx = car[None]*prev_pair.shape[0] + car[:,None]  # Get 1-D indices for all pairs
            prev_score = prev_pair.flatten()[idx].sum() / 2  # prev_pair is symmetric. Divide by 2 to only sum 1 side

            score+=BIPOC_WEIGHT * bipoc_score + AGE_WEIGHT * age_score + EXP_WEIGHT * exp_score + PREV_WEIGHT * prev_score

        if score < min_score:
            best_group = car_groups
            min_score = score

    return best_group

def rand_car_groups(car_groups0, vols, potential_drivers, must_be_in_same_car, do_not_pair, experience):
    
    max_iter = 20
    for _ in range(max_iter):
        random.shuffle(potential_drivers)
        car_group = copy.deepcopy(car_groups0)
        avail = [True for _ in range(len(vols))]

        avail_groups = [True for _ in range(len(must_be_in_same_car))]

        # Add driver to each car
        avail_drivers = [True for _ in range(len(potential_drivers))]
        fail = False
        for k in range(len(car_group)):
            if car_group[k][0]==EMPTY:
                for d in range(len(potential_drivers)):
                    if not avail_drivers[d]:
                        continue

                    # Check if driver is part of group
                    g = [x for x in must_be_in_same_car if potential_drivers[d] in x]
                    # Check if car is big enough
                    if len(g)>0:
                        g = g[0]
                        if len(car_group[k])<len(g):
                            continue

                        avail_groups[must_be_in_same_car.index(g)] = False
                        car_group[k][0] = potential_drivers[d]
                        avail[vols.index( potential_drivers[d])] = False
                        for j in range(1,len(car_group[k])):
                            for n in range(len(g)):
                                if avail[vols.index(g[n])]:
                                    car_group[k][j] = g[n]
                                    avail[vols.index(g[n])] = False
                                    break
                    else:
                        # Not in group
                        car_group[k][0] = potential_drivers[d]
                        avail[vols.index( potential_drivers[d])] = False
                    avail_drivers[d] = False
                    break
                else:
                    fail = True
                    break

        if fail:
            continue

        max_experience = experience.max()

        rem_groups = [x for x,y in zip(must_be_in_same_car, avail_groups) if y]
        random.shuffle(rem_groups)
        # Insert all groups
        for g in rem_groups:
            # Find cars with enough space
            avail_cars = [x for x in car_group if (x==EMPTY).sum()>=len(g)]
            if len(avail_cars)==0:
                fail = True
                break
            random.shuffle(avail_cars)
            for car in avail_cars:
                # Ensure that driver can be paired with all members of group
                can_pair = len([d for d in do_not_pair if car[0] in d and any(x in d for x in g)])==0
                # Ensure that there is someone with max experience in group
                has_experience = experience.loc[car[0]]==max_experience or (experience.loc[g]==max_experience).any()
                if can_pair and has_experience:
                    car[np.where(car==EMPTY)[:len(g)]] = g
                    break
            else:
                fail = True
                break

        if fail:
            continue

        rem = [x for x,y in zip(vols, avail) if y and not any(x in g for g in rem_groups)]
        random.shuffle(rem)

        exp_vols = experience.loc[rem]==max_experience
        exp_vols = exp_vols[exp_vols].index

        # Ensure that there is an experienced volunteer in all groups
        used = []
        for car in car_group:
            if (car==EMPTY).any() and not (experience.loc[car[car!=EMPTY]]==max_experience).any():
                # Car has space and none of current volunteers are most experienced
                for v in [x for x in exp_vols if x not in used]:
                    if len([d for d in do_not_pair if v in d and any(x in d for x in car)])==0:
                        car[np.where(car==EMPTY)[0][0]] = v
                        used.append(v)
                        break
                else:
                    fail = True
                    break

        if fail:
            continue      

        remove = [x for x in exp_vols if x in used]
        rem = [x for x in rem if x not in remove]
        used = []
        for car in car_group:
            for m in range(len(car)):
                if car[m]==EMPTY:
                    for v in rem:
                        if v not in used and len([d for d in do_not_pair if v in d and any(x in d for x in car)])==0:
                            car[m] = v
                            used.append(v)
                            break
                    else:
                        fail = True

        if fail:
            continue

        assert len(rem)==len(used)

        return car_group
    else:
        raise ValueError('Failed to generate car group due to constraints on car pairings and drivers')

if __name__=='__main__':
    parser = argparse.ArgumentParser(
                    prog='CP Cars Generator',
                    description='Populates Google Sheet with Car Groups Based on Optimization')
    parser.add_argument('-i', '--init', action='store_true', help='Spreadsheet must be initialized before use.') 
    parser.add_argument('-m', '--mode', default='next', choices=['next','overwrite'], help='Generate car group for next day or overwrite most recent day')

    args = parser.parse_args()

    if args.init:
        init()
    else:
        main(args.mode)
    
    # filename = 'volunteers.xlsx'

    # if not os.path.exists(filename):
    #     df_all = sim_volunteers(20)
    #     df_all.to_excel(filename, index=False)

    # gen_car_groups(filename)