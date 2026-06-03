# LA Mayor Race 2026 — Live Results

A lightweight, real-time dashboard for the 2026 Los Angeles mayoral primary election results.

- **Linear view**: Horizontal bar chart + per-candidate progress bars showing vote share.
- **Pie chart**: Visual distribution of the vote.
- **Auto-refresh**: Polls the official data every ~60 seconds.
- **Manual refresh**: Large, clearly visible "REFRESH NOW" button for instant updates.
- **Zero dependencies** for the backend (pure Python stdlib).

> **Note**: Results are unofficial and come directly from the Los Angeles County Registrar-Recorder/County Clerk. They will update as ballots are counted. The top two candidates advance to the November general election (unless one receives a majority).

## Live Demo / Local Run

```bash
python server.py
```

Then open **http://localhost:8000** in your browser.

The server:
- Serves the static `index.html`
- Exposes `/api/results` (proxies + parses the county JSON feed)
- Caches upstream responses (~35s) to be polite to the public data source

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

- The frontend calls `/api/results` which returns a slim JSON:
  ```json
  {
    "timestamp": "...",
    "totalVotes": 12345,
    "candidates": [
      { "name": "KAREN RUTH BASS", "party": "Non Partisan", "votes": 1234, "pct": 42.3 },
      ...
    ]
  }
  ```
- Prominent candidates (Bass, Raman, Pratt) get distinct colors; the rest are grouped as "Others (N)".
- Works great even before any votes are reported (shows "awaiting results" state gracefully).

## License

MIT (or whatever you prefer for a small demo project).

---

Built to track the June 2, 2026 primary in real time. Data will become more interesting as the first batches of results are released by LA County!
