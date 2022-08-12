import datetime
import hashlib
import os
import re
import requests
from importlib import import_module
Wiki = import_module('TFWiki-scripts.wikitools.wiki').Wiki
Page = import_module('TFWiki-scripts.wikitools.page').Page

verbose = False

FIND_YAHOO_TABLE = re.compile('<table[^>]*?data-test="historical-prices">(.*?)</table>')
FIND_TABLE_ROWS  = re.compile('<tr[^>]*>(.*?)</tr>')
FIND_TABLE_CELLS = re.compile('<span>([^>]*?)</span>')

dow_cache = {}
def get_dow_jones(day):
  if day.strftime('%Y-%m-%d') in dow_cache:
    return dow_cache[day.strftime('%Y-%m-%d')]

  range_start = int((day - datetime.timedelta(days=7)).timestamp()) # One week ago
  range_end = int(day.timestamp())
  headers = {'User-Agent': 'https://github.com/jbzdarkid/geohashing'} # Yahoo 404s requests without a UA
  r = requests.get(f'https://finance.yahoo.com/quote/%5EDJI/history?period1={range_start}&period2={range_end}', headers=headers)

  # Parse out the data. https://stackoverflow.com/a/1732454
  table = FIND_YAHOO_TABLE.search(r.text)[1]
  row = FIND_TABLE_ROWS.findall(table)[1] # The 0th row is the table headers.
  cells = FIND_TABLE_CELLS.findall(row)

  # At time of writing (2022-07-30) the rows are as follows:
  # Date, Open, High, Low, Close, Adjusted Close, Volume
  # Fortunately, we only care about the first two, so hopefully Yahoo doesn't mess with this too badly.
  dow_date = datetime.datetime.strptime(cells[0], '%b %d, %Y') # Unfortunately Yahoo uses the USA date standard: Dec 21, 2012
  dow_jones_open = cells[1].replace(',', '') # And they also use the USA numerical separator: ,
  if verbose:
    print(f'The DOW for {dow_date} opened at {dow_jones_open}')

  dow_cache[day.strftime('%Y-%m-%d')] = dow_jones_open
  return dow_jones_open


def get_geohash(day):
  date = day.strftime('%Y-%m-%d')
  dow_jones_open = get_dow_jones(day)

  hash = hashlib.md5(f'{date}-{dow_jones_open}'.encode('utf-8')).hexdigest()
  if verbose:
    print(f'Raw hash for {day}: {hash}')

  latitude  = str(float.fromhex(f'0.{hash[:16]}'))[2:] # Convert hex to float then removing leading '0.'
  longitude = str(float.fromhex(f'0.{hash[16:]}'))[2:] # Convert hex to float then removing leading '0.'
  centicule = latitude[0] + longitude[0]
  if verbose:
    print(f'(lat, long, cent): {latitude}, {longitude}, {centicule}')

  return (latitude, longitude, centicule)


def main(w):
  event = os.environ.get('GITHUB_EVENT_NAME', 'local_run')

  if event != 'local_run':
    if not w.login(os.environ['WIKI_USERNAME'], os.environ['WIKI_PASSWORD']):
      exit(1)

  failures = []

  if event == 'workflow_dispatch':
    # For manual runs (aka testing), don't spam other users' pages.
    pages = [Page(w, 'User:Darkid/Potential expeditions')]
  else:
    pages = w.get_all_category_pages('Category:Tracked by DarkBOT', namespaces=['User'])

  for page in pages:
    try:
      if verbose:
        print(f'Updating {page.title}...')
      contents = page.get_wiki_text()
      unchanged = True

      lines = contents.split('\n')
      for line in lines:
        if line.count('|') < 5:
          continue
        parts = line.split('|')
        lat = int(parts[1].strip())
        long = int(parts[3].strip())
        cents = parts[5].strip()

        settings = {}
        if line.count('|') >= 9:
          settings['email'] = 'email' in parts[9].lower(),

        eastern_time = datetime.timezone(-datetime.timedelta(hours=5, minutes=30))
        today = datetime.datetime.now(tz=eastern_time)
        if long >= -30:
          today -= datetime.timedelta(days=1)

        if today.weekday() in [0, 1, 2, 3]:
          days = [today] # Monday through Thursday only report for the current day
        elif today.weekday() == 4:
          # Fridays update the entire weekend (since it's known by that point)
          days = [today, today + datetime.timedelta(days=1), today + datetime.timedelta(days=2)]
        elif today.weekday() in [5, 6]:
          continue # On Saturday and Sunday, no updates (because we already updated on Friday)

        # Computing DOW holidays is really complex, so I'm just not doing it.

        for day in days:
          latitude, longitude, centicule = get_geohash(day=day)
          if centicule not in cents:
            continue # Too far away for this user

          if verbose:
            print(f'Found geohash on {day} within centicules for {page.title}: {line}')

          date = today.strftime('%Y-%m-%d')
          title = f'{date} {lat} {long}'
          page_link = f'https://geohashing.site/index.php?title={title}&action=edit'.replace(' ', '%20')
          map_link = f'https://maps.google.com/?q={lat}.{latitude},{long}.{longitude}'

          contents += f'\n=== [{page_link} {title}] ===\n'
          contents += f'[{map_link} Centicule {centicule}]\n'
          unchanged = False

          if settings.get('email'):
            user = page.basename.split('/', 1)[0] # User:Darkid/Foo -> User:Darkid
            title = f'On {date}, the geohashing site in {lat} {long} is within your selected centicule {centicule}'
            message = f'Map link: {map_link}\n'
            message += f'Wiki page: {page_link}\n'

            w.email_user(user, title, message)
            if verbose:
              print(f'Sent email to {user}')

      # End 'for line in lines'
      if unchanged:
        print(f'No relevant changes for {page.title}')
      elif page.edit(contents, bot=True, summary='Automatic update via https://github.com/jbzdarkid/geohashing'):
        if verbose:
          print(f'Updated {page.title}')
      else:
        failures.append(page.title)
    except:
      if verbose:
        print(f'Failed to update {page.title}')
        import traceback
        traceback.print_exc()
      failures.append(page.title)

  return len(failures)


if __name__ == '__main__':
  verbose = True
  w = Wiki('https://geohashing.site/api.php')
  exit(main(w))
