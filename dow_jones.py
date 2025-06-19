import collections
import json
import re
import requests
from datetime import datetime

verbose = False

FIND_TABLE       = re.compile('<table[^>]*>(.*?)</table>')
FIND_TABLE_ROWS  = re.compile('<tr[^>]*>(.*?)</tr>')
FIND_TABLE_CELLS = re.compile('<td[^>]*>(.*?)</td>')

def get_url(url):
  headers = {'User-Agent': 'Mozilla/5.0 (https://github.com/jbzdarkid/geohashing)'} # Yahoo 404s requests without a UA
  r = requests.get(url, headers=headers)
  r.raise_for_status()
  return r.text

# 2025-06-19 still working
def dow_from_yahoo():
  text = get_url('https://finance.yahoo.com/quote/%5EDJI/history')

  table = FIND_TABLE.findall(text)[0] # 1st table
  for row in FIND_TABLE_ROWS.findall(table):
    cells = FIND_TABLE_CELLS.findall(row)
    if not cells:
      continue

    date = datetime.strptime(cells[0], '%b %d, %Y')
    yield (date, cells[1].replace(',', ''))


# 2025-06-19 testing
def dow_from_investing():
  text = get_url('https://www.investing.com/indices/us-30-historical-data')

  table = FIND_TABLE.findall(text)[1] # 2nd table
  for row in FIND_TABLE_ROWS.findall(table):
    cells = FIND_TABLE_CELLS.findall(row)
    if not cells:
      continue

    raw_date = re.search(r'\d{2}/\d{2}/20\d{2}', cells[0])
    date = datetime.strptime(raw_date[0], '%m/%d/%Y')
    yield (date, cells[2].replace(',', ''))


# 2025-06-19 testing
def dow_from_financialtimes():
  text = get_url('https://markets.ft.com/data/indices/tearsheet/historical?s=DJI:DJI')

  table = FIND_TABLE.findall(text)[0] # 1st table
  for row in FIND_TABLE_ROWS.findall(table):
    cells = FIND_TABLE_CELLS.findall(row)
    if not cells:
      continue

    raw_date = re.search('<span[^>]*>(.*?)</span>', cells[0])
    date = datetime.strptime(raw_date[1], '%A, %B %d, %Y')
    yield (date, cells[1].replace(',', ''))


# 2025-06-19 anti-bot technology
def dow_from_seekingalpha():
  text = get_url('https://seekingalpha.com/symbol/DJI')

  start_idx = text.index('real_time_quotes')
  end_idx = text.index(']', start_idx)
  data = json.loads(text[start_idx + 19:end_idx])

  date = datetime.strptime(data['updated_at'][:10], '%Y-%m-%d')
  yield (date, str(data['open']))


# 2025-06-19 just created, testing
def dow_from_businessinsider():
  text = get_url('https://markets.businessinsider.com/index/dow_jones?op=1')

  start_idx = text.index('historicalPrices: {')
  end_idx = text.index('\n', start_idx)

  data = json.loads(text[start_idx + 18:end_idx])
  row = data['model'][0]
  date = datetime.strptime(row['Date'], '%m/%d/%y')
  yield (date, str(row['Open']))


# 2025-06-19 just created, testing
def dow_from_marketwatch():
  text = get_url('https://www.marketwatch.com/investing/index/djia')

  start_idx = text.index('<meta name="quoteTime" content="')
  end_idx = text.index('"', start_idx)
  date = datetime.strptime(text[start_index+32:end_idx-9], '%b %d, %Y')

  start_idx = text.index('day-open="')
  end_idx = text.index('"', start_idx)
  open = text[start_idx+10:end_idx]

  yield (date, open)


dow_sources = [dow_from_yahoo, dow_from_investing, dow_from_financialtimes, dow_from_businessinsider, dow_from_marketwatch]
def get_dow_jones_opens():
  temp_cache = collections.defaultdict(list)
  for dow_source in dow_sources:
    try:
      for date, dow in dow_source():
        temp_cache[date.strftime('%Y-%m-%d')].append(dow)
    except:
      import traceback
      traceback.print_exc()
      continue

  if verbose:
    print('Temp cache', temp_cache)

  dow_opens = {}
  for key, values in temp_cache.items():
    if len(values) < 2: # We need at least 2 agreements (but ideally we have 3)
      continue
    value_dict = {}
    for value in values:
      value_dict[value] = value_dict.get(value, 0) + 1
    for value, count in value_dict.items():
      if count > len(values) / 2:
        dow_opens[key] = value
        break
    else:
      if verbose:
        print(f'Not enough information to determine the DOW opening for {key}')

  if verbose:
    print('Dow opens', dow_opens)

  return dow_opens


if __name__ == '__main__':
  verbose = True
  print(get_dow_jones_opens())
