import gspread
import streamlit as st
from streamlit_gsheets import GSheetsConnection
import tomllib

import constants
import utils

# TODO: Create timeline of when people are present including half-day status
# TODO: Add ability to change config and import/export config

st.set_page_config(
    page_title="Car Generator",
    initial_sidebar_state="auto",
    layout = 'wide',
    menu_items={
        'Report a Bug': "mailto:"+constants.EMAIL
    }
)

st.warning(r'This app is intended to provide a 90% solution for generating your car groups. ' \
    'You should review the results and update manually as needed.\n\n' \
    'Also, this is a BETA version of this app. Thank you for testing it, and we hope you find it useful. ' \
    f'If you encounter any issues, please contact [admin](mailto:{constants.EMAIL}).')


if 'display_error' not in st.session_state:
    st.session_state['is_sample'] = False
    conn = st.connection("gsheets", type=GSheetsConnection)
    st.session_state['client'] = conn.client._client
    st.session_state['display_error'] = {}
    with open('config.toml', 'rb') as f:
        st.session_state['config'] = tomllib.load(f)

pg = st.navigation([st.Page("1_get_url.py"), st.Page("2_status.py"), st.Page("3_pairings.py"), st.Page('4_drivers.py'), st.Page('5_cargen.py'), 
                    st.Page('6_success.py')], position='hidden')

# TODO: Catch not a valid URL. Restricted URL. Not writeable URL.

try:
    pg.run()
except gspread.exceptions.NoValidUrlKeyFound:
    st.error(f'ERROR: The entered URL does not appear to be a valid URL. If the URL is valid, please contact [admin](mailto:{constants.EMAIL}).')
except PermissionError:
    st.error('ERROR: The entered URL has restricted access. This means only users who have explicitly been given access can use the spreadsheet.'+
             'Please reload this page and follow the instructions for sharing the Google sheet.')
except gspread.exceptions.APIError:
    st.error('ERROR: The entered URL is not shared with Editor access. '+
                 'Please reload this page and follow the instructions for sharing the Google sheet.')
except Exception as e:
    display_msg, traceback_msg = utils.get_error_msgs(st.session_state)
    st.error(display_msg)
    st.download_button('Download Error Message', traceback_msg)
    raise

st.info(f'If you encounter any issues with this site, please contact [admin](mailto:{constants.EMAIL})')