import re
import streamlit as st

import base_page
import cp_gsheet
from worksheets import ROSTER_WORKSHEET
import columns
from columns import NAME_COL

gsheet = base_page.setup(__file__)

st.subheader("Today's Roster")

# TODO: Update ROSTER_WORKSHEET to not have driver information

st.info(f'The below roster is correct if the "{ROSTER_WORKSHEET}" of the Google sheet is up-to-date. '+
        '\n\nIf is not, update it and press the "Reload Spreadsheet" button below')

df_roster = cp_gsheet.get_sheet(gsheet['file'], ROSTER_WORKSHEET, clean=True, 
                                str_cols=[NAME_COL, columns.HALF_DAY_COL, columns.GENERATION_COL, columns.EXPERIENCE_COL, columns.AFFILIATION_COL])
day_cols = [x for x in df_roster.columns if re.search(r'^Day\s\d+\s', x)]

st.session_state['day'] = cp_gsheet.set_day('NEXT', gsheet['worksheets'], len(day_cols))

day_col = [x for x in df_roster.columns if x.startswith(f'Day {st.session_state['day']}')][0]

df_roster = df_roster[df_roster[day_col]].reset_index(drop=True)
st.session_state['df_roster'] = df_roster

col0, col1, col2 = st.columns(3)
if col0.button('Previous'):
    st.switch_page('2_status.py')

col1.button('Reload Spreadsheet', help=f'Reload "{ROSTER_WORKSHEET}" tab from Google sheet (for example if changes were made)')

if col2.button('Accept Roster'):
    st.switch_page('4_pairings.py')


st.dataframe(df_roster)