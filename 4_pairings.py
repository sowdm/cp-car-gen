import pandas as pd
import streamlit as st

import base_page
from columns import NAME1_COL, NAME2_COL, PAIR_COL, SEPARATE_COL, SAME_CAR, DIFFERENT_CAR
from generator import CarGenerator

gsheet = base_page.setup(__file__)

st.subheader('Are there people you want to be in the same car? Or people you want to keep in separate cars?')

st.info('1. Create a new row by clicking the empty row in the table below\n' \
        '2. Add names of 2 volunteers who you want in the same car or different cars. For groups larger than 2, use multiple rows.\n' \
        '3. Indicate whether you want them in the same car or different cards\n' \
        f'4. If a group that will be in a separate car, indicate "Yes" in the "{SEPARATE_COL} column\n' \
        '5. Repeat as needed\n' \
        '6. Click "Accept Pairings" when complete' \
        )
st.markdown('**TIP**: To delete a row, select the empty column on the left of the row and then click the trash icon in the upper right of the table.')

df_roster = st.session_state['df_roster']

# TODO: Add validation of rows!!!

df_pairings = st.session_state['df_pairings'] if isinstance(st.session_state['df_pairings'], pd.DataFrame) else pd.DataFrame(columns=[NAME1_COL, NAME2_COL, PAIR_COL, SEPARATE_COL])

col0, col1 = st.columns(2)

name_config = st.column_config.SelectboxColumn(options=df_roster['Name'].tolist())
pair_config = st.column_config.SelectboxColumn(options=[SAME_CAR, DIFFERENT_CAR], 
                                               help=f'Mark "{SAME_CAR}" if 2 people MUST be in the same car. '
                                               'Mark "{DIFFERENT_CAR}" if 2 people must NOT be in the same car', default=SAME_CAR)
separate_config = st.column_config.SelectboxColumn(options=['Yes','No'],
                                                   help='Check if group of people who must be in the same car must also be in their own car '
                                                   'without anyone else.', 
                                                   default='No')

df = st.data_editor(df_pairings, num_rows='dynamic', 
                    column_config={NAME1_COL:name_config, NAME2_COL:name_config, PAIR_COL:pair_config, SEPARATE_COL:separate_config})

disabled = (df[NAME1_COL] == df[NAME2_COL]).any()
if disabled:
    st.warning(f'ERROR: a row exists with the same name in {NAME1_COL} and {NAME2_COL} columns. Please correct!')

if col0.button('Previous'):
    st.switch_page('3_roster.py')

if col1.button('Accept Pairings', disabled=disabled):
    # If new rows are added, they may contain a list of a string rather than just a string
    st.session_state['drivers'] = None
    st.session_state['df_car_groups'] = None
    st.session_state['df_pairings'] = df.copy()
    df[PAIR_COL] = df[PAIR_COL] == SAME_CAR
    df[SEPARATE_COL] = df[SEPARATE_COL].str.lower() == 'yes'
    st.session_state['cargen'] = CarGenerator(df_roster, df, st.session_state['day'], gsheet, st.session_state['config'])
    st.switch_page('5_drivers.py')