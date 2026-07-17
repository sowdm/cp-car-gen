import streamlit as st
from streamlit_gsheets import GSheetsConnection

import helper
from worksheets import FULL_ROSTER_WORKSHEET, ROSTER_WORKSHEET, PAIRINGS_WORKSHEET, CAR_GROUP_WORKSHEET

# TODO: Overwrite vs. Next
# TODO: Create timeline of when people are present including half-day status

GET_URL_PAGE = 'file'
NO_CP_EXPORT_PAGE = 'no export'
CLEAR_SAMPLE_PAGE = 'sample'
INIT_PAGE = 'init'
CAR_GEN_PAGE = 'car gen'
PAGES = [GET_URL_PAGE, NO_CP_EXPORT_PAGE, CLEAR_SAMPLE_PAGE, INIT_PAGE, CAR_GEN_PAGE]
# TODO: Add test to ensure that all adv_pages are in pages
ADV_PAGES = [GET_URL_PAGE]
SAMPLE_URL = 'Use Sample'
NO_NEXT = [GET_URL_PAGE, NO_CP_EXPORT_PAGE]


if 'cur_page' not in st.session_state:
    st.session_state['cur_page'] = GET_URL_PAGE
    st.session_state['is_advanced'] = False
    st.session_state['is_sample'] = False
    st.session_state['page_history'] = []
    conn = st.connection("gsheets", type=GSheetsConnection)
    st.session_state['client'] = conn.client._client

if 'gsheet' in st.session_state:
    gsheet = st.session_state['gsheet']

if st.session_state['cur_page'] not in st.session_state['page_history']:
    st.session_state['page_history'].append(st.session_state['cur_page'])

if st.session_state['is_sample'] and st.session_state['cur_page']!=GET_URL_PAGE:
    st.info(f"Sample spreadsheet can be viewed [here]({st.secrets['SAMPLE_URL']})")

st.set_page_config(
    page_title="Car Generator",
    initial_sidebar_state="auto",
    layout = 'wide',
    menu_items={
        'Report a Bug': "mailto:openpolicedata@gmail.com"
    }
)

container = st.container()

cur_pages = ADV_PAGES if st.session_state['is_advanced'] else PAGES
page_idx = cur_pages.index(st.session_state['cur_page'])

st.divider()

left, right = st.columns(2)
if left.button('Previous', disabled=page_idx==0):
    st.session_state['page_history'].pop(-1)
    st.session_state['cur_page'] = st.session_state['page_history'][-1]
    
if right.button('Next', disabled=st.session_state['cur_page'] in NO_NEXT):
    st.session_state['cur_page'] = cur_pages[max(len(cur_pages)-1, page_idx+1)]


with container:
    if st.session_state['cur_page'] == GET_URL_PAGE:
        url = st.text_input('Google Sheet URL')

        def set_url():
            st.session_state['gsheet'] = helper.get_spreadsheet(st.session_state['client'], url)
            if not st.session_state['gsheet']['has_cp_export']:
                st.session_state['cur_page'] = NO_CP_EXPORT_PAGE
            else:
                st.session_state['cur_page'] = CAR_GEN_PAGE if st.session_state['gsheet']['is_init'] else INIT_PAGE
            st.session_state['is_sample'] = False

        left,right = st.columns([1, 5])
        left.button('Use URL', on_click=set_url)
        right.markdown(f'*Google Sheet should contain the CP roster export spreadsheet in a sheet called "**{FULL_ROSTER_WORKSHEET}**" (including the !). '+
                    'This spreadsheet MUST be [shared with Editor access](https://support.google.com/a/users/answer/13309904?hl=en) with the email address provided to you. '+
                    'If no email has been provided to you, request the email on Slack.*')
        

        def use_sample():
            st.session_state['gsheet'] = helper.get_spreadsheet(st.session_state['client'], st.secrets['SAMPLE_URL'])
            assert st.session_state['gsheet']['has_cp_export'], 'ERROR: Sample spreadsheet does not have roster. This should not happen. Please report this issue.'
            st.session_state['cur_page'] = CLEAR_SAMPLE_PAGE if st.session_state['gsheet']['is_init'] else INIT_PAGE
            st.session_state['is_sample'] = True

        left,right = st.columns([1, 5])
        left.button(SAMPLE_URL, on_click=use_sample)
        right.markdown(f"If you don't have a Google Sheet URL and want to try out the generator with our [sample spreadsheet]({st.secrets['SAMPLE_URL']}), click **{SAMPLE_URL}** button")
    elif st.session_state['cur_page'] == NO_CP_EXPORT_PAGE:
        st.warning(f'The spreadsheet at the requested URL must have the export of the roster from the CP app in a sheet called "{FULL_ROSTER_WORKSHEET}". '+
                   'Contact the administrator at the email below if you are not sure what this is.')
    elif st.session_state['cur_page'] == CLEAR_SAMPLE_PAGE:
        car_group_days = [k for k,x in enumerate(gsheet['date_has_car_group']) if x]
        if gsheet['car_group_date_error']:
            st.error(f'There are gaps between days with existing car groups in the sample spreadsheet. The following days have car groups: {car_group_days}. '+
                     'This should not happen with the sample spreadsheet. Please report to the administrator at the email below.')
        else:
            if len(car_group_days)==0:
                msg = 'Sample spreadsheet has been initialized but there are no car groups set up.'
            elif len(car_group_days)==len(gsheet['date_has_car_group']):
                msg = f"Car groups for all {len(car_group_days)} have been completd."
            else:
                msg = f"Car groups for {len(car_group_days)} of {len(gsheet['date_has_car_group'])} days have been completed."

            st.info('The sample spreadsheet has already been started by you or someone else. '+msg+' You can pick up where they left off or start over.')
            left,right = st.columns(2)

            def start_over():
                for w in [x for x in gsheet['worksheets'] if x!=FULL_ROSTER_WORKSHEET]:
                    gsheet['file'].del_worksheet(w)
                st.session_state['cur_page'] = INIT_PAGE
            
            def cont():
                st.session_state['cur_page'] = CAR_GEN_PAGE

            left.button('Start Over', on_click=start_over)
            right.button('Continue', on_click=cont)
    else:
        raise ValueError(f"Unknown page: {st.session_state['cur_page']}")

st.info(f'If you encounter any issues with this site, please contact [admin](mailto:openpolicedata@gmail.com)')