# Digital Stainless Steel Price List

A single-page web app for searching stainless steel and aluminum prices, generating Thai/English customer quotations, viewing price history, and managing products — all client-side, no backend or database required.

## Tech

Plain HTML/CSS/JavaScript. No build step, no framework, no server. `data.js` holds the product/price database as a JS object; `app.js` runs the search, quotation, and admin logic; admin edits are saved in the visitor's browser via `localStorage`.

## Run locally

Just open `index.html` in a browser, or serve it:

```bash
npx serve .
```

## Deploy to GitHub Pages

1. Push this folder to a GitHub repo.
2. In the repo, go to **Settings → Pages → Build and deployment → Source**, and choose **GitHub Actions**.
3. Push to `main` — the included workflow (`.github/workflows/deploy.yml`) builds and publishes the site automatically. Your app will be live at `https://<username>.github.io/<repo-name>/`.

No secrets, API keys, or environment variables are needed — the whole app is static files.

## Important: admin edits are per-browser

Because there's no backend, any price/product edits made in **Price Management** or via CSV import are saved only in the browser (device) that made them — they are *not* shared with other visitors or synced anywhere. Use **Export Data (JSON/CSV)** in Price Management to back up changes, and re-import or regenerate `data.js` (see below) to make edits visible to everyone.

To bake edits into the base dataset for all visitors, update `build_db.py` (or edit `data.js` directly) and commit the regenerated `data.js` — anything only saved via the in-browser admin UI stays local to that browser.

## Tests

```bash
npm install
npm test
```

Runs the jsdom-based test suite (`tests/`) covering search, quotation generation, admin add/edit, and CSV import.

## Files

- `index.html`, `app.js`, `style.css`, `data.js` — the app
- `build_db.py` — regenerates `data.js` from transcribed source price-list data
- `tests/` — automated test suite
