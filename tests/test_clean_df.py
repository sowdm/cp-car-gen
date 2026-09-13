import pandas as pd
import re

from utils import clean_df

data = {
    'Name': ['   FirstName      LastName      ', 'First Last', 'First   Middle Last ', 0, False, 'aaaaaaaaa bbbbbb', 'AAAAAAA BBBBBBBB'],
    'Bool': ['   YES  ', 'yes', 'no', False, True, 'x', 'X  ']
}

def test_bool_col():
    df = pd.DataFrame(data)

    df = clean_df(df)

    assert not df['Name'].any()

    y = [x.strip() if isinstance(x,str) else x for x in data['Bool']]
    y = [x.lower() in ['yes','x'] if isinstance(x,str) else x for x in y]

    assert df['Bool'].tolist()==y


def test_string_col():
    df = pd.DataFrame(data)

    df = clean_df(df, str_cols=['Name'])

    y = [re.sub(r'\s\s+', ' ', x).strip().title() if isinstance(x,str) else x for x in data['Name']]
    assert df['Name'].tolist()==y


def test_name_col():
    df = pd.DataFrame(data)

    df = clean_df(df, name_cols=['Name'])

    y = [re.sub(r'\s\s+', ' ', x).strip() if isinstance(x,str) else x for x in data['Name']]
    assert df['Name'].tolist()==y
