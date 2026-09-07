import streamlit as st

import base_page

base_page.setup(__file__)
st.header('Please review the results! Car group has successfully been exported to Google Sheet.')

st.text('Click "Start Over" to add car groups for the next day.')

left, right = st.columns(2)   

if left.button('Start Over'):
    st.switch_page('1_get_url.py')

if right.button('I Like Balloons' if st.session_state['is_balloon'] else 'Make It Snow'):
    if st.session_state['is_balloon']:
        st.balloons()
    else:
        st.snow()