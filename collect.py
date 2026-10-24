#!/usr/bin/env python3
"""Collect supermarket prices through Apify, keep rolling history and publish public feed.
Only exact, explicitly configured brand/size matches are eligible for recommendations.
"""
import json, os, re, sys, urllib.request, datetime, pathlib
from collections import defaultdict
ROOT=pathlib.Path(__file__).resolve().parent
DATA=ROOT
CONFIG=json.loads((ROOT/'watchlist.json').read_text())
TODAY=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
ACTOR=os.getenv('APIFY_ACTOR','fairfetch~au-supermarket-prices')
TOKEN=os.getenv('APIFY_TOKEN')
if not TOKEN: sys.exit('Set APIFY_TOKEN in environment (GitHub Actions secret).')
queries=list(dict.fromkeys(x['query'] for x in CONFIG))
body={'retailers':['coles','woolworths'],'searchQueries':queries,'maxItemsPerQuery':30,'proxyConfiguration':{'useApifyProxy':True}}
url=f'https://api.apify.com/v2/acts/{ACTOR}/run-sync-get-dataset-items?format=json&timeout=240'
request=urllib.request.Request(url,data=json.dumps(body).encode(),headers={'Authorization':'Bearer '+TOKEN,'Content-Type':'application/json'},method='POST')
try:
    with urllib.request.urlopen(request,timeout=270) as resp: raw=json.load(resp)
except Exception as e: sys.exit(f'Apify request failed (existing published feed preserved): {e}')
if not isinstance(raw,list) or not raw: sys.exit('No product rows returned; preserving existing feed')

def pick(obj,*keys):
    for key in keys:
        value=obj.get(key)
        if value is not None and value!='': return value
    return None

def number(v):
    if isinstance(v,dict): v=pick(v,'value','amount','price')
    try: return float(re.sub(r'[^\d.]','',str(v)))
    except (ValueError,TypeError): return None

def norm(s): return re.sub(r'\s+',' ',re.sub(r'[^a-z0-9]+',' ',str(s or '').lower())).strip()

def valid(row,rule):
    title=norm(' '.join(str(pick(row,k) or '') for k in ['name','title','productName','brand','size','packageSize']))
    return all(norm(t) in title for t in rule['required_terms']) and not any(norm(t) in title for t in rule.get('exclude_terms',[]))

out=[]; seen=set()
for row in raw:
    if not isinstance(row,dict): continue
    store=norm(pick(row,'retailer','store','supermarket','source'))
    if 'woolworth' in store: store='Woolworths'
    elif 'coles' in store: store='Coles'
    else: continue
    price=number(pick(row,'price','currentPrice','salePrice','current_price'))
    if price is None or price<=0 or price>10000: continue
    was=number(pick(row,'wasPrice','originalPrice','was_price','regularPrice','rrp'))
    link=pick(row,'url','productUrl','product_url','link') or ''
    if link and not str(link).startswith(('https://','http://')): link=''
    for rule in CONFIG:
        if not valid(row,rule): continue
        key=(rule['item'],store,str(pick(row,'id','productId','barcode','url','name')))
        if key in seen: continue
        seen.add(key)
        out.append({'item':rule['item'],'size':rule['size'],'store':store,'price':price,'was_price':was if was and was>price else None,'url':link,'date':TODAY,'source':'apify','product_title':pick(row,'name','title','productName') or ''})
if not out: sys.exit('No watchlist products matched. Preserving existing feed.')
history_file=DATA/'history.json'
try: history=json.loads(history_file.read_text())
except (FileNotFoundError,ValueError): history=[]
# Keep one observation per retailer / item per calendar day; for duplicates retain cheapest matched listing.
best={}
for p in out:
    key=(p['item'],p['size'],p['store'])
    if key not in best or p['price']<best[key]['price']: best[key]=p
out=list(best.values())
for p in out:
    previous=[h['price'] for h in history if h['item']==p['item'] and h['size']==p['size'] and h['store']==p['store'] and h['date'][:10]!=TODAY[:10]]
    # Established history beats retailer crossed-out anchor; don't fabricate a discount from one observation.
    p['reference_price']=round(sorted(previous)[len(previous)//2],2) if len(previous)>=4 else (p['was_price'] or p['price'])
    p['reference_basis']='historical_median' if len(previous)>=4 else ('retailer_was' if p['was_price'] else 'no_reference')
newkeys={(p['item'],p['size'],p['store'],p['date'][:10]) for p in out}
history=[h for h in history if (h['item'],h['size'],h['store'],h['date'][:10]) not in newkeys]
history+=out
cutoff=datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(days=180)
history=[h for h in history if datetime.datetime.fromisoformat(h['date'].replace('Z','+00:00'))>=cutoff]
# Avoid publishing raw API response, which may include irrelevant products.
(DATA/'latest.json').write_text(json.dumps({'generated_at':TODAY,'provider':ACTOR,'offers':out},indent=2)+'\n')
history_file.write_text(json.dumps(history,indent=2)+'\n')
print(f'Published {len(out)} matched offers across {len(raw)} source rows; {len(history)} history points')
