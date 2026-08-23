import streamlit as st

import base_page
import constants
import cp_gsheet
from worksheets import FULL_ROSTER_WORKSHEET

base_page.setup(__file__, True)

st.info('Provide URL for generating cars or use Sample URL (Scroll down for Sample button)')

url = st.text_input('Google Sheet URL')

left,right = st.columns([1, 5])
if left.button('Use URL'):
    if len(url)==0:
        st.toast('ERROR: URL must be entered into Google Sheet URL textbox.')
    else:
        st.session_state['url'] = url.strip()
        st.session_state['gsheet'] = cp_gsheet.get_spreadsheet(st.session_state['client'], url)
        st.session_state['is_sample'] = False
        st.switch_page('2_status.py')

right.markdown(
    'To generator car groups for your trip, you must:\n\n' \
    '1. Create a [Google Sheet](https://sheets.google.com/)\n' \
    f'2. Create or rename a sheet to be called "**{FULL_ROSTER_WORKSHEET}**" (including the !). '\
        'See bar at bottom. Press + to add sheet or double click on sheet to rename.\n'
    '3. Go to your trip on the Common Power app.\n' \
    '4. Click "Export Trip Data to CSV"\n' \
    '5. Open the downloaded CSV.\n' \
    f'6. Copy the table and on Google sheets, paste into your sheet named "**{FULL_ROSTER_WORKSHEET}**"\n'
    f'7. Share the sheet with this app just like you would share it with another person. ' + 
        'Sharing MUST be done with **EDITOR ACCESS**! See instructions [here](https://support.google.com/a/users/answer/13309904?hl=en). ' \
        f'(A) If using "Share a spreadsheet with specific people" option, email [admin](mailto:{constants.EMAIL}) requesting the email to share with. ' +
            'Please include your CP Slack username in the email. '
        '(B) If using "Share a link to a spreadsheet" option, click Share button, change '
            '"General access" to "Anyone with the Link", change the Role from "Viewer" to "Editor".'
    f'8. Copy the shareable URL (not the one from your browser\'s Address Bar!!!). Click Share button. Then click Copy Link.'+
    '9. Enter copied URL in the text box above'
            
)

left,right = st.columns([1, 5])
SAMPLE_URL = 'Use Sample'
if left.button(SAMPLE_URL):
    st.session_state['url'] = st.secrets['SAMPLE_URL']
    st.session_state['gsheet'] = cp_gsheet.get_spreadsheet(st.session_state['client'], st.secrets['SAMPLE_URL'])
    assert st.session_state['gsheet']['has_cp_export'], 'ERROR: Sample spreadsheet does not have roster. This should not happen. Please report this issue.'
    st.session_state['is_sample'] = True
    st.switch_page('2_status.py')

right.markdown(f"If you don't have a Google Sheet URL and want to try out the generator with our [sample spreadsheet]({st.secrets['SAMPLE_URL']}), click **{SAMPLE_URL}** button")