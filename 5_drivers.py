import re
import streamlit as st
from streamlit_sortables import sort_items

import base_page
import cp_gsheet
from generator import get_drivers
from worksheets import DRIVER_WORKSHEET
from columns import NAME_COL, DRIVER_TYPE_COL

gsheet = base_page.setup(__file__)

ncars = st.session_state['cargen'].ncars
must_be_in_same_car = st.session_state['cargen'].must_be_in_same_car

st.subheader(f'Driver Selection')

st.info(f'The default drivers shown here are based on the "{DRIVER_WORKSHEET}" tab of the Google spreadsheet. '+
        f'To control the default drivers, see instructions at the bottom of this page.')

def reload():
    st.session_state['reload_drivers'] = True

if 'reload_drivers' not in st.session_state:
    st.session_state['reload_drivers'] = True

df_roster = st.session_state['cargen'].df_roster
if not st.session_state['reload_drivers'] and st.session_state['drivers'] is not None:
    drivers = st.session_state['drivers']
    not_drivers = st.session_state['not_drivers']
    ncars-=len(st.session_state['separate_car_drivers'])

    df_drivers = st.session_state['df_drivers_all'][st.session_state['df_drivers_all'][NAME_COL].isin(df_roster[NAME_COL])]
    df_drivers = df_drivers[~df_drivers[NAME_COL].isin(st.session_state['ignore'])]
else:
    separate_car = st.session_state['cargen'].separate_car
    FULL_CAR_SIZE = st.session_state['cargen'].FULL_CAR_SIZE

    st.session_state['df_drivers_all'] = cp_gsheet.get_sheet(gsheet['file'], DRIVER_WORKSHEET, clean=True, 
                                     numeric_cols=[DRIVER_TYPE_COL],
                                     name_cols=[NAME_COL])
    df_drivers = st.session_state['df_drivers_all'][st.session_state['df_drivers_all'][NAME_COL].isin(df_roster[NAME_COL])]
    df_drivers = df_drivers[~df_drivers[NAME_COL].isin(st.session_state['ignore'])]

    names = df_drivers[NAME_COL].tolist()
    types = df_drivers[DRIVER_TYPE_COL].tolist()

    # All separate cars or groups that fill a car must have a driver in the group
    separate_car_drivers = []
    remove_drivers = []
    for m,s in zip(must_be_in_same_car, separate_car):
        if s or len(m)>=FULL_CAR_SIZE:
            # Find potential drivers in group
            group_drivers = [x for x in m if x in names]
            if len(group_drivers)==0:
                if s:
                    st.error(f'No drivers found in paired group {m} that much be in a separate car. Press Previous to update pairings '+
                             f'or update the {DRIVER_WORKSHEET} tab of the Google spreadsheet and press Reload.')
                else:
                    st.error(f'No drivers found in paired group {m} who must be in a separate car due to size. Press Previous to update pairings '+
                            f'or update the {DRIVER_WORKSHEET} tab of the Google spreadsheet and press Reload.')

                col1, col2 = st.columns(2)
                if col1.button('Previous'):
                    st.switch_page('4_pairings.py')
                col2.button('Reload Spreadsheet', on_click=reload, 
                    help=f'Reload "{DRIVER_WORKSHEET}" tab from Google spreadsheet (for example if changes were made)')
                st.stop()

            d = get_drivers(1, names, types, subset=group_drivers)
            separate_car_drivers.append(d[0])
            remove_drivers.extend(group_drivers)

    ncars-=len(separate_car_drivers)
    remaining_names = [x for x in names if x not in remove_drivers]
    drivers = get_drivers(ncars, names, types, subset=remaining_names, must_be_in_same_car=must_be_in_same_car)
    if not drivers:
        st.error(f'There are not enough drivers available for {ncars}. See {DRIVER_WORKSHEET} in Google Sheet')
        st.stop()

    not_drivers = [x for x in remaining_names if x not in drivers]
    
    st.session_state['drivers'] = drivers
    st.session_state['not_drivers'] = not_drivers
    st.session_state['reload_drivers'] = False
    st.session_state['separate_car_drivers'] = separate_car_drivers

if len(st.session_state['separate_car_drivers'])>0:
    st.warning('The following individuals will be drivers based on pairings selected on the last page and preferences in '+
               f'the {DRIVER_WORKSHEET} tab of the Google Sheet: {st.session_state["separate_car_drivers"]}')

