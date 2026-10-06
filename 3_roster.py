import pandas as pd
import re
import streamlit as st

import base_page
import cp_gsheet
from worksheets import ROSTER_WORKSHEET
import columns
from columns import NAME_COL

gsheet = base_page.setup(__file__)

if st.session_state['load_roster']:
    with st.spinner():
        df_roster = cp_gsheet.get_sheet(gsheet['file'], ROSTER_WORKSHEET, clean=True, 
                                        str_cols=[columns.HALF_DAY_COL, columns.GENERATION_COL, columns.EXPERIENCE_COL, columns.AFFILIATION_COL,
                                                'MiniVan Experience', 'Dietary Restrictions'],
                                        name_cols=[NAME_COL])

    no_name = df_roster[NAME_COL].apply(lambda x: len(x.strip())==0)
    no_name = no_name[no_name]
    for k in no_name.index:
        df_roster.loc[k, NAME_COL] = f'UNNAMED {k}'

    st.session_state['df_roster_full'] = df_roster

    day_cols = [x for x in df_roster.columns if re.search(r'^Day\s\d+\s', x)]

    st.session_state['day'] = cp_gsheet.set_day('NEXT', gsheet['worksheets'], len(day_cols))
else:
    df_roster = st.session_state['df_roster']
    day_cols = [x for x in df_roster.columns if re.search(r'^Day\s\d+\s', x)]

st.session_state['load_roster'] = False

st.header(f"Day {st.session_state['day']} Roster Setup")
st.info(f'The below roster is correct if the "{ROSTER_WORKSHEET}" sheet  the Google spreadsheet is up-to-date. '+
        '\n\nIf is not, update it and press the "Reload Spreadsheet" button below.')

day_col = [x for x in df_roster.columns if x.startswith(f'Day {st.session_state['day']}')][0]

df_roster = df_roster[df_roster[day_col]].reset_index(drop=True)
st.session_state['df_roster'] = df_roster

col0, col1, col2, col3 = st.columns(4)
if col0.button('Previous'):
    st.switch_page('1_get_url.py' if st.session_state['is_sample'] else '2_select_my_own_url.py')

def reload():
    st.session_state['load_roster'] = True

col1.button('Reload Spreadsheet', help=f'Reload "{ROSTER_WORKSHEET}" tab from Google sheet (for example if changes were made)', on_click=reload)

if col2.button('Learn About My Trip'):
    st.switch_page('3a_trip_stats.py')

if col3.button('Accept Roster'):
    for n in st.session_state['select_skip_day']:
        # Update local copies of roster
        st.session_state['df_roster_full'].loc[st.session_state['df_roster_full'][NAME_COL]==n, day_col] = False
        drop = st.session_state['df_roster'][NAME_COL]==n
        st.session_state['df_roster'] = st.session_state['df_roster'].drop(index=drop[drop].index)

    for n in st.session_state['select_never_arrived']:
        # Update local copies of roster
        st.session_state['df_roster_full'].loc[st.session_state['df_roster_full'][NAME_COL]==n, day_cols] = False
        drop = st.session_state['df_roster'][NAME_COL]==n
        st.session_state['df_roster'] = st.session_state['df_roster'].drop(index=drop[drop].index)

    for n in st.session_state['select_add']:
        # Update local copies of roster
        st.session_state['df_roster_full'].loc[st.session_state['df_roster_full'][NAME_COL]==n, day_cols[st.session_state['day']-1:]] = True
        st.session_state['df_roster'] = pd.concat([st.session_state['df_roster'], 
                                                   st.session_state['df_roster_full'].loc[st.session_state['df_roster_full'][NAME_COL]==n]],
                                                   ignore_index=True)

    cp_gsheet.update_sheet(gsheet['file'], ROSTER_WORKSHEET, st.session_state['df_roster_full'], gsheet['worksheets'])
    st.stop()

    # Reset index
    st.session_state['df_roster_full'] = st.session_state['df_roster_full'].reset_index(drop=True)
    st.session_state['df_roster'] = st.session_state['df_roster'].reset_index(drop=True)
    
    # Update spreadsheet
    st.session_state['df_pairings'] = None
    st.switch_page('4_pairings.py')

st.subheader('Roster Modifications')
st.text('Modifications take effect and update spreadsheet when "Accept Roster" is clicked')
st.multiselect(f"Volunteers Who Will Not Be in a Car on Day {st.session_state['day']} (e.g. staying at the hotel)", df_roster[NAME_COL], 
               key='select_skip_day', on_change='ignore')
st.multiselect(f"Volunteers to Remove from Carpool Today and In the Future (e.g. never arrived)", df_roster[NAME_COL],
               key='select_never_arrived', on_change='ignore')
st.multiselect(f"Volunteers to Add to Day {st.session_state['day']} and remaining days (e.g. arrived early)", 
                set(st.session_state['df_roster_full'][NAME_COL]) - set(df_roster[NAME_COL]),
                key='select_add', on_change='ignore')

st.subheader('Roster')
st.dataframe(df_roster)