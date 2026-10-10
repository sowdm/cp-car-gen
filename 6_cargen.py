import gspread
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

col0, col1, col2 = st.columns(3)
day = st.session_state['day']
if col1.button('Re-Generate Car Groups'):
    st.session_state['df_car_groups'] = None
    
if not isinstance(st.session_state['df_car_groups'], pd.DataFrame):
    pbar = st.progress(0.0, 'Simulating Car Groups...')
    st.session_state['df_car_groups'] =st.session_state['cargen'].gen_car_groups(pbar)
    pbar.empty()

st.subheader('Generated Car Groups')

st.info('To re-arrange car pools, drag and drop between lists. Click Export button when complete.\n\n' \
        '**Generations**: S = Silent Generation, B = Boomer, X = Gen X, M = Millenial, Z = Gen Z\n\n' \
        '**Experience**: E0 = None, E1 = A little w/o CP, E2 = A lot w/o CP, E3 = A little w/ CP, E4 = A lot w/ CP\n\n' \
        'Action = Action Academy Student or Graduate')
# TODO: Add swap function

car_sizes = st.session_state['df_car_groups']['Car'].value_counts()
min_car_size = car_sizes.min()
max_car_size = car_sizes.max()

container = st.container()

car_groups = []
for car in st.session_state['df_car_groups']['Car'].unique():
    m = st.session_state['df_car_groups']['Car']==car
    car_groups.append({'header':f'Car {car}', 'items':[]})
    for row in st.session_state['df_car_groups'].loc[m].iterrows():
        row = row[1]
        gen = row[columns.GENERATION_COL]
        if (m:=re.search('Gen ([A-Z])', gen, flags=re.IGNORECASE)):
            gen = m.groups()[0]
        elif 'millenial' in gen.lower():
            gen = 'M'
        elif 'boomer' in gen.lower():
            gen = 'B'
        elif 'silent' in gen.lower():
            gen = 's'
        name = f'{row[columns.NAME_COL]} ({gen}'

        exp = columns.EXPERIENCE_COL.lower()
        if 'with cp' in columns.EXPERIENCE_COL:
            if 'a lot' in exp:
                exp = 4
            else:
                exp = 3
        elif 'a lot' in exp:
            exp = 2
        elif 'none' in exp:
            exp = 0
        else:
             exp = 1

        name+=f', E{exp}'

        if row[columns.BIPOC_COL].lower()=='yes':
            name+=', BIPOC'

        if row[columns.AFFILIATION_COL].lower() not in ['','n/a','none']:
            affil = re.sub(r'\(.+\)', '', row[columns.AFFILIATION_COL])
            if 'action academy' in affil.lower():
                affil = 'Action'
            name+=', ' + affil

        name+=')'

        car_groups[-1]['items'].append(name)

selection = sort_items(car_groups, multi_containers=True, direction='horizontal')

req_car_sizes = [len(x['items']) for x in selection]
if min(req_car_sizes) < min_car_size or max(req_car_sizes) > max_car_size:
    with container:
        st.warning(f'One or more carpools has fewer/more volunteers than the minimum/maximum expected ({min_car_size}/{max_car_size}). ' +\
                   'This is allowable but please review to ensure it is desired!')

if col0.button('Previous'):
    st.switch_page('5_drivers.py')

if col2.button(f'Export Day {day} Car Group to Google Spreadsheet'):
    for k in range(len(selection)):
        names = [re.sub(r'\s\(.*\)', '', x) for x in selection[k]['items']]
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
    st.switch_page('7_success.py')