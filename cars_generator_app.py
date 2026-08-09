import pandas as pd
import re
import streamlit as st
from streamlit_gsheets import GSheetsConnection
import tomllib

import cp_gsheet
import generator
from worksheets import FULL_ROSTER_WORKSHEET, PAIRINGS_WORKSHEET, ROSTER_WORKSHEET, CAR_GROUP_WORKSHEET
from columns import NAME1_COL, NAME2_COL, PAIR_COL, SEPARATE_COL
from constants import MARK

# TODO: Overwrite vs. Next
# TODO: Add ability to delete car groups
# TODO: Add summary screen indicating status of spreadsheet
# TODO: Create timeline of when people are present including half-day status
# TODO: Add ability to change config and import/export config

GET_URL_PAGE = 'file'
NO_CP_EXPORT_PAGE = 'no export'
STATUS_PAGE = 'status'
CLEAR_SAMPLE_PAGE = 'sample'
INIT_PAGE = 'init'
PAIRINGS_PAGE = 'pairings'
CAR_GEN_PAGE = 'car gen'
SUCCESS_PAGE = 'success'
PAGES = [GET_URL_PAGE, NO_CP_EXPORT_PAGE, STATUS_PAGE, CLEAR_SAMPLE_PAGE, INIT_PAGE, PAIRINGS_PAGE, CAR_GEN_PAGE, SUCCESS_PAGE]
SAMPLE_URL = 'Use Sample'
NO_NEXT = [GET_URL_PAGE, NO_CP_EXPORT_PAGE, CAR_GEN_PAGE]

st.warning('This is a BETA version of this test. Thank you for testing it, and we hope you find it useful. ' \
    'If you encounter any issues, please contact [admin](mailto:openpolicedata@gmail.com).')


if 'cur_page' not in st.session_state:
    st.session_state['cur_page'] = GET_URL_PAGE
    st.session_state['is_sample'] = False
    st.session_state['page_history'] = []
    conn = st.connection("gsheets", type=GSheetsConnection)
    st.session_state['client'] = conn.client._client
    with open('config.txt') as f:
        st.session_state['config'] = tomllib.load(f)

cur_page = st.session_state['cur_page']

if 'gsheet' in st.session_state:
    gsheet = st.session_state['gsheet']

if cur_page not in st.session_state['page_history']:
    st.session_state['page_history'].append(cur_page)

if st.session_state['is_sample'] and cur_page!=GET_URL_PAGE:
    st.info(f"Sample spreadsheet can be viewed [here]({st.secrets['SAMPLE_URL']})")

st.set_page_config(
    page_title="Car Generator",
    initial_sidebar_state="auto",
    layout = 'wide',
    menu_items={
        'Report a Bug': "mailto:openpolicedata@gmail.com"
    }
)

page_idx = PAGES.index(cur_page)

show_prev = show_next = False
next_on_click = None

if cur_page == GET_URL_PAGE:
    url = st.text_input('Google Sheet URL')

    def set_url():
        st.session_state['gsheet'] = cp_gsheet.get_spreadsheet(st.session_state['client'], url)
        if not st.session_state['gsheet']['has_cp_export']:
            st.session_state['cur_page'] = NO_CP_EXPORT_PAGE
        else:
            st.session_state['cur_page'] = PAIRINGS_PAGE if st.session_state['gsheet']['is_init'] else INIT_PAGE
        st.session_state['is_sample'] = False

    left,right = st.columns([1, 5])
    left.button('Use URL', on_click=set_url)
    right.markdown(f'*Google Sheet should contain the CP roster export spreadsheet in a sheet called "**{FULL_ROSTER_WORKSHEET}**" (including the !). '+
                'This spreadsheet MUST be [shared with Editor access](https://support.google.com/a/users/answer/13309904?hl=en) with the email address provided to you. '+
                'If no email has been provided to you, request the email on Slack.*')
    
    def use_sample():
        st.session_state['gsheet'] = cp_gsheet.get_spreadsheet(st.session_state['client'], st.secrets['SAMPLE_URL'])
        assert st.session_state['gsheet']['has_cp_export'], 'ERROR: Sample spreadsheet does not have roster. This should not happen. Please report this issue.'
        st.session_state['cur_page'] = CLEAR_SAMPLE_PAGE if st.session_state['gsheet']['is_init'] else INIT_PAGE
        st.session_state['is_sample'] = True

    left,right = st.columns([1, 5])
    left.button(SAMPLE_URL, on_click=use_sample)
    right.markdown(f"If you don't have a Google Sheet URL and want to try out the generator with our [sample spreadsheet]({st.secrets['SAMPLE_URL']}), click **{SAMPLE_URL}** button")
