import re
import streamlit as st

import base_page
import cp_gsheet
from worksheets import ROSTER_WORKSHEET
import columns
from columns import NAME_COL

gsheet = base_page.setup(__file__)

# TODO: Update ROSTER_WORKSHEET to not have driver information

with st.spinner():
    df_roster = cp_gsheet.get_sheet(gsheet['file'], ROSTER_WORKSHEET, clean=True, 
                                    str_cols=[columns.HALF_DAY_COL, columns.GENERATION_COL, columns.EXPERIENCE_COL, columns.AFFILIATION_COL],
                                    name_cols=[NAME_COL])

no_name = df_roster[NAME_COL].apply(lambda x: len(x.strip())==0)
no_name = no_name[no_name]
for k in range(len(no_name)):
    df_roster.loc[no_name[k].index, NAME_COL] = f'UNNAMED {k}'

day_cols = [x for x in df_roster.columns if re.search(r'^Day\s\d+\s', x)]

st.session_state['day'] = cp_gsheet.set_day('NEXT', gsheet['worksheets'], len(day_cols))

st.subheader(f"Day {st.session_state['day']} Roster")
st.info(f'The below roster is correct if the "{ROSTER_WORKSHEET}" sheet  the Google spreadsheet is up-to-date. '+
        '\n\nIf is not, update it and press the "Reload Spreadsheet" button below.')

day_col = [x for x in df_roster.columns if x.startswith(f'Day {st.session_state['day']}')][0]

df_roster = df_roster[df_roster[day_col]].reset_index(drop=True)
st.session_state['df_roster'] = df_roster

col0, col1, col2 = st.columns(3)
if col0.button('Previous'):
    st.switch_page('1_get_url.py' if st.session_state['is_sample'] else '2_select_my_own_url.py')

col1.button('Reload Spreadsheet', help=f'Reload "{ROSTER_WORKSHEET}" tab from Google sheet (for example if changes were made)')

if col2.button('Accept Roster'):
    st.session_state['df_pairings'] = None
    st.switch_page('4_pairings.py')

st.dataframe(df_roster)