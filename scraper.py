from urllib.request import urlopen
from bs4 import BeautifulSoup
import pandas as pd

def scrape(url):
    html = urlopen(url)

    soup = BeautifulSoup(html)

    headers = [th.getText() for th in soup.findAll('tr', limit=2)[0].findAll('th')][1:] # Gets all column headers

    rows = soup.findAll('tr')[1:]
    stats = [[td.getText() for td in rows[i].findAll('td')]
                for i in range(len(rows))]

    return pd.DataFrame(data = stats, columns = headers)