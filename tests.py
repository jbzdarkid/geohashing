# A very light smattering of tests
import datetime
import inspect
import os
import sys

import main
import dow_jones

_id = 0
def get_id():
  global _id
  _id += 1
  return _id

class MockPage:
  def __init__(self, wiki, title):
    self.title = title
    self.wikitext = f'default for {self.title}'

  def get_wiki_text(self):
    return self.wikitext

  def get_edit_url(self):
    return 'https://edit.url/' + self.title.replace(' ', '_')

  def edit(self, contents, **kwargs):
    self.wikitext = contents

class MockWiki:
  def __init__(self):
    self.category_pages = []

  def get_all_category_pages(self, *args, **kwargs):
    return self.category_pages

  def login(self, username, password):
    return True

class Tests:
  dow_opens = {
      '2024-05-07': '38858.94',
      '2024-05-06': '38762.43',
      '2024-05-03': '38709.36',
      '2024-05-02': '38075.65',
      '2024-05-01': '37845.56',
      '2024-04-30': '38337.40',
      '2024-04-29': '38282.16',
      '2024-04-26': '38114.70',
      '2024-04-25': '38052.09',
      '2024-04-24': '38552.79',
      '2024-04-23': '38356.07',
      '2024-04-22': '38116.89',
    }

  #############
  #!# Tests #!#
  #############
  def test_hashes(self):
    # These values were independently confirmed with geohashing.info
    lat, long, cent = main.get_geohash(self.dow_opens, datetime.datetime(2024, 4, 30))
    assert lat == '9023250203492802'
    assert long == '5518558190767081'
    assert cent == '95'

    lat, long, cent = main.get_geohash(self.dow_opens, datetime.datetime(2024, 5, 1))
    assert lat == '9725225494237593'
    assert long == '987217588117626'
    assert cent == '99'

    lat, long, cent = main.get_geohash(self.dow_opens, datetime.datetime(2024, 5, 4))
    assert lat == '8657127823310143'
    assert long == '4690159903840444'
    assert cent == '84'

    lat, long, cent = main.get_geohash(self.dow_opens, datetime.datetime(2024, 5, 6))
    assert lat == '07702675125845192'
    assert long == '965342070246618'
    assert cent == '09'

  def test_hashes_30w(self):
    # These values were independently confirmed with geohashing.info
    lat, long, cent = main.get_geohash(self.dow_opens, datetime.datetime(2024, 4, 30, tzinfo=datetime.timezone.utc), w30 = False)
    assert lat == '1352540080910259'
    assert long == '9037177752203457'
    assert cent == '19'

    lat, long, cent = main.get_geohash(self.dow_opens, datetime.datetime(2024, 5, 1, tzinfo=datetime.timezone.utc), w30 = False)
    assert lat == '915065169318582'
    assert long == '4317648130720158'
    assert cent == '94'

    lat, long, cent = main.get_geohash(self.dow_opens, datetime.datetime(2024, 5, 4, tzinfo=datetime.timezone.utc), w30 = False)
    assert lat == '8657127823310143'
    assert long == '4690159903840444'
    assert cent == '84'

    lat, long, cent = main.get_geohash(self.dow_opens, datetime.datetime(2024, 5, 6, tzinfo=datetime.timezone.utc), w30 = False)
    assert lat == '06277180306206916'
    assert long == '5890366767633993'
    assert cent == '05'

  def test_parse_config(self):
    text = '''
    {| border="1" cellpadding="5" cellspacing="0"
    |-
    !Latitude!!Longitude!!Centicule!!Message!!Settings
    |-
    | 47 || -122 || 50 51 52 60 61 62 70 71 72 || || Email, Saturday
    |-
    | 47 || -122 || 61 || ||
    |}
    '''

    config = main.parse_config(text)
    assert len(config) == 7
    for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'sunday']:
      assert config[day] == {(47, -122): {'61': {'config_page': True}}}

    assert len(config['saturday'][(47, -122)]) == 9
    assert config['saturday'][(47, -122)]['50'] == {'email': True, 'config_page': True}
    assert config['saturday'][(47, -122)]['61'] == {'email': True, 'config_page': True}

  def test_dow_quorum(self):
    source1 = [(datetime.datetime(2020, 1, 1), 100)]
    source2 = [(datetime.datetime(2020, 1, 1), 100)]
    source3 = [(datetime.datetime(2020, 1, 1), 100)]
    dow_jones.dow_sources = [lambda: source1, lambda: source2, lambda: source3]

    assert dow_jones.get_dow_jones_opens() == {'2020-01-01': 100}

    source1 = [(datetime.datetime(2020, 1, 1), 101)]
    assert dow_jones.get_dow_jones_opens() == {'2020-01-01': 100}

    source2 = [(datetime.datetime(2020, 1, 1), 101)]
    assert dow_jones.get_dow_jones_opens() == {'2020-01-01': 101}

    source1 = [(datetime.datetime(2020, 1, 1), 102)]
    assert dow_jones.get_dow_jones_opens() == {}

    source3 = [(datetime.datetime(2020, 1, 1), 102)]
    assert dow_jones.get_dow_jones_opens() == {'2020-01-01': 102}

    source2 = [(datetime.datetime(2020, 1, 2), 103)]
    assert dow_jones.get_dow_jones_opens() == {'2020-01-01': 102}

    source1 = []
    assert dow_jones.get_dow_jones_opens() == {}

    source2 = []
    assert dow_jones.get_dow_jones_opens() == {}

    source3 = []
    assert dow_jones.get_dow_jones_opens() == {}

  def test_parse_config_cents(self):
    text = '''
    | 1 || 2 || 03 04 05 06          || || Monday
    | 1 || 2 ||    04 05 06 07       || || Monday, Email
    | 1 || 2 ||       05 06 07 08    || || Monday, Tuesday
    | 1 || 2 ||          06 07 08 09 || || Monday, Tuesday, Talkpage
    '''
    config = main.parse_config(text)
    assert len(config) == 2

    assert len(config['monday']) == 1
    assert len(config['monday'][(1, 2)]) == 7
    assert config['monday'][(1, 2)]['03'] == {'config_page': True}
    assert config['monday'][(1, 2)]['04'] == {'config_page': True, 'email': True}
    assert config['monday'][(1, 2)]['05'] == {'config_page': True, 'email': True}
    assert config['monday'][(1, 2)]['06'] == {'config_page': True, 'email': True, 'talkpage': True}
    assert config['monday'][(1, 2)]['07'] == {'config_page': True, 'email': True, 'talkpage': True}
    assert config['monday'][(1, 2)]['08'] == {'config_page': True,                'talkpage': True}
    assert config['monday'][(1, 2)]['09'] == {'config_page': True,                'talkpage': True}

    assert len(config['tuesday'][(1, 2)]) == 5
    assert config['tuesday'][(1, 2)]['05'] == {'config_page': True}
    assert config['tuesday'][(1, 2)]['06'] == {'config_page': True, 'talkpage': True}
    assert config['tuesday'][(1, 2)]['07'] == {'config_page': True, 'talkpage': True}
    assert config['tuesday'][(1, 2)]['08'] == {'config_page': True, 'talkpage': True}
    assert config['tuesday'][(1, 2)]['09'] == {'config_page': True, 'talkpage': True}

  def test_end2end(self):
    source1 = [(datetime.datetime(2020, 1, 1), '100')]
    source2 = [(datetime.datetime(2020, 1, 1), '100')]
    source3 = [(datetime.datetime(2020, 1, 1), '100')]
    dow_jones.dow_sources = [lambda: source1, lambda: source2, lambda: source3]

    os.environ['WIKI_USERNAME'] = 'mock_username'
    os.environ['WIKI_PASSWORD'] = 'mock_password'

    main.Page = MockPage

    wiki = MockWiki()
    page = MockPage(wiki, 'category_page')
    page.wikitext = '| 1 || 2 || 28'
    wiki.category_pages = [page]
    today = datetime.datetime(2020, 1, 1, 13, 30, tzinfo=datetime.timezone.utc)
    main.main(wiki, today)

    expected = '\n'.join([
      '| 1 || 2 || 28',
      '=== [https://edit.url/2020-01-01_1_2 2020-01-01 1 2] ===',
      '[https://maps.google.com/?q=1.27537086088503215,2.857575622080932 Centicule 28]',
    ])
    assert page.wikitext == expected

if __name__ == '__main__':
  test_class = Tests()

  def is_test(method):
    return inspect.ismethod(method) and method.__name__.startswith('test')
  tests = list(inspect.getmembers(test_class, is_test))
  tests.sort(key=lambda func: func[1].__code__.co_firstlineno)

  for test in tests:
    if len(sys.argv) > 1: # Requested specific test(s)
      if test[0] not in sys.argv[1:]:
        continue

    # Test setup

    # Run test
    print('---', test[0], 'started')
    try:
      test[1]()
    except Exception:
      print('!!!', test[0], 'failed:')
      import traceback
      traceback.print_exc()
      sys.exit(-1)

    print('===', test[0], 'passed')
  print('\nAll tests passed')
