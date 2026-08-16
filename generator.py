import copy
import math
import numpy as np
import pandas as pd
import random
import re

from cp_gsheet import get_sheet
from worksheets import CAR_GROUP_WORKSHEET
from columns import PAIR_COL, \
    NAME1_COL, NAME2_COL, SEPARATE_COL
from constants import EMPTY, MARK

def gen_car_groups(df_roster, df_pairings, day, sht, config):
    FULL_CAR_SIZE = config['FULL_CAR_SIZE']

    age_cats = df_roster['Generation'].unique()
    gen_start_years = [int(re.search(r'\((\d+)\s\-', x).groups(0)[0]) for x in age_cats]
    age_cats = [x for _, x in sorted(zip(gen_start_years, age_cats))]  # Sort by year

    # Reduce number of age categories
    gen_labels, new_age_cats = combine_age_groups(df_roster['Generation'], age_cats, config)

    # Convert to index values
    df_roster['age'] = gen_labels.apply(lambda x: new_age_cats.index(x))
    df_roster['bipoc'] = df_roster['BIPOC Status'].apply(lambda x: list(df_roster['BIPOC Status'].unique()).index(x))
    df_roster['experience'] = combine_experience_groups(df_roster['Canvassing Experience'], day)
    df_roster['driver'] = (df_roster['Driver'].str.lower()=='yes') | df_roster['Driver'].str.contains(str(day)) | (df_roster['Driver']==day)

    num_vols = len(df_roster)

    # Create a mapping of volunteers who have previously been paired
    prev_pair = np.zeros((num_vols,num_vols))
    for d in range(day-1):
        df_past = get_sheet(sht['file'], CAR_GROUP_WORKSHEET.format(d+1))

        # Populate prev_pair
        for c in df_past['Car'].unique():
            matches = df_roster['Name'].isin(df_past['Name'][df_past['Car']==c])
            for i in matches[matches].index:
                for j in matches[matches].index:
                    if i!=j:
                        prev_pair[i,j]+=1

    must_be_in_same_car, separate_car, do_not_pair = get_pairs(df_pairings)

    # Remove people not canvassing this day
    must_be_in_same_car = [[y for y in x if (df_roster['Name']==y).any()] for x in must_be_in_same_car]
    do_not_pair = [[y for y in x if (df_roster['Name']==y).any()] for x in do_not_pair]

    # Get rid of groups that no longer have more than 1 person
    lens = [len(x) for x in must_be_in_same_car]
    must_be_in_same_car = [x for x,y in zip(must_be_in_same_car, lens) if y>1]
    separate_car = [x for x,y in zip(separate_car, lens) if y>1]
    do_not_pair = [x for x in do_not_pair if len(x)>1]

    # Sort in descending order of group size
    must_be_in_same_car =  [x for _, x in sorted(zip([len(y) for y in must_be_in_same_car], must_be_in_same_car), reverse=True)]
    do_not_pair =  [x for _, x in sorted(zip([len(y) for y in do_not_pair], do_not_pair), reverse=True)]

    # Convert names to indices in must_be_in_same_car
    must_be_in_same_car = [[df_roster['Name'][df_roster['Name'] == y].index[0] for y in x] for x in must_be_in_same_car]
    do_not_pair = [[df_roster['Name'][df_roster['Name'] == y].index[0] for y in x] for x in do_not_pair]

    carsizes = get_car_sizes(num_vols, must_be_in_same_car, separate_car, FULL_CAR_SIZE)
    carsizes.sort(reverse=True)

    # Create base car groups
    car_groups0 = [np.ones(x, dtype=int)*EMPTY for x in carsizes]

    # Add groups consisting of people who must be in the same car AND must be in their own separate car
    available0 = list(df_roster.index)
    num_cars_avail = len(car_groups0)
    drop = []
    for j, (m,s) in enumerate(zip(must_be_in_same_car, separate_car)):
        if s or len(m)>=FULL_CAR_SIZE:  # Must be in separate car due to request or size of group
            # Find car of this size that is empty
            drop.append(j)
            car = [x for x in car_groups0 if len(x)==len(m) and x[0]==EMPTY][0]
            num_cars_avail-=1

            # Find a driver. Driver must be first.
            drivers = df_roster.loc[m, 'driver']
            if not drivers.any():
                drivers = df_roster.loc[m, 'Backup Driver'].str.lower()=='yes'
                if not drivers.any():
                    raise ValueError(f'No one in group is a driver: {m}')
            drivers = drivers[drivers].index
            car[0] = drivers[0]
            available0.remove(drivers[0])
            m.remove(drivers[0])
            for k in range(len(m)):
                car[k+1] = m[k]
                available0.remove(m[k])

    # Remove pairings that have already been used
    must_be_in_same_car = [x for k, x in enumerate(must_be_in_same_car) if k not in drop]

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

            score+=config['BIPOC_WEIGHT'] * bipoc_score + config['AGE_WEIGHT'] * age_score + config['EXP_WEIGHT'] * exp_score + config['PREV_WEIGHT'] * prev_score

        if score < min_score:
            best_group = car_groups
            min_score = score

    out = {'Role':[], 'Car':[], 'Name':[], 'Gen':[], 'BIPOC':[], 'Exp':[]}
    for car, team in enumerate(best_group):
        for k,v in enumerate(team):
            role = 'Driver' if k==0 else ''
            out['Role'].append(role)
            out['Car'].append(car+1)
            out['Name'].append(df_roster.loc[v, 'Name'])
            out['Gen'].append(df_roster.loc[v, 'age'])
            out['BIPOC'].append(df_roster.loc[v, 'bipoc'])
            out['Exp'].append(df_roster.loc[v, 'experience'])

    df_out = pd.DataFrame(out)

    return df_out


def combine_age_groups(gen_labels, age_cats, config):
    ngroups = config['NUM_AGE_GROUPS']
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


def get_pairs(df_pairings):
    must_pair = []
    separate_car = []
    do_not_pair = []
    for k in df_pairings.index:
        is_pair = df_pairings.loc[k, PAIR_COL]
        groups = must_pair if is_pair else do_not_pair
        is_separate = df_pairings.loc[k, SEPARATE_COL] if is_pair else False
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


def get_car_sizes(num_vols0, must_be_in_same_car, separate_car, FULL_CAR_SIZE):
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
                    car[np.where(car==EMPTY)[0][:len(g)]] = g
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