original_items = [
    {'header': "Today's Drivers",  'items': drivers},
    {'header': 'Available Drivers', 'items': not_drivers},
    {'header': 'Permanently Remove from Driver Pool (i.e. does not have car)', 'items': []}
]

st.markdown(f'Select drivers for {ncars} remaining cars by dragging between the Drivers and NOT Drivers lists')

col0, col1, col2 = st.columns(3)

selection = sort_items(original_items, multi_containers=True, direction='horizontal')

selected_drivers = selection[0]['items']
ndrivers = len(selected_drivers)
disabled = ndrivers != ncars
if ndrivers < ncars:
    st.error(f'{ncars-ndrivers} more drivers needed.')
elif ndrivers > ncars:
    st.error(f'{ndrivers-ncars} drivers need to be removed. There are only {ncars} available cars.')

# Check if multiple selected drivers must be in the same car
for m in must_be_in_same_car:
    if sum(x in m for x in selected_drivers)>1:
        disabled = True
        st.error(f'ERROR: More than one driver selected from paired group: {m}')

if col0.button('Previous'):
    st.switch_page('4_pairings.py')

col1.button('Reload Spreadsheet', on_click=reload, 
            help=f'Reload "{DRIVER_WORKSHEET}" tab from Google spreadsheet (for example if changes were made)')

if col2.button('Accept Drivers', disabled=disabled):
    perm_del_drivers = selection[2]['items']
    if len(perm_del_drivers)>0:
        st.session_state['df_drivers_all'] = st.session_state['df_drivers_all'][~st.session_state['df_drivers_all'][NAME_COL].isin(perm_del_drivers)]
        cp_gsheet.update_sheet(gsheet['file'], DRIVER_WORKSHEET, st.session_state['df_drivers_all'], gsheet['worksheets'])

    st.session_state['drivers'] = selected_drivers
    st.session_state['not_drivers'] = selection[1]['items']
    selected_drivers.extend(st.session_state['separate_car_drivers'])
    st.session_state['cargen'].set_drivers(selected_drivers)
    st.session_state['df_car_groups'] = None
    st.switch_page('6_cargen.py')

st.subheader('Driver Pool Updates')
st.text("Add drivers or update driver likelihoods (drivers with highest likelihoods are selected as default set of drivers)")

col0, col1, col2 = st.columns(3)
name_update = col0.selectbox('Name', st.session_state['cargen'].df_roster[NAME_COL])

slider_key = 'slider_'+name_update

idx = df_drivers[NAME_COL]==name_update
is_driver = idx.any()
default = df_drivers.loc[idx, DRIVER_TYPE_COL].iloc[0] if is_driver else 0
maxval = df_drivers[DRIVER_TYPE_COL].max()+1
likelihood = col1.slider('Driver Likelihood', 0, int(maxval), default, key=slider_key)

if col2.button('Update Driver'):
    update = True
    if is_driver:
        # Update driver likelihood
        update = st.session_state['df_drivers_all'].loc[st.session_state['df_drivers_all'][NAME_COL]==name_update, DRIVER_TYPE_COL].iloc[0] != likelihood
        st.session_state['df_drivers_all'].loc[st.session_state['df_drivers_all'][NAME_COL]==name_update, DRIVER_TYPE_COL] = likelihood
    else:
        # Append new driver
        st.session_state['df_drivers_all'].loc[len(st.session_state['df_drivers_all']), NAME_COL] = name_update
        st.session_state['df_drivers_all'].loc[len(st.session_state['df_drivers_all'])-1, DRIVER_TYPE_COL] = likelihood

        day_cols = [x for x in df_roster.columns if re.search(r'^Day\s\d+\s', x)]
        idx = st.session_state['cargen'].df_roster[NAME_COL]==name_update
        for d in day_cols:
            st.session_state['df_drivers_all'].loc[len(st.session_state['df_drivers_all'])-1, d] = \
                st.session_state['cargen'].df_roster.loc[idx, d].iloc[0]

    if update:
        with st.spinner():
            cp_gsheet.update_sheet(gsheet['file'], DRIVER_WORKSHEET, st.session_state['df_drivers_all'], gsheet['worksheets'])
        st.session_state['reload_drivers'] = True
        st.rerun()