import streamlit as st

pages = ['file']

TODO: Create placeholder

if st.button('Previous'):
    

if 'cur_page' not in st.session_state:
    st.session_state['cur_page'] = 0
TODO: add beginner and advanced page list

if st.session_state['cur_page'] == 'file':
    URL = st.text_input('Google Sheet URL')
TODO
    st.markdown('Google Sheet should contain the CP roster export spreadsheet in a sheet called XXXX')
else:
    raise(Value error(f"Unknown page: {st.session_state['cur_page']}"))

