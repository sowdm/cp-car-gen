import gspread
import logging
import pandas as pd
import random
import re
import streamlit as st
from streamlit_sortables import sort_items

import base_page
import columns
import cp_gsheet
from worksheets import CAR_GROUP_WORKSHEET

gsheet = base_page.setup(__file__)

nav_cols = base_page.navigation_buttons(2, '5_drivers.py')

day = st.session_state['day']
if nav_cols[0].button('Re-Generate Car Groups'):
    st.session_state['df_car_groups'] = None
    
if not isinstance(st.session_state['df_car_groups'], pd.DataFrame):
    pbar = st.progress(0.0, 'Simulating Car Groups...')
    st.session_state['df_car_groups'] =st.session_state['cargen'].gen_car_groups(pbar)
    pbar.empty()

    st.session_state['car_groups_default'] = []
    for car in st.session_state['df_car_groups']['Car'].unique():
        m = st.session_state['df_car_groups']['Car']==car
        st.session_state['car_groups_default'].append({'header':'', 'items':[]})
        carpool_dict = st.session_state['car_groups_default'][-1]
        for row in st.session_state['df_car_groups'].loc[m].iterrows():
            row = row[1]
            gen = row[columns.GENERATION_COL]
            if (m:=re.search('Gen ([A-Z])', gen, flags=re.IGNORECASE)):
                gen = m.groups()[0]
            elif 'millennial' in gen.lower():
                gen = 'M'
            elif 'boomer' in gen.lower():
                gen = 'B'
            elif 'silent' in gen.lower():
                gen = 'S'
            name = f'{row[columns.NAME_COL]} ({gen}'

            exp = row[columns.EXPERIENCE_COL].lower()
            if 'not with cp' in exp or 'without cp' in exp:
                if 'a lot' in exp:
                    exp = 2
                else:
                    exp = 1
            elif 'a lot' in exp:
                exp = 4
            elif 'none' in exp:
                exp = 0
            else:
                exp = 3

            name+=f', E{exp}'

            if row[columns.BIPOC_COL].lower()=='yes':
                name+=', BIPOC'

            if row[columns.AFFILIATION_COL].lower() not in ['','n/a','none']:
                affil = re.sub(r'\(.+\)', '', row[columns.AFFILIATION_COL])
                if 'action academy' in affil.lower():
                    affil = 'Action'
                name+=', ' + affil

            name+=')'

            if row['Role']=='Driver':
                carpool_dict['header'] = f'Car {car} Driven By **{name}**'
            else:
                carpool_dict['items'].append(name)

st.subheader('Generated Car Groups')

st.info('**To re-arrange car pools, use the select boxes to add and subtract people from a car. '
        'Click Export button when complete.**\n\n' \
        '**Generations**: S = Silent Generation, B = Boomer, X = Gen X, M = Millenial, Z = Gen Z\n\n' \
        '**Experience**: E0 = None, E1 = A little w/o CP, E2 = A lot w/o CP, E3 = A little w/ CP, E4 = A lot w/ CP\n\n' \
        'Action = Action Academy Student or Graduate')

# -1 is to account for driver not being included
car_sizes = st.session_state['df_car_groups']['Car'].value_counts()
min_car_size = car_sizes.min()-1
max_car_size = car_sizes.max()-1

container_error = st.container()
container_warning = st.container()

all_names = [y for x in st.session_state['car_groups_default'] for y in x['items']]

st.session_state['carpool_selection'] = []
for car in st.session_state['car_groups_default']:
    st.session_state['carpool_selection'].append(st.multiselect(car['header'], options=all_names, default=car['items']))

req_car_sizes = [len(x) for x in st.session_state['carpool_selection']]
if min(req_car_sizes) < min_car_size or max(req_car_sizes) > max_car_size:
    with container_warning:
        st.warning(f'One or more carpools has fewer/more volunteers than the minimum/maximum expected ({min_car_size}/{max_car_size}). ' +\
                   'This is allowable but please review to ensure it is desired!')

# Ensure that nobody is in multiple cars
counts = [[] for _ in all_names]
for carnum, car in enumerate(st.session_state['carpool_selection']):
    for y in car:
        for k,n in enumerate(all_names):
            if y==n:
                counts[k].append(carnum)

multiple_cars = [(x,y) for x,y in zip(all_names, counts) if len(y)>1]
no_cars = [x for x,y in zip(all_names, counts) if len(y)==0]

disabled = len(multiple_cars)>0 or len(no_cars)>0
if disabled:
    with container_error:
        errmsg = ''
        if len(multiple_cars)>0:
            errmsg = f'There are volunteers in multiple cars. Please correct: '
            for name, cars in multiple_cars:
                errmsg+=name + ' (Cars '
                for c in cars:
                    errmsg+=f'{c},'
                errmsg = errmsg[:-1]  + '), ' # Remove trailing comma

            errmsg = errmsg[:-2]

        if len(no_cars)>0:
            if len(errmsg)>0:
                errmsg+='\n\n'

            errmsg += f'There are volunteers NOT in a car. Please correct: {', '.join(no_cars)}'

        st.error(errmsg)

if nav_cols[1].button(f'Export Day {day} Car Group to Google Spreadsheet', disabled=disabled):
    for k in range(len(st.session_state['carpool_selection'])):
        names = [x[:x.rfind('(')-1] for x in st.session_state['carpool_selection'][k]]
        for n in names:
            i = st.session_state['df_car_groups'][columns.NAME_COL]==n
            assert i.any(), f'Name {n} not found in car groups'
            st.session_state['df_car_groups'].loc[i, 'Car'] = k+1

    # Enable sorting of driver to front
    sort_val = 'ZZZ'
    st.session_state['df_car_groups'].loc[st.session_state['df_car_groups']['Role']=='', 'Role'] = sort_val
    st.session_state['df_car_groups'] = st.session_state['df_car_groups'].sort_values(by=['Car', 'Role', columns.NAME_COL])
    st.session_state['df_car_groups'].loc[st.session_state['df_car_groups']['Role']==sort_val, 'Role'] = ''

    sheet = CAR_GROUP_WORKSHEET.format(day)
    cp_gsheet.update_sheet(gsheet['file'], sheet, st.session_state['df_car_groups'], gsheet['worksheets'],
                           color=gspread.utils.convert_colors_to_hex_value(green=1.0), 
                           index=0)
    st.session_state['is_balloon'] = random.randint(0,1)==1

    logging.info('Carpools exported')
    st.switch_page('7_success.py')