import collections
import datetime
import hashlib
import os
import time
import zoneinfo
from importlib import import_module
Wiki = import_module('TFWiki-scripts.wikitools.wiki').Wiki
Page = import_module('TFWiki-scripts.wikitools.page').Page

import dow_jones

verbose = False

def get_geohash(dow_opens, end_day, w30 = True):
  last_dow_open = None
  date_range = [end_day - datetime.timedelta(days=i) for i in range(10)][::-1]
  for day in date_range:
    # The 30W rule states that coordinates east of Long -30 should be computed using the previous day's DOW opening.
    if not w30 and day >= datetime.datetime(2008, 5, 27, tzinfo=datetime.timezone.utc):
      day -= datetime.timedelta(days = 1)

    date = day.strftime('%Y-%m-%d')
    if dow_open := dow_opens.get(date):
      last_dow_open = dow_open

  if not last_dow_open:
    print('DOW open could not be found, cannot compute geohash')
    exit(1)
  # Compute using the original unmodified day
  hash_string = end_day.strftime('%Y-%m-%d') + '-' + last_dow_open
  hash = hashlib.md5(hash_string.encode('utf-8')).hexdigest()

  latitude  = str(float.fromhex(f'0.{hash[:16]}'))[2:] # Convert hex to float then removing leading '0.'
  longitude = str(float.fromhex(f'0.{hash[16:]}'))[2:] # Convert hex to float then removing leading '0.'
  centicule = latitude[0] + longitude[0]
  if verbose:
    print(f'hash({hash_string}) = {hash} -> ({latitude}, {longitude}, {centicule})')

  return (latitude, longitude, centicule)

DAY_OF_WEEK = 'monday, tuesday, wednesday, thursday, friday, saturday, sunday'.split(', ')
def parse_config(contents):
  # Nested map, day-of-week:(lat, long):centicule:{notification_methods}
  config = collections.defaultdict(
    lambda: collections.defaultdict(
      lambda: collections.defaultdict(dict)))

  lines = contents.split('\n')
  for line in lines:
    if line.count('|') < 5:
      continue
    parts = line.split('|')
    lat = int(parts[1].strip())
    long = int(parts[3].strip())
    cents = parts[5].strip()

    target_days = []
    notification_methods = ['config_page']
    if len(parts) >= 9:
      settings = parts[9].lower().replace(',', ' ').split(' ') # Separators may be ',' or ' '
      for setting in settings:
        if not setting:
          continue
        elif setting in DAY_OF_WEEK:
          target_days.append(setting)
        elif setting in ['email', 'talkpage']:
          notification_methods.append(setting)
        else:
          print(f'Unknown setting: "{setting}"')
    if len(target_days) == 0:
      target_days = DAY_OF_WEEK # If not specified, all the days of the week

    for day in target_days:
      for cent in cents.replace(',', ' ').split(' '): # Separators may be ',' or ' '
        if cent: # Only handle non-empty to skip padding
          for method in notification_methods:
            config[day][(lat, long)][cent][method] = True

  return config

