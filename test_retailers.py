import pathlib, unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
class RetailerTests(unittest.TestCase):
 def test_collector_excludes_aldi(self):
  s=(ROOT/'scripts/collect.py').read_text()
  self.assertIn("['coles','woolworths']",s)
  self.assertNotIn("elif 'aldi'",s)
 def test_app_supports_costco(self):
  s=(ROOT/'index.html').read_text()
  self.assertIn("'Costco'",s)
  self.assertIn('canonicalStore(o.store)',s)
if __name__=='__main__': unittest.main()
