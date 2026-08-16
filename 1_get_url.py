import streamlit as st

import base_page
import cp_gsheet
from worksheets import FULL_ROSTER_WORKSHEET

base_page.setup(__file__, True)

url = st.text_input('Google Sheet URL')

left,right = st.columns([1, 5])
if left.button('Use URL'):
    if len(url)==0:
        st.toast('ERROR: URL must be entered into Google Sheet URL textbox.')
    else:
        st.session_state['url'] = url
        st.session_state['gsheet'] = cp_gsheet.get_spreadsheet(st.session_state['client'], url)
        st.session_state['is_sample'] = False
        st.switch_page('2_status.py')

right.markdown(f'*Google Sheet should contain the CP roster export spreadsheet in a sheet called "**{FULL_ROSTER_WORKSHEET}**" (including the !). '+
            'This spreadsheet MUST be [shared with Editor access](https://support.google.com/a/users/answer/13309904?hl=en) with the email address provided to you. '+
            'If no email has been provided to you, request the email on Slack.*')

left,right = st.columns([1, 5])
SAMPLE_URL = 'Use Sample'
if left.button(SAMPLE_URL):
    st.session_state['url'] = st.secrets['SAMPLE_URL']
    st.session_state['gsheet'] = cp_gsheet.get_spreadsheet(st.session_state['client'], st.secrets['SAMPLE_URL'])
    assert st.session_state['gsheet']['has_cp_export'], 'ERROR: Sample spreadsheet does not have roster. This should not happen. Please report this issue.'
    st.session_state['is_sample'] = True
    st.switch_page('2_status.py')

right.markdown(f"If you don't have a Google Sheet URL and want to try out the generator with our [sample spreadsheet]({st.secrets['SAMPLE_URL']}), click **{SAMPLE_URL}** button")