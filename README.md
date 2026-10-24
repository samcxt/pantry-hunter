# Pantry Hunter v0.2

A static, mobile-friendly pantry stock-up app with a scheduled supermarket-price feed. It **does not yet have a live feed** until you supply an Apify token and deploy it. Price results from third-party collectors should be independently verified before purchase.

## Activate live prices (GitHub Pages)

1. Create an Apify account and confirm the [fairfetch Australian supermarket actor](https://apify.com/fairfetch/au-supermarket-prices) is available and its input/output schema still matches the configured collector. This is a third-party service, not an official supermarket API; charges and reliability may change.
2. Upload this folder's contents to a **new GitHub repository**. For GitHub Pages deployment, use a **public repository** (published price JSON will be public; no token is published).
3. In repository **Settings → Secrets and variables → Actions**, create a secret named `APIFY_TOKEN` with your token.
4. In repository **Settings → Actions → General**, ensure workflows have read/write permissions, or configure job permissions to allow pushing updates. The included workflow requests `contents: write`.
5. In **Actions → Update pantry prices → Run workflow**, trigger the first collection. Inspect logs and `data/latest.json`. If results don't match the expected schema, adjust `scripts/collect.py` before relying on prices.
6. In **Settings → Pages**, publish from the `main` branch `/ (root)`. Visit the Pages link (HTTPS) and press **Check for updated prices**. The workflow schedules a daily run (GitHub can delay or suspend scheduled jobs).

Local preview: `python3 -m http.server 8000` in this folder, then open http://localhost:8000. Opening `index.html` directly may prevent network feed reads. To collect locally: `APIFY_TOKEN=... python3 scripts/collect.py`; never put a token in `index.html` or commit a `.env` file.

## Data rules

- `watchlist.json` defines search queries and required/excluded title terms. Matching requires all configured terms; **verify matches and package sizes** because a substring match is not a guarantee of equivalent products.
- `data/latest.json` stores matched offers and their reference price; `data/history.json` retains up to 180 days of daily snapshots.
- Before at least four historical daily observations, reference price uses retailer-provided crossed-out price if available, otherwise current price. Thus a recommendation may legitimately be **zero**. After that, an observed-history median is used.
- This is **not** a guarantee that the historical median represents the correct normal price; a stable discount/price-change will affect it. Historical comparisons are within item/size/store.
- Offers older than three days are not loaded. Availability, postcode-dependent pricing, purchase limits, delivery fees, multipacks and supermarket terms are not verified. No checkout automation.
- Settings and basket are browser-local; switching device/browser will not synchronize pantry preferences.
- The scheduled collector is separate from the app and requires an API subscription/credits. No API secrets live in the front end.

## CSV fallback

The original CSV import still works without an account or live feed. Price CSV columns: `item,store,price,reference_price,size,url,date`.

## Testing

`python3 -m unittest discover -s tests -v`

## Household catalogue (v0.3)
- `catalogue.json` contains 35 staples supplied by the household. Initial inventory, monthly use, and price ceiling default to zero (unknown); **pack sizes are provisional** until confirmed.
- `watchlist.json` contains one preliminary search rule per item. Review retailer-specific naming and pack sizes before enabling automated purchases or trusting matching. Broad terms may return false positives.
- The My Pantry panel has an educational alternative-brand dialog, including an explicitly dated baked-beans price comparison (not a live price). Future version should collect equivalent SKUs and compare prices per 100g/100mL while preserving the household's approval of substitutions.
- Cheese: hard tasty/cheddar blocks can be frozen, although texture may become crumbly; best for cooking or grating after thawing in the refrigerator.

## Custom domain

This repository includes `CNAME` set to `pantry.runsam.au` for GitHub Pages. Once the repository is created and Pages is enabled for the `main` branch root, set the custom domain in **Settings → Pages** to `pantry.runsam.au`. In the `runsam.au` DNS zone add a CNAME record for the `pantry` subdomain pointing to `samcxt.github.io` (not the repository-specific path). Once DNS resolves and GitHub provisions a certificate, enable **Enforce HTTPS**. Do not change existing records for other subdomains. A published GitHub Pages site remains public even if access to source changes.

## Retailers and shopping modes (v0.4)

Only **Coles, Woolworths and Costco** are compared. The scheduled Apify collector requests Coles and Woolworths only. **Costco is not claimed as automated**: import known Costco unit-equivalent prices via CSV until a dependable warehouse price feed exists. Costco multipacks should be normalised to comparable sizes before recommendation; factor membership, travel, freezer space and pack sizes into any stock-up decision. Coles/Woolworths are home-delivery options, Costco is a planned haul. Aldi is excluded.
