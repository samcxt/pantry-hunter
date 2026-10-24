# Pantry Hunter v0.5

A static, mobile-friendly pantry stock-up app. Price results from third-party collectors should be independently verified before purchase.

## Live prices

Coles and Woolworths prices come from a weekly job on Sam's own Majordomo household system, not from anything in this repo. The app loads `https://pantry-feed.runsam.au/feed.js` on start (and on demand via **Check for updated prices**) and shows the date prices were collected, with a warning if that's more than eight days old. There is no Apify token, collector script or GitHub Actions workflow in this repo any more - that approach (see git history) got blocked scraping Coles/Woolworths directly, and the replacement collector lives outside this repo entirely, buying data from CrawlPlant's Apify actors instead of scraping.

Costco has no automated feed. Costco prices are entered once in Majordomo and travel to the app through the same weekly feed; refreshed every few months since they rarely change.

The staples list (35 items, pack sizes, target months, price ceilings) is also maintained in Majordomo, not here. This repo only hosts the front end.

## Hosting

This app is published through Sam's household static-app host on a Synology NAS, as `pantry-hunter.runsam.au` - not GitHub Pages. Publishing is: copy `index.html` into the app's folder on the host and republish. There is no build step.

Local preview: `python3 -m http.server 8000` in this folder, then open http://localhost:8000. Opening `index.html` directly may prevent the feed from loading (script-tag loads generally still work from `file://`, but a local server is more representative).

## Data rules

- `watchlist.json`/`catalogue.json` are historical references from this app's earlier iterations; Majordomo's `staples.json` is now the source of truth for the live feed.
- Live offers are matched to pantry items by id. CSV import still matches by item name + size (case-insensitive) and remains the manual fallback - columns `item,store,price,reference_price,size,url` plus an optional `date`.
- A buy recommendation requires a genuine special (or a price at/below its 30-day low), never a questionable one, under your price ceiling if you've set one, and cheaper than Costco per pack if a Costco price is on file. An item with too little price history yet is labelled rather than guessed at.
- Offers older than three days are not loaded from CSV. Availability, postcode-dependent pricing, purchase limits, delivery fees, multipacks and supermarket terms are not verified. No checkout automation.
- Settings and basket are browser-local; switching device/browser will not synchronise pantry preferences.

## CSV fallback

The original CSV import still works without an account or live feed, exactly as before.

## Testing

No automated tests remain in this repo - `test_collector.py` and `test_retailers.py` tested the removed Python collector and were deleted with it. `index.html` has no test suite; verify changes by hand in a browser.

## Retailers and shopping modes

Only **Coles, Woolworths and Costco** are compared. Coles/Woolworths are home-delivery options, Costco is a planned haul - factor membership, travel, freezer space and pack sizes into any stock-up decision. Aldi is excluded.
