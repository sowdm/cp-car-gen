import streamlit as st

import base_page
from worksheets import CAR_GROUP_WORKSHEET

gsheet = base_page.setup(__file__)

if 'are_you_sure' not in st.session_state:
    st.session_state['are_you_sure'] = False

if st.session_state['are_you_sure']:
    st.header('Are You Sure?')
    st.text('This will permanently delete sheets from your Google Spreadsheet')
    left, right = st.columns(2)
    if left.button('No'):
        st.session_state['are_you_sure'] = False
        st.rerun()
    elif right.button('Yes'):
        st.session_state['are_you_sure'] = False
        for k in range(len(gsheet['dates'])):
            w = CAR_GROUP_WORKSHEET.format(k+1)
            if w in gsheet['worksheets']:
                gsheet['file'].del_worksheet(gsheet['file'].worksheet(w))
        st.switch_page('1_get_url.py')

    st.stop()

delete_msg = 'DELETE ALL CAR GROUPS'
if st.session_state['gsheet']['is_complete']:
    st.header('Car groups have already been generated for all days!')
    st.warning(f'You may remove ALL car groups from the Google Spreadsheet and start over by clicking "{delete_msg}"')
else:
    st.header('**ERROR FOUND!** There is a gap in the days that have car groups created in the spreadsheet.')
    st.warning(f'Fix manually in the spreadsheet or you may remove ALL car groups and start over by clicking "{delete_msg}"')

left, right = st.columns(2)

if left.button('Previous'):
    if st.session_state['is_sample']:
        st.switch_page('1_get_url.py')
    else:
        st.switch_page('2_select_my_own_url.py')

if right.button(f'DELETE ALL CAR GROUPS', help=f'Reset the spreadsheet. Remove all the auto-generated car groups sheets'):
    st.session_state['are_you_sure'] = True
    st.rerun()