class mock_worksheet:
    def __init__(self, title, df):
        self.title = title
        self.df = df

    def get_all_records(self):
        return self.df.to_records(index=False)

    def row_values(self, idx):
        if idx==1:
            return list(self.df.columns)
        else:
            return list(self.iloc[idx-2])

class mock_spreadsheet:
    def __init__(self, titles, dfs):
        self.titles = titles
        dfs = dfs.copy()
        for _ in range(len(dfs), len(titles)):
            dfs.append([])

        self.dfs = dfs

    def worksheets(self):
        return [mock_worksheet(t, df) for t, df in zip(self.titles, self.dfs)]

    def worksheet(self, title):
        ws = [x for x in self.worksheets() if x.title==title]
        return ws[0]


def set_mockreturn(client, monkeypatch, worksheets, dfs=[]):
    def mockreturn(url):
        return mock_spreadsheet(worksheets, dfs)
    
    monkeypatch.setattr(client, 'open_by_url', mockreturn)