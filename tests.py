# A very light smattering of tests
import datetime
import inspect
import sys
from pathlib import Path
from unittest.mock import patch

import main

_id = 0
def get_id():
  global _id
  _id += 1
  return _id

class Tests:
  dow_opens = {
      '2024-05-07': 38858.94,
      '2024-05-06': 38762.43,
      '2024-05-03': 38709.36,
      '2024-05-02': 38075.65,
      '2024-05-01': 37845.56,
      '2024-04-30': 38337.40,
      '2024-04-29': 38282.16,
      '2024-04-26': 38114.70,
      '2024-04-25': 38052.09,
      '2024-04-24': 38552.79,
      '2024-04-23': 38356.07,
      '2024-04-22': 38116.89,
    }

  #############
  #!# Tests #!#
  #############
  def test_hashes(self):
    geohashes = main.get_geohashes(self.dow_opens, datetime.datetime(year=2024, month=5, day=07))
    # These values were independently confirmed with geohashing.info
    lat, long, cent = geohashes['2024-04-30')
    assert lat == '90233'
    assert long == '55186'
    assert cent == '95'

    lat, long, cent = geohashes['2024-05-01')
    assert lat == '9725225494237593'
    assert long == '987217588117626'
    assert cent == '99'

    lat, long, cent = geohashes['2024-05-04')
    assert lat == '86571'
    assert long == '46902'
    assert cent == '84'

if __name__ == '__main__':
  test_class = Tests()
  with patch('dow_jones.get_dow_jones_opens', new=test_class.mock_get_dow):

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

