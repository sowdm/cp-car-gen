import os
import streamlit as st

def setup(cur_page, is_first_page=False):
    cur_page = os.path.basename(cur_page)

    gsheet = None
    if 'gsheet' in st.session_state:
        gsheet = st.session_state['gsheet']
    elif int(cur_page[0]) > 2 or cur_page[:2]=='2a':
        st.switch_page('1_get_url.py')

    if st.session_state['is_sample'] and not is_first_page:
        st.info(f"Sample spreadsheet can be viewed [here]({st.secrets['SAMPLE_URL']})")

    return gsheet

def navigation_buttons(ncols, prev_file, alt_prev_file=None, decision_key=None):
    cols = st.columns(2+ncols)
    if cols[0].button('Restart'):
        st.switch_page('1_get_url.py')

    if cols[1].button('Previous'):
        if alt_prev_file and decision_key:
            prev_file = prev_file if st.session_state[decision_key] else alt_prev_file
        st.switch_page(prev_file)

    return cols[2:]