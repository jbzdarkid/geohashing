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
  r = requests.get('https://www.investing.com/indices/us-30-historical-data', headers=headers)
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


dow_cache = {}
def get_dow_jones(day):
  if not dow_cache:
    temp_cache = collections.defaultdict(list)
    for date, dow in dow_from_yahoo():
      temp_cache[date.strftime('%Y-%m-%d')].append(dow)
    for date, dow in dow_from_investing():
      temp_cache[date.strftime('%Y-%m-%d')].append(dow)
    for date, dow in dow_from_markets():
      temp_cache[date.strftime('%Y-%m-%d')].append(dow)

    print(temp_cache)

    for key, value in temp_cache.items():
      if len(value) < 3:
        continue
      source1, source2, source3 = value
      if source1 == source2:
        value = source1
      elif source2 == source3:
        value = source2
      elif source3 == source1:
        value = source3
      else:
        continue
      dow_cache[key] = value

  dow_jones_open = None
  while not dow_jones_open:
    dow_jones_open = dow_cache.get(day.strftime('%Y-%m-%d'), None)
    day -= timedelta(hours=1)

  if verbose:
    print(f'The DOW for {day} opened at {dow_jones_open}')
  return dow_jones_open
