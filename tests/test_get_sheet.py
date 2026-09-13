import pandas as pd

from cp_gsheet import get_sheet
from mock_gspread import set_mockreturn

def test_no_records(monkeypatch, client):
    worksheets = ['test']
    df_orig = pd.DataFrame(columns=['Col1','Col2','Col3'])
    set_mockreturn(client, monkeypatch, worksheets, [df_orig])

    sht = client.open_by_url('test')
    df = get_sheet(sht, worksheets[0])
    assert len(df)==0
    assert (df.columns == df_orig.columns).all()


def test_has_records(monkeypatch, client):
    worksheets = ['test']

    data = {
        'Name': ['   FirstName      LastName      ', 'First Last', 'First   Middle Last ', 0, False, 'aaaaaaaaa bbbbbb', 'AAAAAAA BBBBBBBB'],
        'Bool': ['   YES  ', 'yes', 'no', False, True, 'x', 'X  ']
    }
    df_orig = pd.DataFrame(data)
    set_mockreturn(client, monkeypatch, worksheets, [df_orig])

    sht = client.open_by_url('test')
    df = get_sheet(sht, worksheets[0])
    assert df.equals(df_orig)