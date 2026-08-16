import inspect
import os
import streamlit as st

def setup(cur_page, is_first_page=False):
    cur_page = os.path.basename(cur_page)

    gsheet = None
    if 'gsheet' in st.session_state:
        gsheet = st.session_state['gsheet']
    elif not cur_page.startswith('1'):
        st.switch_page('1_get_url.py')

    if st.session_state['is_sample'] and not is_first_page:
        st.info(f"Sample spreadsheet can be viewed [here]({st.secrets['SAMPLE_URL']})")

    return gsheet