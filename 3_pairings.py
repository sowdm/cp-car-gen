import re
import streamlit as st

import base_page
import cp_gsheet
from worksheets import ROSTER_WORKSHEET, PAIRINGS_WORKSHEET
from columns import NAME1_COL, NAME2_COL, PAIR_COL, SEPARATE_COL
from constants import MARK

gsheet = base_page.setup(__file__)

st.info('Input people who must OR must NOT be paired in the same car. This can also be done directly in the spreadsheet including for multiple days. ' \
        'although it requires restarting this process. Click Next to generate car groups.')

df_roster = cp_gsheet.get_sheet(gsheet['file'], ROSTER_WORKSHEET)
df_roster = df_roster.replace(MARK, True).replace("", False)
day_cols = [x for x in df_roster.columns if re.search(r'^Day\s\d+\s', x)]

df_pairings_full = cp_gsheet.get_sheet(gsheet['file'], PAIRINGS_WORKSHEET)
df_pairings_full = df_pairings_full.replace(MARK, True).replace("", False).replace('Yes', True).replace('yes', True).replace('No', False).replace('no', False)

ndays = len(day_cols)
st.session_state['day'] = cp_gsheet.set_day('NEXT', gsheet['worksheets'], ndays)

day_col = [x for x in df_pairings_full.columns if x.startswith(f'Day {st.session_state['day']}')][0]

for c in [day_col, PAIR_COL, SEPARATE_COL]:
    bad_vals = set(df_pairings_full[c].tolist()) - {True,False}
    if len(bad_vals):
        st.error(f'ERROR: Bad values found in column {c}: {bad_vals}')

df_pairings = df_pairings_full[df_pairings_full[day_col]].reset_index(drop=True) if len(df_pairings_full)>0 else df_pairings_full

for c in [NAME1_COL, NAME2_COL]:
    bad_vals = set(df_pairings_full[c].tolist()) - set(df_roster['Name'].tolist())
    if len(bad_vals):
        st.error(f'ERROR: Bad values found in column {c}: {bad_vals}')

df_roster = df_roster[df_roster[day_col]].reset_index(drop=True)

df_pairings = df_pairings[[NAME1_COL, NAME2_COL, PAIR_COL, SEPARATE_COL]]

# TODO: Add validation!!!

name_config = st.column_config.MultiselectColumn(options=df_roster['Name'])
pair_config = st.column_config.CheckboxColumn(help='Check if 2 people MUST be in the same car. Uncheck if 2 people must NOT be in the same car', default=True)
separate_config = st.column_config.CheckboxColumn(help='Check if people who must be in the same car must be in their own car without anyone else.', default=False)

df = st.data_editor(df_pairings, num_rows='dynamic', column_config={NAME1_COL:name_config, NAME2_COL:name_config, PAIR_COL:pair_config, SEPARATE_COL:separate_config})

col0, col1 = st.columns(2)
if col0.button('Previous'):
    st.switch_page('2_status.py')

if col1.button('Accept Pairings'):
    st.session_state['df_roster'] = df_roster
    # If new rows are added, they may contain a list of a string rather than just a string
    df[NAME1_COL] = df[NAME1_COL].apply(lambda x: x[0] if isinstance(x,list) and len(x)==1 else x)
    df[NAME2_COL] = df[NAME2_COL].apply(lambda x: x[0] if isinstance(x,list) and len(x)==1 else x)
    st.session_state['df_pairings'] = df
    st.session_state['df_car_groups'] = None
    st.switch_page('4_cargen.py')

st.subheader('Key')
st.text(f'Default data is pulled from "{PAIRINGS_WORKSHEET}" sheet of Google spreadsheet')
st.markdown(f'**{NAME1_COL} / {NAME2_COL}**: Names of volunteers who must OR must NOT be in the same car. Names '
            'must match people on the roster. To match more than 2 people, create a chain across multiple rows '
            '(i.e. Person 1 and Person 2 in Row 1 and Person 2 and Person 3 in Row will match Person 1-3)')
st.markdown(f'**{PAIR_COL}**: Checked (or Yes in the spreadsheet) = Put 2 people in the same car. Unchecked (or No in the spreadsheet) = Ensure 2 people are NOT in the same car')
st.markdown(f'**{SEPARATE_COL}**: Checked (or {MARK} in the spreadsheet) = Put group of people in a separate car (i.e. no one will be in the car group '
            'except people paired together here). Unchecked (or an empty cell in the spreadsheet) = Fill any remaining seats in the car for this group with other people.')
st.markdown(f'**Day Columns in Spreadsheet (not shown)**: Checked (or {MARK} in the spreadsheet) = Grouping is applicable to the corresponding day. '
            'Unchecked (or an empty cell in the spreadsheet) = Grouping constraint will not be applied to the corresponding day')
st.markdown('To add a new row, click on the empty row.')
st.markdown('To delete a row, select the empty column on the left of the row and then click the trash icon in the upper right of the table.')