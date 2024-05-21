import collections
import re
import requests
from datetime import datetime, timedelta

verbose = True

FIND_TABLE       = re.compile('<table[^>]*>(.*?)</table>')
FIND_TABLE_ROWS  = re.compile('<tr[^>]*>(.*?)</tr>')
FIND_TABLE_CELLS = re.compile('<td[^>]*>(.*?)</td>')
headers = {'User-Agent': 'Mozilla/5.0 (https://github.com/jbzdarkid/geohashing)'} # Yahoo 404s requests without a UA

def dow_from_yahoo():
  r = requests.get('https://finance.yahoo.com/quote/%5EDJI/history', headers=headers)
  if not r.ok:
    print(r.text)
    r.raise_for_status()

  table = FIND_TABLE.findall(r.text)[0] # 1st table
  for row in FIND_TABLE_ROWS.findall(table):
    cells = FIND_TABLE_CELLS.findall(row)
    if not cells:
      continue
    
    # This pagescraper was last updated on 2024-05-18
    date = datetime.strptime(cells[0], '%b %d, %Y')
    yield (date, cells[1].replace(',', ''))


def dow_from_investing():
  return
  r = requests.get('https://www.investing.com/indices/us-30-historical-data', headers=headers)
  if not r.ok:
    print(r.text)
    r.raise_for_status()

  table = FIND_TABLE.findall(r.text)[1] # 2nd table
  for row in FIND_TABLE_ROWS.findall(table):
    cells = FIND_TABLE_CELLS.findall(row)
    if not cells:
      continue

    # This pagescraper was last updated on 2024-05-18
    raw_date = re.search(r'\d{2}/\d{2}/20\d{2}', cells[0])
    date = datetime.strptime(raw_date[0], '%m/%d/%Y')
    yield (date, cells[2].replace(',', ''))


def dow_from_markets():
  r = requests.get('https://markets.ft.com/data/indices/tearsheet/historical?s=DJI:DJI', headers=headers)
  if not r.ok:
    print(r.text)
    r.raise_for_status()

  table = FIND_TABLE.findall(r.text)[0] # 1st table
  for row in FIND_TABLE_ROWS.findall(table):
    cells = FIND_TABLE_CELLS.findall(row)
    if not cells:
      continue

    # This pagescraper was last updated on 2024-05-18
    raw_date = re.search('<span[^>]*>(.*?)</span>', cells[0])
    date = datetime.strptime(raw_date[1], '%A, %B %d, %Y')
    yield (date, cells[1].replace(',', ''))


def get_dow_jones_opens():
  temp_cache = collections.defaultdict(list)
  for date, dow in dow_from_yahoo():
    temp_cache[date.strftime('%Y-%m-%d')].append(dow)
  for date, dow in dow_from_investing():
    temp_cache[date.strftime('%Y-%m-%d')].append(dow)
  for date, dow in dow_from_markets():
    temp_cache[date.strftime('%Y-%m-%d')].append(dow)

  if verbose:
    print('Temp cache', temp_cache)

  dow_opens = {}
  for key, values in temp_cache.items():
    if len(values) < 2: # We need at least 2 agreements (but ideally we have 3)
      continue
    if values[0] == values[1]:
      dow_opens[key] = values[0]
    elif len(values) > 2 and values[1] == values[2]:
      dow_opens[key] = values[1]
    elif len(values) > 2 and values[2] == values[0]:
      dow_opens[key] = values[2]
    else:
      dow_opens[key] = -len(values) # Signal value

  if verbose:
    print('Dow opens', dow_opens)

  return dow_opens
