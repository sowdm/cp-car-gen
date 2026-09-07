import gspread
import pandas as pd
import random
import streamlit as st

import base_page
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
st.dataframe(st.session_state['df_car_groups'], width='content')

if col0.button('Previous'):
    st.switch_page('5_drivers.py')

if col2.button(f'Export Day {day} Car Group to Google Spreadsheet'):
    sheet = CAR_GROUP_WORKSHEET.format(day)
    cp_gsheet.update_sheet(gsheet['file'], sheet, st.session_state['df_car_groups'], gsheet['worksheets'],
                           color=gspread.utils.convert_colors_to_hex_value(green=1.0), 
                           index=0)
    st.session_state['is_balloon'] = random.randint(0,1)==1
    st.switch_page('7_success.py')