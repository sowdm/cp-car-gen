import pandas as pd
import streamlit as st
import uuid

import base_page
import cp_gsheet
from worksheets import PAIRINGS_WORKSHEET
from columns import NAME1_COL, NAME2_COL, PAIR_COL, SEPARATE_COL, NAME_COL
from generator import CarGenerator

gsheet = base_page.setup(__file__)

st.subheader('Select people who you want to be in the same car (Pair=Yes) or in different cars (Pair=No)')
st.text('All others will be assigned randomly')

st.info('1. Input people who must OR must NOT be paired in the same car. For groups larger than 2, use multiple rows.\n' \
        '2. Set Pair=Yes to put in same car and Pair=No to put in different cards\n' \
        '3. If Pair=Yes, set Separate Car=Yes to put the group in a separate car (i.e. no one else will be randomly assigned to the car)\n\n' \
        'Pairings can be set across multiple days in the Google Sheet. See instructions below table.')

if 'reload_pairs' not in st.session_state:
    st.session_state['reload_pairs'] = True

df_roster = st.session_state['df_roster']
if not st.session_state['reload_pairs'] and isinstance(st.session_state['df_roster'], pd.DataFrame):
    df_pairings = st.session_state['df_pairings']
else:
    df_pairings_full = cp_gsheet.get_sheet(gsheet['file'], PAIRINGS_WORKSHEET, clean=True, str_cols=[NAME1_COL, NAME2_COL])

    day_col = [x for x in df_pairings_full.columns if x.startswith(f'Day {st.session_state['day']}')][0]
    df_pairings = df_pairings_full[df_pairings_full[day_col]].reset_index(drop=True) if len(df_pairings_full)>0 else df_pairings_full
    df_pairings = df_pairings[[NAME1_COL, NAME2_COL, PAIR_COL, SEPARATE_COL]]

    # Remove pairings where either person is not here
    keep = df_pairings[NAME1_COL].isin(df_roster[NAME_COL]) & df_pairings[NAME2_COL].isin(df_roster[NAME_COL])
    df_pairings = df_pairings[keep]

    st.session_state['df_pairings'] = df_pairings
    st.session_state['reload_pairs'] = False
    st.session_state['pairings_key'] = uuid.uuid4()

# TODO: Add validation of rows!!!

name_config = st.column_config.SelectboxColumn(options=df_roster['Name'].tolist())
pair_config = st.column_config.CheckboxColumn(help='Check if 2 people MUST be in the same car. Uncheck if 2 people must NOT be in the same car', default=True)
separate_config = st.column_config.CheckboxColumn(help='Check if people who must be in the same car must be in their own car without anyone else.', default=False)

df = st.data_editor(df_pairings, num_rows='dynamic', key=st.session_state['pairings_key'],
                    column_config={NAME1_COL:name_config, NAME2_COL:name_config, PAIR_COL:pair_config, SEPARATE_COL:separate_config})

st.markdown('**TIP**: To add a new row, click on the empty row.')
st.markdown('**TIP**: To delete a row, select the empty column on the left of the row and then click the trash icon in the upper right of the table.')

col0, col1, col2 = st.columns(3)
if col0.button('Previous'):
    st.switch_page('3_roster.py')

def reload():
    st.session_state['reload_pairs'] = True

col1.button('Reload Spreadsheet', on_click=reload, 
            help=f'Reload "{PAIRINGS_WORKSHEET}" tab from Google sheet (for example if changes were made)')

if col2.button('Accept Pairings'):
    # If new rows are added, they may contain a list of a string rather than just a string
    df[NAME1_COL] = df[NAME1_COL].apply(lambda x: x[0] if isinstance(x,list) and len(x)==1 else x)
    df[NAME2_COL] = df[NAME2_COL].apply(lambda x: x[0] if isinstance(x,list) and len(x)==1 else x)
    st.session_state['drivers'] = None
    st.session_state['df_car_groups'] = None
    st.session_state['cargen'] = CarGenerator(df_roster, df, st.session_state['day'], gsheet, st.session_state['config'])
    st.switch_page('5_drivers.py')

st.subheader('Importable Pairings')
st.text(f'The default pairings shown here are from "{PAIRINGS_WORKSHEET}" sheet of Google spreadsheet. '+
        f'Pairings set up in the "{PAIRINGS_WORKSHEET}" sheet can be created for multiple days. See below for how to populate the table:')
st.markdown(f'**{NAME1_COL} / {NAME2_COL}**: Names of volunteers who must OR must NOT be in the same car. Names '
            'must match people on the roster. To match more than 2 people, create a chain across multiple rows '
            '(i.e. Person 1 and Person 2 in Row 1 and Person 2 and Person 3 in Row will group Persons 1-3)')
st.markdown(f'**{PAIR_COL}**: Yes = Put 2 people in the same car. No = Put 2 people in different cars.')
st.markdown(f'**{SEPARATE_COL}**: Yes = Put group of people in a separate car (i.e. no one will be in the car group '
            'except people paired together here). No or leave empty to fill any remaining seats in the car.')
st.markdown(f'Put an X in any **Day Columns in Spreadsheet (not shown)**for days that you want the pairing to be used.')