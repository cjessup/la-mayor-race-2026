# LA Mayor Race 2026 — Live Results

A lightweight, real-time dashboard for the 2026 Los Angeles mayoral primary election results.

**🌐 Live site:** https://cjessup.github.io/la-mayor-race-2026/

- **Linear view**: Horizontal bar chart + per-candidate progress bars showing vote share.
- **Pie chart**: Visual distribution of the vote.
- **Auto-refresh**: Polls the official data every ~60 seconds.
- **Manual refresh**: Large, clearly visible "REFRESH NOW" button for instant updates.
- **Fully static** — the hosted version on GitHub Pages requires **no backend** at all (pure client-side JS + a public CORS proxy for the data feed). The included Python server is optional and only needed for convenient local development.

> **Note**: Results are unofficial and come directly from the Los Angeles County Registrar-Recorder/County Clerk. They will update as ballots are counted. The top two candidates advance to the November general election (unless one receives a majority).

## Live Site (GitHub Pages)

The site is hosted for free on GitHub Pages and works completely statically:

→ https://cjessup.github.io/la-mayor-race-2026/

All data fetching and parsing happens in the browser. A public CORS proxy (api.allorigins.win) is used so the page can reach the LA County JSON endpoint without CORS errors.

## Local Run (with optional Python server)

For local development you can still use the included server (recommended for devs because it avoids the 3rd-party CORS proxy and adds simple caching):

```bash
python server.py
```

Then open **http://localhost:8000** in your browser.

The server:
- Serves the static `index.html`
- Exposes `/api/results` (proxies + parses the county JSON feed)
- Caches upstream responses (~35s) to be polite to the public data source

You can also just open `index.html` directly in a browser — it will automatically fall back to fetching the data via the CORS proxy.

## Data Source

Official JSON feed:  
https://results.lavote.gov/electionresults/json?electionid=4338

The site extracts the contest titled **"LOS ANGELES CITY PRIMARY NOMINATING ELECTION Mayor"**.

## Tech Stack

- Backend: Python 3 stdlib (`http.server`, `urllib.request`, `threading`)
- Frontend: 
  - Tailwind CSS (via CDN)
  - Chart.js (via CDN) for bar + pie/doughnut charts
  - Vanilla JavaScript (no build step)
- No npm, no Flask/FastAPI, no external Python packages required

## Project Structure

```
.
├── .gitignore
├── README.md
├── index.html      # Self-contained UI + charts + polling logic
├── server.py       # Simple HTTP server + /api/results proxy
└── (no node_modules, no venv, no build artifacts)
```

## Development Notes

- When the page is served by `python server.py`, it prefers the local `/api/results` endpoint (nice caching + no external proxy).
- On GitHub Pages (or when opening the HTML file directly), the page fetches the full county JSON via a public CORS proxy and does the same parsing entirely in the browser. The slim shape expected by the UI is still produced.
- The client-side parser in `index.html` mirrors the logic that used to live only in `server.py`.
- Prominent candidates (Bass, Raman, Pratt) get distinct colors; the rest are grouped as "Others (N)".
- Works great even before any votes are reported (shows "awaiting results" state gracefully).

## License

MIT (or whatever you prefer for a small demo project).

---

Built to track the June 2, 2026 primary in real time. Data will become more interesting as the first batches of results are released by LA County!