elif cur_page==STATUS_PAGE:
    types = {f'Has {FULL_ROSTER_WORKSHEET}', 'Is Initialized'}
    states = [gsheet['has_cp_export'], gsheet['is_init']]
    if gsheet['is_init']:
        ndays = len(gsheet['date_has_car_group'])
        for k in range(types):
            types.append(f'Has Day {k+1} Car Group')
            states.append(gsheet['date_has_car_group'][k])

    df = pd.DataFrame()

    # TODO: Text saying hover over buttons to take action
    # TODO: Button to continue
    # TODO: Buttons: Delete most recent car group. Re-initialize.
elif cur_page == NO_CP_EXPORT_PAGE:
    st.warning(f'The spreadsheet at the requested URL must have the export of the roster from the CP app in a sheet called "{FULL_ROSTER_WORKSHEET}". '+
                'Contact the administrator at the email below if you are not sure what this is.')
elif cur_page == CLEAR_SAMPLE_PAGE:
    show_prev = True
    car_group_days = [k for k,x in enumerate(gsheet['date_has_car_group']) if x]
    if gsheet['car_group_date_error']:
        st.error(f'There are gaps between days with existing car groups in the sample spreadsheet. The following days have car groups: {car_group_days}. '+
                    'This should not happen with the sample spreadsheet. Please report to the administrator at the email below.')
    else:
        disable_continue = False
        if len(car_group_days)==0:
            msg = 'Sample spreadsheet has been initialized but there are no car groups set up.'
        elif len(car_group_days)==len(gsheet['date_has_car_group']):
            msg = f"Car groups for all {len(car_group_days)} have been completd. Please click Start Over button if you'd like to work with the sample spreadsheet."
            disable_continue = True
        else:
            msg = f"Car groups for {len(car_group_days)} of {len(gsheet['date_has_car_group'])} days have been completed."

        st.info('The sample spreadsheet has already been started by you or someone else. '+msg+' You can pick up where they left off or start over.')
        left,right = st.columns(2)

        def start_over():
            for w in [x for x in gsheet['worksheets'] if x!=FULL_ROSTER_WORKSHEET]:
                gsheet['file'].del_worksheet(gsheet['file'].worksheet(w))
            gsheet['worksheets'] = [x.title for x in gsheet['file'].worksheets()]
            gsheet['is_init'] = False
            st.session_state['cur_page'] = INIT_PAGE
        
        def cont():
            st.session_state['cur_page'] = PAIRINGS_PAGE

        left.button('Start Over', on_click=start_over)
        right.button('Continue', on_click=cont, disabled=disable_continue)
elif cur_page==INIT_PAGE:
    show_prev = True
    show_next = True
    st.info('The Google Sheet has not been *initialized*. Initialization will add sheets to the Google Sheet that will add 2 sheets:\n\n'+
            '1. Simplified roster sheet: Add any additional people and change which days people are canvassing here\n\n'+
            '2. Pairings sheet: Mark people who must or must NOT be paired together for specific days here\n\n'
            'Click next to initialize')
    
    def init_spreadsheet():
        cp_gsheet.init(gsheet)
        
    next_on_click = init_spreadsheet
