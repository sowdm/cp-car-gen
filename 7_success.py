import streamlit as st

import base_page

base_page.setup(__file__)
st.success('Car group has successfully been imported to Google Sheet.\n\n' \
    'Click "Start Over" to add car groups for the next day or make other updates to a Google Sheet.')

if st.button('Start Over'):
    st.switch_page('1_get_url.py')