import streamlit as st

import base_page
import cp_gsheet

base_page.setup(__file__, True)

st.header('Car Group Generator')

st.info('**This site will automatically create an initial draft of car groups for you.**\n\n' \
        'The first step is to select a Google Sheets URL that contains your roster.\n\n'
        'NOTE: you should always review the results to ensure they meet your needs and for factors that this methodology cannot account for!')

col1, col2 = st.columns(2)

if col1.button('I have a roster. I want to use my own Google Sheet.'):
    st.switch_page('2_select_my_own_url.py')

if col2.button('I want to use the example Google Sheet.'):
    with st.spinner():
        st.session_state['gsheet'], errmsg = cp_gsheet.load_url(st.session_state['client'], st.secrets['SAMPLE_URL'])
    assert not errmsg, 'ERROR: Sample spreadsheet does not have roster. This should not happen. Please report this issue.'
    st.session_state['is_sample'] = True
    if st.session_state['gsheet']['is_complete'] or st.session_state['gsheet']['car_group_date_error']:
        st.switch_page('2a_car_group_error.py')
    else:
        st.switch_page('3_roster.py')