elif cur_page==PAIRINGS_PAGE:
    st.info('Input people who must OR must NOT be paired in the same car. This can also be done directly in the spreadsheet including for multiple days. ' \
        'although it requires restarting this process. Click Next to generate car groups.')

    df_roster = cp_gsheet.get_sheet(gsheet['file'], ROSTER_WORKSHEET)
    df_roster = df_roster.replace(MARK, True)

    df_pairings_full = cp_gsheet.get_sheet(gsheet['file'], PAIRINGS_WORKSHEET)
    day_cols = [x for x in df_pairings_full.columns if re.search(r'^Day\s\d+\s', x)]
    df_pairings_full = df_pairings_full.replace(MARK, True)

    ndays = len(day_cols)
    st.session_state['day'] = cp_gsheet.set_day('NEXT', gsheet['worksheets'], ndays)

    day_col = [x for x in df_pairings_full.columns if x.startswith(f'Day {st.session_state['day']}')][0]
    df_pairings = df_pairings_full[df_pairings_full[day_col]].reset_index(drop=True)

    df_roster = df_roster[df_roster[day_col]].reset_index(drop=True)

    # TODO: Only keep people in roster? Is it better to show with some sort of error???
    # df_pairings = df_pairings[df_pairings[NAME1_COL].isin(df_roster['Name']) & df_pairings[NAME2_COL].isin(df_roster['Name'])]

    df_pairings = df_pairings[[NAME1_COL, NAME2_COL, PAIR_COL, SEPARATE_COL]]

    name_config = st.column_config.MultiselectColumn(options=df_roster['Name'])
    pair_config = st.column_config.CheckboxColumn(help='Check if 2 people MUST be in the same car. Uncheck if 2 people must NOT be in the same car', default=True)
    separate_config = st.column_config.CheckboxColumn(help='Check if people who must be in the same car must be in their own car without anyone else.', default=False)

    df = st.data_editor(df_pairings, num_rows='dynamic', column_config={NAME1_COL:name_config, NAME2_COL:name_config, PAIR_COL:pair_config, SEPARATE_COL:separate_config})

    st.subheader('Key')
    st.markdown(f'**{NAME1_COL} / {NAME2_COL}**: Names of volunteers who must OR must NOT be in the same car. Names '
                'must match people on the roster. To match more than 2 people, create a chain across multiple rows '
                '(i.e. Person 1 and Person 2 in Row 1 and Person 2 and Person 3 in Row will match Person 1-3)')
    st.markdown(f'**{PAIR_COL}**: TRUE or an X to put 2 people in the same car or FALSE or an empty cell to ensure 2 people are NOT in the same car')
    st.markdown(f'**{SEPARATE_COL}**: TRUE or an X to put a group of people in a separate car (i.e. no one will be in the car group except people paired together here)')

    def set_pairings():
        st.session_state['df_roster'] = df_roster
        st.session_state['df_pairings'] = df
        st.session_state['df_car_groups'] = None
            
    next_on_click = set_pairings
elif cur_page==CAR_GEN_PAGE:
    col1, col2 = st.columns(2)
    day = st.session_state['day']
    if st.session_state['car_groups'] == None or col1.button('Re-Generate Car Groups'):
        st.session_state['df_car_groups'] =generator.gen_car_groups(st.session_state['df_roster'], st.session_state['df_pairings'], 
                                                                 day, gsheet, st.session_state['config'])

    st.subheader('Generated Car Groups')
    st.dataframe(st.session_state['car_groups'])

    if col2.button('Accept Car Groups', help='Export car groups to Google sheet'):
        sheet = CAR_GROUP_WORKSHEET.format(day)
        df_out_min = st.session_state['car_groups'][[x for x in st.session_state['car_groups'].columns if x.startswith('Car')]].reset_index()
        cols = list(df_out_min.columns)
        cols[0] = ''
        df_out_min.columns = cols
        cp_gsheet.update_sheet(gsheet['file'], sheet, df_out_min, gsheet['worksheets'])
        st.session_state['cur_page'] = SUCCESS_PAGE
elif cur_page==SUCCESS_PAGE:
    st.info('Car group has successfully been imported to Google Sheet. Re-load page to add car groups for the next day or make other updates to a Google Sheet.')
else:
    raise ValueError(f"Unknown page: {cur_page}")
    
if show_prev or show_next:
    st.divider()
    
    left, right = st.columns(2)
    if show_prev:
        def go_to_prev():
            st.session_state['page_history'].pop(-1)
            st.session_state['cur_page'] = st.session_state['page_history'][-1]

        left.button('Previous', on_click=go_to_prev)
        
    if show_next:
        def go_to_next():
            if next_on_click:
                next_on_click()

            st.session_state['cur_page'] = PAGES[min(len(PAGES)-1, page_idx+1)]

        right.button('Next', on_click=go_to_next)

st.info(f'If you encounter any issues with this site, please contact [admin](mailto:openpolicedata@gmail.com)')