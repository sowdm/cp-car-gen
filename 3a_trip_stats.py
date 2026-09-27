import pandas as pd
import re
import streamlit as st

import base_page

gsheet = base_page.setup(__file__)

if st.button('Previous'):
    st.switch_page('3_roster.py')

df_roster = st.session_state['df_roster_full']

day_cols = [x for x in df_roster.columns if re.search(r'^Day\s\d+\s', x)]

df = pd.DataFrame(columns=['Volunteers','Capacity (Drivers x 4)','Not Enough Drivers Warning! (if checked)', 'Drivers', 
                           'Backup Drivers', 'BIPOC Status'], index=day_cols)
df['Volunteers'] = df_roster[day_cols].sum()

for c in day_cols:
    df.loc[c, 'Drivers'] = df_roster['Driver'][df_roster[c]].sum()
    df.loc[c, 'Capacity (Drivers x 4)'] = df.loc[c, 'Drivers'] * 4
    df.loc[c, 'Not Enough Drivers Warning! (if checked)'] = df.loc[c, 'Capacity (Drivers x 4)'] < df.loc[c, 'Volunteers']
    df.loc[c, 'Backup Drivers'] = df_roster['Backup Driver'][df_roster[c]].sum()
    df.loc[c, 'BIPOC Status'] = df_roster['BIPOC Status'][df_roster[c]].sum()


st.subheader('Volunteers and Drivers')
st.dataframe(df.fillna(0))

generations = df_roster['Generation'].unique()
df = pd.DataFrame(columns=generations, index=day_cols)

for c in day_cols:
    df.loc[c, : ] = df_roster[df_roster[c]]['Generation'].value_counts()

st.subheader('Generation')
st.dataframe(df.fillna(0))

exp = df_roster['Canvassing Experience'].unique()
df = pd.DataFrame(columns=exp, index=day_cols)

for c in day_cols:
    df.loc[c, : ] = df_roster[df_roster[c]]['Canvassing Experience'].value_counts()

st.subheader('Canvassing Experience')
st.dataframe(df.fillna(0))

st.subheader('Half Day Status')
st.dataframe(df_roster[df_roster['Half Day Status'].apply(lambda x: len(x)>0)][['Name','Half Day Status']].reset_index(drop=True))

diets = df_roster['Dietary Restrictions'].unique()
df = pd.DataFrame(columns=diets, index=day_cols)

for c in day_cols:
    df.loc[c, : ] = df_roster[df_roster[c]]['Dietary Restrictions'].value_counts()

df = df.drop(columns=['','No','None'], errors=False)

st.subheader('Dietary Restrictions')
st.dataframe(df.fillna(0))