def main(w, today):
  event = os.environ.get('GITHUB_EVENT_NAME', 'local_run')

  if event != 'local_run':
    if not w.login(os.environ['WIKI_USERNAME'], os.environ['WIKI_PASSWORD']):
      exit(1)

  if event == 'workflow_dispatch':
    # For manual runs (aka testing), don't spam other users' pages.
    pages = [Page(w, 'User:Darkid/Potential expeditions')]
  else:
    pages = w.get_all_category_pages('Category:Tracked by DarkBOT', namespaces=['User'])

  if today.day == 1:
    # On the first of the month, ping github to keep the workflow enabled
    headers = {
      'Accept': 'application/vnd.github.v3+json',
      'Authorization': 'Bearer ' + os.environ['GITHUB_TOKEN'],
    }
    import requests
    s = requests.Session()
    s.get('https://github.com/login') # Just to populate cookies
    r = s.put('https://github.com/jbzdarkid/geohashing/actions/workflows/31355940/enable', headers)
    print(r.status_code, r.text)
    r.raise_for_status()

  if today.weekday() in [0, 1, 2, 3]:
    days = [today]
    if verbose:
      print(f'{DAY_OF_WEEK[today.weekday()]} (index {today.weekday()}) is a weekday, running a single update')
  elif today.weekday() == 4:
    # Fridays update the entire weekend (since it's known by that point)
    # In theory we could update monday if it's a DOW holiday -- but that's really complicated logic and I don't want to do it.
    # I could also just parse the NYSE holiday hours webpage.
    days = [today, today + datetime.timedelta(days=1), today + datetime.timedelta(days=2)]
    if verbose:
      print('Today is a Friday, so running a triple update for the weekend.')
  elif today.weekday() in [5, 6]:
    if verbose:
      print('Today is a weekend, so the geohashes were already computed Friday.')
    return

  # The Dow Jones Industrial Average opens with the New York Stock Exchange at 9:30 AM, Eastern Time.
  # The reporting for the value is usually available within two hours, so if we can't find an opening value by then,
  # assume it's a weekend or a holiday. See https://www.nyse.com/markets/hours-calendars for more precise holiday info.
  date = today.strftime('%Y-%m-%d')
  for _ in range(120):
    dow_opens = dow_jones.get_dow_jones_opens() # This samples 3 websites, and only reports data if >= 2 of them agree.
    if date in dow_opens:
      if verbose:
        print(f'Dow jones open found for {date}: {dow_opens[date]}')
      break
    if verbose:
      print(f'Did not find dow jones open for {date}: {dow_opens}, sleeping')
    time.sleep(60) # Sleep for 60 seconds

  # Now that the stock exchange has opened (and we have information about the dow jones), we can process geohashes.
  for page in pages:
    if verbose:
      print(f'Handling {page.title}...')
    config_contents = []
    talk_contents = []
    email_message = []

    config = parse_config(page.get_wiki_text())
    for day in days:
      day_name = DAY_OF_WEEK[day.weekday()]
      for (lat, long), data in config[day_name].items():
        (latitude, longitude, centicule) = get_geohash(dow_opens, day, long < -30)
        if centicule not in data:
          print(f'For day {day}, centicule {centicule} is not within the configured centicules:', ', '.join(data.keys()))
          continue

        if verbose:
          print(f'Found geohash on {day} within centicules for {page.title}: {lat, long, centicule}')

        date = day.strftime('%Y-%m-%d')
        expedition = Page(w, f'{date} {lat} {long}')
        map_link = f'https://maps.google.com/?q={lat}.{latitude},{long}.{longitude}'

        notifications = data[centicule]
        if notifications.get('config_page'):
          config_contents.append(f'\n=== [{expedition.get_edit_url()} {expedition.title}] ===')
          config_contents.append(f'[{map_link} Centicule {centicule}]')

        if notifications.get('talkpage'):
          talk_contents.append(f'\n== New geohashing site on {date} ==')
          talk_contents.append(f'See [[{page}]]')

        if notifications.get('email'):
          email_message.append(f'<h2>New geohashing site on {date}, in centicule {centicule}</h2>')
          email_message.append(f'Map link: <a href="{map_link}">{map_link}</a>')
          email_message.append(f'Config page: <a href="{page.get_page_url()}">{page.title}</a>')
          email_message.append(f'Expedition page: <a href="{expedition.get_edit_url()}">{expedition.title}</a>')

    # End 'for day in days'
    if config_contents:
      config = page.get_wiki_text()
      config += '\n'.join(config_contents)
      r = page.edit(config, bot=True, summary='Automatic update via https://github.com/jbzdarkid/geohashing')
      if verbose:
        print(f'Edited config page {page}: {r}')
    if talk_contents:
      talkpage_title = page.basename.split('/', 1)[0] # User:Darkid/Foo -> User:Darkid
      talkpage = Page(w, talkpage_title.replace('User:', 'User talk:'))
      talk = talkpage.get_wiki_text()
      talk += '\n'.join(talk_contents)
      r = talkpage.edit(talk, bot=True, summary='New geohash(es) in your centicule(s)')
      if verbose:
        print(f'Edited talkpage {talkpage}: {r}')
    if email_message:
      user = page.basename.split('/', 1)[0] # User:Darkid/Foo -> User:Darkid
      title = 'New geohash(es) in your centicule(s)'
      email = '<br>'.join(email_message)
      r = w.email_user(user, title, email)
      if verbose:
        print(f'Sent email to {user}: {r}')

if __name__ == '__main__':
  verbose = True
  w = Wiki('https://geohashing.site/api.php')

  eastern_time = zoneinfo.ZoneInfo('America/New_York')
  today = datetime.datetime.now(tz=eastern_time)

  main(w, today)
