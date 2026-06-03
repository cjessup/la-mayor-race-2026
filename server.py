#!/usr/bin/env python3
"""
Simple HTTP server for LA Mayor Race 2026 live results site.
Serves index.html and provides /api/results that proxies + filters the official
LA County JSON feed (https://results.lavote.gov/electionresults/json?electionid=4338).

Features:
- Caches upstream response for ~35 seconds to be respectful to the county endpoint.
- Extracts only the LA City Mayor contest.
- Returns clean JSON with total votes + per-candidate votes + computed %.
- Also serves any other static files in the directory (for future expansion).
"""

import json
import time
from datetime import datetime, timezone
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
import os
import threading

# Config
PORT = 8000
UPSTREAM_URL = "https://results.lavote.gov/electionresults/json?electionid=4338"
CACHE_TTL_SECONDS = 35
MAYOR_CONTEST_KEYWORDS = ["LOS ANGELES CITY PRIMARY NOMINATING ELECTION Mayor"]

# In-memory cache
_cache = {
    "data": None,
    "timestamp": 0,
    "lock": threading.Lock()
}


def fetch_upstream():
    """Fetch and return the full parsed JSON from LA County."""
    req = urllib.request.Request(
        UPSTREAM_URL,
        headers={
            "User-Agent": "LA-Mayor-Race-Results-Viewer/1.0 (+https://localhost)",
            "Accept": "application/json",
        }
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        raw = resp.read()
        return json.loads(raw)


def get_mayor_contest(full_data):
    """Locate the LA Mayor contest inside the big JSON and return its candidates list."""
    election = full_data.get("Election", {})
    for cg in election.get("ContestGroups", []):
        for contest in cg.get("Contests", []):
            title = contest.get("Title", "")
            if any(kw.lower() in title.lower() for kw in MAYOR_CONTEST_KEYWORDS):
                return contest
    return None


def build_results_payload(full_data):
    """Build the slim response the frontend expects."""
    contest = get_mayor_contest(full_data)
    if not contest:
        return {
            "timestamp": full_data.get("Timestamp"),
            "totalVotes": 0,
            "candidates": [],
            "error": "Mayor contest not found in feed",
            "lastChecked": datetime.now(timezone.utc).isoformat()
        }

    candidates_raw = contest.get("Candidates", [])
    total = sum(int(c.get("Votes", 0)) for c in candidates_raw)

    candidates = []
    for c in candidates_raw:
        votes = int(c.get("Votes", 0))
        pct = (votes / total * 100.0) if total > 0 else 0.0
        candidates.append({
            "name": c.get("Name", "Unknown"),
            "party": c.get("Party", "Non Partisan"),
            "votes": votes,
            "pct": round(pct, 2)
        })

    # Sort by votes desc for convenience
    candidates.sort(key=lambda x: x["votes"], reverse=True)

    payload = {
        "timestamp": full_data.get("Timestamp"),
        "totalVotes": total,
        "candidates": candidates,
        "contestTitle": contest.get("Title"),
        "source": "https://results.lavote.gov/",
        "lastChecked": datetime.now(timezone.utc).isoformat()
    }
    return payload


def get_cached_results():
    """Return (possibly fresh) results payload. Refreshes upstream only when cache expired."""
    now = time.time()
    with _cache["lock"]:
        if _cache["data"] and (now - _cache["timestamp"] < CACHE_TTL_SECONDS):
            return _cache["data"]

    # Need to fetch
    try:
        upstream = fetch_upstream()
        payload = build_results_payload(upstream)
        with _cache["lock"]:
            _cache["data"] = payload
            _cache["timestamp"] = now
        return payload
    except Exception as exc:
        print(f"[server] Upstream fetch failed: {exc}")
        # Return stale data if we have any, otherwise error payload
        with _cache["lock"]:
            if _cache["data"]:
                stale = dict(_cache["data"])
                stale["_stale"] = True
                return stale
        return {
            "timestamp": None,
            "totalVotes": 0,
            "candidates": [],
            "error": str(exc),
            "lastChecked": datetime.now(timezone.utc).isoformat()
        }


class LAElectionHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/index.html":
            self.serve_index()
        elif path == "/api/results":
            self.serve_api_results()
        elif path.startswith("/api/"):
            self.send_error(404, "API endpoint not found")
        else:
            # Try to serve other static files from cwd (css, etc if added later)
            self.serve_static(path.lstrip("/"))

    def serve_index(self):
        try:
            with open("index.html", "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.end_headers()
            self.wfile.write(content)
        except FileNotFoundError:
            self.send_error(500, "index.html not found — run from the project directory")

    def serve_api_results(self):
        payload = get_cached_results()
        body = json.dumps(payload, indent=2).encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def serve_static(self, filename):
        # Basic static file serving (only allow safe files)
        safe_extensions = (".html", ".css", ".js", ".json", ".ico", ".png", ".svg")
        if not filename or ".." in filename or not filename.lower().endswith(safe_extensions):
            self.send_error(404)
            return

        if not os.path.exists(filename):
            self.send_error(404)
            return

        try:
            with open(filename, "rb") as f:
                content = f.read()

            # crude mime
            if filename.endswith(".css"):
                ctype = "text/css"
            elif filename.endswith(".js"):
                ctype = "application/javascript"
            elif filename.endswith(".json"):
                ctype = "application/json"
            else:
                ctype = "application/octet-stream"

            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Cache-Control", "public, max-age=120")
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error(500, str(e))

    def log_message(self, format, *args):
        # Quieter logging
        print(f"[server] {self.address_string()} - {args[0]}")


def run_server(port=PORT):
    server_address = ("", port)
    httpd = HTTPServer(server_address, LAElectionHandler)
    print("=" * 60)
    print("LA MAYOR RACE 2026 — LIVE RESULTS SERVER")
    print("=" * 60)
    print(f"Serving on http://localhost:{port}")
    print(f"  • Open http://localhost:{port} in your browser")
    print(f"  • API: http://localhost:{port}/api/results")
    print(f"  • Polling official feed every {CACHE_TTL_SECONDS}s (client polls ~60s)")
    print("Press Ctrl+C to stop.\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        httpd.server_close()


if __name__ == "__main__":
    run_server()