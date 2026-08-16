import pandas as pd
import streamlit as st

import base_page
import cp_gsheet
import generator
from worksheets import CAR_GROUP_WORKSHEET

gsheet = base_page.setup(__file__)

col0, col1, col2 = st.columns(3)
day = st.session_state['day']
if col1.button('Re-Generate Car Groups'):
    st.session_state['df_car_groups'] = None
    
if not isinstance(st.session_state['df_car_groups'], pd.DataFrame):
    st.session_state['df_car_groups'] =generator.gen_car_groups(st.session_state['df_roster'], st.session_state['df_pairings'], 
                                                                day, gsheet, st.session_state['config'])

st.subheader('Generated Car Groups')
st.dataframe(st.session_state['df_car_groups'], width='content')

if col0.button('Previous'):
    st.switch_page('3_pairings.py')

if col2.button('Accept Car Groups', help='Export car groups to Google sheet'):
    sheet = CAR_GROUP_WORKSHEET.format(day)
    cp_gsheet.update_sheet(gsheet['file'], sheet, st.session_state['df_car_groups'], gsheet['worksheets'])
    st.switch_page('5_success.py')