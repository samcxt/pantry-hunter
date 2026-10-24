#!/usr/bin/env python3
"""Free, bounded Coles/Woolworths product price monitor; no paid Apify services.
Uses retail websites' publicly exposed product search endpoints. Fail closed: do not
publish if neither retailer returns plausible products. This may break when retailer
endpoints change, and should be checked against storefront before relying on prices.
"""
import datetime as dt
import json
import os
import pathlib
import re
import time
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
RULES = json.loads((ROOT / 'watchlist.json').read_text())
NOW = dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')
# Up to 35 queries x 2 stores: no category-wide scraping, paid usage or proxy.
LIMIT = min(35, max(1, int(os.getenv('PANTRY_QUERY_LIMIT', '35'))))
STORE_TIMEOUT = 10
HEADERS = {'User-Agent': 'PantryHunter/0.5 (+personal pantry price watch)', 'Accept': 'application/json'}

def get(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=STORE_TIMEOUT) as response:
        return json.load(response)

def numeric(x):
    if isinstance(x, dict): x = x.get('Value', x.get('value', x.get('amount')))
    try: return float(x)
    except (TypeError, ValueError): return None

def normal(x): return ' '.join(re.findall(r'[a-z0-9]+', str(x or '').lower()))

def matches(name, size, rule):
    title = normal(name + ' ' + size)
    return all(normal(t) in title for t in rule['required_terms']) and not any(normal(t) in title for t in rule.get('exclude_terms', []))

def woolworths(q):
    url='https://www.woolworths.com.au/apis/ui/Search/products?' + urllib.parse.urlencode({'searchTerm':q,'pageSize':5})
    data=get(url)
    groups=data.get('Products', []) if isinstance(data,dict) else []
    for group in groups:
        for p in group.get('Products', [group]):
            code=p.get('Stockcode')
            if code:
                yield {'store':'Woolworths','name':p.get('DisplayName') or p.get('Name') or '',
                       'size':p.get('PackageSize') or '', 'price':numeric(p.get('Price') or p.get('InstorePrice')),
                       'was':numeric(p.get('WasPrice')),
                       'url':f'https://www.woolworths.com.au/shop/productdetails/{code}'}

def coles(q):
    url='https://www.coles.com.au/api/products/v2/search?' + urllib.parse.urlencode({'query':q,'page':1,'pageSize':5})
    data=get(url)
    rows=(data.get('results') or data.get('products') or data.get('items') or []) if isinstance(data,dict) else []
    # Do not guess a price if the API changes shape.
    for p in rows:
        if not isinstance(p,dict): continue
        pricing=p.get('pricing') or {}
        if not isinstance(pricing,dict): pricing={}
        name=p.get('name') or p.get('title') or p.get('displayName') or ''
        ident=p.get('id') or p.get('productId')
        url=p.get('url') or (f'/product/{ident}' if ident else '')
        if url.startswith('/'): url='https://www.coles.com.au'+url
        yield {'store':'Coles','name':name,'size':p.get('size') or p.get('packageSize') or '',
               'price':numeric(pricing.get('now') or pricing.get('price') or p.get('price') or p.get('retailPrice')),
               'was':numeric(pricing.get('was') or p.get('wasPrice')),
               'url':url}

def main():
    found=[]; failures=[]
    queries=RULES[:LIMIT]
    for rule in queries:
        for label,fn in [('Woolworths',woolworths),('Coles',coles)]:
            try:
                rows=list(fn(rule['query']))
                for p in rows:
                    if not p['price'] or p['price']<=0 or not matches(p['name'],p['size'],rule): continue
                    found.append({'item':rule['item'],'size':rule['size'],'store':label,'price':p['price'],
                                  'was_price':p['was'] if p['was'] and p['was']>p['price'] else None,
                                  'url':p['url'],'date':NOW,'source':'retailer-web-api',
                                  'product_title':p['name']})
            except Exception as exc:
                failures.append(f"{label}: {rule['item']}: {type(exc).__name__}: {exc}")
            time.sleep(0.15)
    best={}
    for p in found:
        key=(p['item'],p['size'],p['store'])
        if key not in best or p['price']<best[key]['price']: best[key]=p
    out=list(best.values())
    if not out:
        print('\n'.join(failures[:12]))
        raise SystemExit('No verified product prices: existing published feed left untouched.')
    history_path=ROOT/'history.json'
    try: history=json.loads(history_path.read_text())
    except (OSError,ValueError): history=[]
    for p in out:
        prior=sorted(h['price'] for h in history if h.get('item')==p['item'] and h.get('size')==p['size'] and h.get('store')==p['store'] and h.get('date','')[:10]!=NOW[:10])
        p['reference_price']=round(prior[len(prior)//2],2) if len(prior)>=4 else (p['was_price'] or p['price'])
        p['reference_basis']='historical_median' if len(prior)>=4 else ('retailer_was' if p['was_price'] else 'no_reference')
    keys={(p['item'],p['size'],p['store'],NOW[:10]) for p in out}
    history=[h for h in history if (h.get('item'),h.get('size'),h.get('store'),h.get('date','')[:10]) not in keys]
    history+=out
    cutoff=dt.datetime.now(dt.timezone.utc)-dt.timedelta(days=180)
    history=[h for h in history if dt.datetime.fromisoformat(h['date'].replace('Z','+00:00'))>=cutoff]
    (ROOT/'latest.json').write_text(json.dumps({'generated_at':NOW,'provider':'direct-retailer-apis','offers':out},indent=2)+'\n')
    history_path.write_text(json.dumps(history,indent=2)+'\n')
    print(f'Published {len(out)} prices; endpoint errors: {len(failures)}')
    if failures: print('\n'.join(failures[:5]))

if __name__=='__main__': main()
