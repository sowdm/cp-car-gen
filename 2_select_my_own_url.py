import streamlit as st

import base_page
import cp_gsheet
from worksheets import FULL_ROSTER_WORKSHEET

gsheet = base_page.setup(__file__)

st.subheader('Enter Google Sheet URL')

url = st.text_input('Google Sheet URL')

left,right = st.columns(2)

if left.button('Previous'):
    st.switch_page('1_get_url.py')

if right.button('Create Car Groups for This URL'):
    if len(url)==0:
        st.toast('ERROR: URL must be entered into Google Sheet URL textbox.', duration='long')
    else:
        with st.spinner():
            st.session_state['gsheet'], errmsg = cp_gsheet.load_url(st.session_state['client'], url)
        st.session_state['is_sample'] = False

        if errmsg:
            st.toast(errmsg, duration='long', icon='🚨')
        elif st.session_state['gsheet']['is_complete'] or st.session_state['gsheet']['car_group_date_error']:
            st.switch_page('2a_car_group_error.py')
        else:
            st.switch_page('3_roster.py')

st.subheader('How to Setup a Google Sheet to Generate Car Groups')

st.markdown(
    'To generator car groups for your trip, you must:\n\n' \
    '1. Create a [Google Spreadsheet](https://sheets.google.com/). Name it whatever you like.\n' \
    f'2. Create or rename a sheet to be called "**{FULL_ROSTER_WORKSHEET}**" (including the !). '\
        'See bar at bottom. Press + to add sheet or double click on sheet to rename.\n'
    '3. Go to your trip on the Common Power app.\n' \
    '4. Click "Export Trip Data to CSV"\n' \
    '5. Open the downloaded CSV.\n' \
    f'6. Copy the table and paste into your sheet named "**{FULL_ROSTER_WORKSHEET}** in your Google spreadsheet"\n'
    '7. In your Google spreadsheet, click the Share button in the upper right\n'
    "8. Enter this app's email **car-creator@common-power.iam.gserviceaccount.com** where it says 'Add People'. "
        "(NOTE: do not email the app. No one will receive it.)\n"
    "9. Ensure that the access level is **Editor** not Viewer or Commenter. This app needs to be able to add your car groups to your spreadsheet!\n"
    '10. Click Send.\n'
    '11. Click Share.\n'
    '12. Click Copy Link\n'
    '13. Enter copied URL in the text box'
            
)