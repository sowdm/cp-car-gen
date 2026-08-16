import streamlit as st
from streamlit_gsheets import GSheetsConnection
import tomllib

# TODO: Create timeline of when people are present including half-day status
# TODO: Add ability to change config and import/export config

st.set_page_config(
    page_title="Car Generator",
    initial_sidebar_state="auto",
    layout = 'wide',
    menu_items={
        'Report a Bug': "mailto:car_gen_app@pm.me"
    }
)

st.warning(r'This app is intended to provide a 90% solution for generating your car groups. ' \
    'You should review the results and update manually as needed.\n\n' \
    'Also, this is a BETA version of this app. Thank you for testing it, and we hope you find it useful. ' \
    'If you encounter any issues, please contact [admin](mailto:car_gen_app@pm.me).')


if 'cur_page' not in st.session_state:
    st.session_state['is_sample'] = False
    conn = st.connection("gsheets", type=GSheetsConnection)
    st.session_state['client'] = conn.client._client
    with open('config.toml', 'rb') as f:
        st.session_state['config'] = tomllib.load(f)

pg = st.navigation([st.Page("1_get_url.py"), st.Page("2_status.py"), st.Page("3_pairings.py"), st.Page('4_cargen.py'), st.Page('5_success.py')], position='hidden')
pg.run()

st.info(f'If you encounter any issues with this site, please contact [admin](mailto:car_gen_app@pm.me)')