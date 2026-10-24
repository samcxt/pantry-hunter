import json, pathlib, unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
class Tests(unittest.TestCase):
 def test_watchlist_keys(self):
  rows=json.loads((ROOT/'watchlist.json').read_text());self.assertTrue(rows)
  for r in rows:
   self.assertTrue(all(k in r for k in ['item','size','query','required_terms']))
 def test_empty_feed_is_nonlive(self):
  d=json.loads((ROOT/'data/latest.json').read_text());self.assertIsNone(d['generated_at']);self.assertEqual(d['offers'],[])
if __name__=='__main__':unittest.main()
