import pandas as pd
import streamlit as st

import base_page
import cp_gsheet
from worksheets import FULL_ROSTER_WORKSHEET, CAR_GROUP_WORKSHEET

gsheet = base_page.setup(__file__)

types = [f'Has "{FULL_ROSTER_WORKSHEET}" sheet containing spreadsheet export from app', 'Initialization']
states = [gsheet['has_cp_export'], gsheet['is_init']]
is_complete = False
if gsheet['is_init']:
    ndays = len(gsheet['date_has_car_group'])
    for k in range(ndays):
        types.append(f'Day {k+1} Car Group')
        states.append(gsheet['date_has_car_group'][k])
    is_complete = sum(gsheet['date_has_car_group'])==ndays

st.subheader('Status of Google Sheet')
df = pd.DataFrame({'Step':types, 'Status':states})
st.dataframe(df)

if not gsheet['has_cp_export']:
    st.error(f'The spreadsheet at the requested URL must have the export of the roster from the CP app in a sheet called "{FULL_ROSTER_WORKSHEET}". '+
                    'Contact the administrator at the email below if you are not sure what this is.')
elif not gsheet['is_init']:
    st.info('The Google Sheet has not been *initialized*. Initialization will add sheets to the Google Sheet that will add 2 sheets:\n\n'+
                '1. Simplified roster sheet: Add any additional people and change which days people are canvassing here\n\n'+
                '2. Pairings sheet: Mark people who must or must NOT be paired together for specific days here\n\n'
                'Click button below to initialize')
    if st.button('Initialize'):
        cp_gsheet.init(gsheet)
        st.session_state['gsheet'] = cp_gsheet.get_spreadsheet(st.session_state['client'], st.session_state['url'])
else:
    avail_days = [k+1 for k,x in enumerate(gsheet['date_has_car_group']) if not x]
    nextday = [avail_days[0] if len(avail_days) else len(gsheet['date_has_car_group'])+1][0]
    st.markdown('*Hover over buttons for more information about each action*')
    col0, col1, col2, col3 = st.columns(4)

    if col0.button('Previous'):
        st.switch_page('1_get_url.py')

    if col1.button(f'Create Day {nextday} Car Group', disabled=is_complete, help=f'Generate car group for Day {nextday}'):
        st.switch_page('3_pairings.py')
        
    def del_car_group():
        sheet = CAR_GROUP_WORKSHEET.format(nextday-1)
        gsheet['file'].del_worksheet(gsheet['file'].worksheet(sheet))
        gsheet['date_has_car_group'][nextday-2] = False
        gsheet['worksheets'].remove(sheet)

    col2.button(f'Delete Day {nextday-1} Car Group', disabled=nextday<2, 
                help=f'Delete car group for Day {nextday-1}', on_click=del_car_group)

    def start_over():
        for w in [x for x in gsheet['worksheets'] if x!=FULL_ROSTER_WORKSHEET]:
            gsheet['file'].del_worksheet(gsheet['file'].worksheet(w))
        gsheet['worksheets'] = [x.title for x in gsheet['file'].worksheets()]
        gsheet['is_init'] = False

    col3.button(f'Re-Initialize', disabled=not gsheet['is_init'], 
                    help=f'Reset the spreadsheet. Remove all the auto-generated sheets except "{FULL_ROSTER_WORKSHEET}"', on_click=start_over)