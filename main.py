from importlib import import_module
Wiki = import_module('TFWiki-scripts.wikitools.wiki').Wiki
Page = import_module('TFWiki-scripts.wikitools.page').Page

import datetime
import os
verbose = False


def get_geohash(day):
  date = day.strftime('%Y-%m-%d')

  import requests
  r = requests.get('https://finance.yahoo.com/quote/%5EDJI?p=^DJI') # TODO: Day
  i = r.text.find('data-test="OPEN-value">') + 23
  dow_jones = r.text[i:r.text.find('</td>', i)].replace(',', '')
  if verbose:
    print(f'The DOW for today was {dow_jones}')

  import hashlib
  print(f'{date}-{dow_jones}')
  hash = hashlib.md5(f'{date}-{dow_jones}'.encode('utf-8')).hexdigest()
  if verbose:
    print(f'Raw hash: {hash}')

  latitude = float.fromhex(f'0.{hash[:16]}')
  longitude = float.fromhex(f'0.{hash[16:]}')
  centicule = str(latitude)[2] + str(longitude)[2]
  if verbose:
    print(f'(lat, long, cent): {latitude}, {longitude}, {centicule}')

  return (latitude, longitude, centicule)


def main(w):
  #if not w.login(os.environ['WIKI_USERNAME'], os.environ['WIKI_PASSWORD']):
  #  exit(1)

  # If other people are interested, I can fetch these pages from a category.
  page_titles = [
    'User:Darkid/Potential_expeditions',
  ]

  for page_title in page_titles:
    page = Page(w, page_title)
    contents = page.get_wiki_text()

    lines = contents.split('\n')
    for line in lines:
      if line.count('|') < 5:
        continue
      parts = line.split('|')
      lat = parts[1].strip()
      long = parts[3].strip()
      cents = parts[5].strip()

      eastern_time = datetime.timezone(-datetime.timedelta(hours=5, minutes=30))
      today = datetime.datetime.now(tz=eastern_time)
      if int(long) >= -30:
        today -= datetime.timedelta(days=1)

      days = [today]
      #if today.weekday() == 4: # On Friday, update the entire weekend
      #  days += [today + datetime.timedelta(days=1), today + datetime.timedelta(days=2)]
      #elif today.weekday() in [5, 6]: # On Saturday and Sunday, no updates (because we already updated on Friday)
      #  continue

      for day in days:
        latitude, longitude, centicule = get_geohash(day=day)
        if centicule not in cents:
          continue # Too far away for this user

        date = today.strftime('%Y-%m-%d')
        contents += f'=== [[{date} {lat} {long}]] ===\n'
        contents += f'Centicule {cent} [https://maps.google.com/?q={lat}.{latitude},{long}.{longitude}]\n'

        if verbose:
          print(f'Updating {page_title} with a new geohash for {date}')

    # End 'for line in lines'
    page.edit(contents, bot=True, summary='Automated update by darkid\'s bot')

if __name__ == '__main__':
  verbose = True
  w = Wiki('https://geohashing.site/api.php')
  main(w)
