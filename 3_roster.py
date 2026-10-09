import pandas as pd
import re
import streamlit as st

import base_page
import cp_gsheet
from worksheets import ROSTER_WORKSHEET, DRIVER_WORKSHEET
import columns
from columns import NAME_COL

gsheet = base_page.setup(__file__)

if st.session_state['load_roster']:
    with st.spinner():
        df_roster = cp_gsheet.get_sheet(gsheet['file'], ROSTER_WORKSHEET, clean=True, 
                                        str_cols=[columns.HALF_DAY_COL, columns.GENERATION_COL, columns.EXPERIENCE_COL, columns.AFFILIATION_COL,
                                                'MiniVan Experience', 'Dietary Restrictions'],
                                        name_cols=[NAME_COL])

        if 'Will Have Car On The Ground' not in df_roster:  # Check if deprecated roster spreadsheet
            st.session_state['gsheet'], errmsg = cp_gsheet.load_url(st.session_state['client'], gsheet['url'], reinit=True)
            df_roster = cp_gsheet.get_sheet(gsheet['file'], ROSTER_WORKSHEET, clean=True, 
                                                    str_cols=[columns.HALF_DAY_COL, columns.GENERATION_COL, columns.EXPERIENCE_COL, columns.AFFILIATION_COL,
                                                            'MiniVan Experience', 'Dietary Restrictions'],
                                                    name_cols=[NAME_COL])

    no_name = df_roster[NAME_COL].apply(lambda x: len(x.strip())==0)
    no_name = no_name[no_name]
    num_unnamed = 0
    for k in no_name.index:
        num_unnamed+=1
        df_roster.loc[k, NAME_COL] = f'UNNAMED {num_unnamed}'

    st.session_state['df_roster_full'] = df_roster

    day_cols = [x for x in df_roster.columns if re.search(r'^Day\s\d+\s', x)]

    st.session_state['day'] = cp_gsheet.set_day('NEXT', gsheet['worksheets'], len(day_cols))
else:
    df_roster = st.session_state['df_roster']
    day_cols = [x for x in df_roster.columns if re.search(r'^Day\s\d+\s', x)]

st.session_state['load_roster'] = False

st.header(f"Day {st.session_state['day']} Roster Setup")
st.info(f'The below roster is correct if the "{ROSTER_WORKSHEET}" tab of the Google spreadsheet is up-to-date. '+
        '\n\nIf is not, update it and press the "Reload Spreadsheet" button below.')

day_col = [x for x in df_roster.columns if x.startswith(f'Day {st.session_state['day']}')][0]

df_roster = df_roster[df_roster[day_col]].reset_index(drop=True)
st.session_state['df_roster'] = df_roster

col0, col1, col2, col3 = st.columns(4)
if col0.button('Previous'):
    st.switch_page('1_get_url.py' if st.session_state['is_sample'] else '2_select_my_own_url.py')

def reload():
    st.session_state['load_roster'] = True

col1.button('Reload Spreadsheet', help=f'Reload "{ROSTER_WORKSHEET}" tab from Google spreadsheet (for example if changes were made)', on_click=reload)

if col2.button('Learn About My Trip'):
    st.switch_page('3a_trip_stats.py')

if col3.button('Accept Roster'):
    update = len(st.session_state['select_skip_day'])>0 or len(st.session_state['select_never_arrived'])>0 or \
             len(st.session_state['select_add'])>0

    if update:
        df_drivers = cp_gsheet.get_sheet(gsheet['file'], DRIVER_WORKSHEET, clean=True, 
                                                numeric_cols=[columns.DRIVER_TYPE_COL],
                                                name_cols=[NAME_COL])
    for n in st.session_state['select_skip_day']:
        # Update local copies of roster
        st.session_state['df_roster_full'].loc[st.session_state['df_roster_full'][NAME_COL]==n, day_col] = False
        df_drivers.loc[df_drivers[NAME_COL]==n, day_col] = False
        drop = st.session_state['df_roster'][NAME_COL]==n
        st.session_state['df_roster'] = st.session_state['df_roster'].drop(index=drop[drop].index)

    for n in st.session_state['select_never_arrived']:
        # Update local copies of roster
        st.session_state['df_roster_full'].loc[st.session_state['df_roster_full'][NAME_COL]==n, day_cols] = False
        df_drivers.loc[df_drivers[NAME_COL]==n, day_cols] = False
        drop = st.session_state['df_roster'][NAME_COL]==n
        st.session_state['df_roster'] = st.session_state['df_roster'].drop(index=drop[drop].index)

    for n in st.session_state['select_add']:
        # Update local copies of roster
        st.session_state['df_roster_full'].loc[st.session_state['df_roster_full'][NAME_COL]==n, day_cols[st.session_state['day']-1:]] = True
        df_drivers.loc[df_drivers[NAME_COL]==n,  day_cols[st.session_state['day']-1:]] = True
        st.session_state['df_roster'] = pd.concat([st.session_state['df_roster'], 
                                                   st.session_state['df_roster_full'].loc[st.session_state['df_roster_full'][NAME_COL]==n]],
                                                   ignore_index=True)

    if update:
        cp_gsheet.update_sheet(gsheet['file'], ROSTER_WORKSHEET, st.session_state['df_roster_full'], gsheet['worksheets'])
        cp_gsheet.update_sheet(gsheet['file'], DRIVER_WORKSHEET, df_drivers, gsheet['worksheets'])
        cp_gsheet.update_trip_stats(st.session_state['df_roster_full'], day_cols, gsheet['file'], gsheet['worksheets'])

    # Reset index
    st.session_state['df_roster_full'] = st.session_state['df_roster_full'].reset_index(drop=True)
    st.session_state['df_roster'] = st.session_state['df_roster'].reset_index(drop=True)
    
    # Update spreadsheet
    st.session_state['ignore'] = []
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