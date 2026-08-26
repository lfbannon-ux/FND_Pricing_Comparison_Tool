#!/usr/bin/env python3
"""
Phase 1 downloader for Rockpoint Gas Storage Inc. (TSX: RGSI).

Runs the moment the environment's egress allowlist admits the filing hosts.
Downloads EVERYTHING before a single number is extracted, audits every output
file, and converts each filing to clean greppable text with tables preserved.

Usage:
    python3 scripts/fetch_primary.py --check          # probe reachability only
    python3 scripts/fetch_primary.py                  # download + audit + convert

Design rules (from the brief):
  * declared User-Agent on every request, >=0.3s between requests, sequential per host
  * keep the RAW bytes; render/parse only from LOCAL files, never live URLs
  * audit every output: magic bytes, page count, block-page signatures
  * uniform file size across different years is a red flag -> reported
  * never bypass logins, paywalls or cookie walls beyond clicking "accept"
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import requests

UA = "Rockpoint Historical Model Build lfbannon@gmail.com"
SLEEP = 0.35
TIMEOUT = 60

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "filings"
TEXT = ROOT / "text"
LOGS = ROOT / "logs"

# Block-page signatures. A 200 response containing any of these is NOT a filing.
BLOCK_SIGNATURES = [
    b"Undeclared Automated Tool",
    b"Request Rate Threshold Exceeded",
    b"Your Request Originates from an Undeclared",
    b"Please enable JavaScript",
    b"Access Denied",
    b"Just a moment...",          # Cloudflare interstitial
    b"cf-browser-verification",
    b"<title>403",
]

# ---------------------------------------------------------------------------
# Targets. SEDAR+ requires a session-driven search, so the issuer IR mirror --
# which publishes its SEDAR filings at stable paths -- is the primary route,
# with SEDAR+ as the authoritative cross-check.
# ---------------------------------------------------------------------------

@dataclass
class Target:
    key: str
    url: str
    fiscal_period: str
    doc_type: str
    notes: str = ""
    dest: Path = field(init=False)

    def __post_init__(self) -> None:
        suffix = ".pdf" if ".pdf" in self.url.lower() else ".html"
        self.dest = RAW / "ir" / f"{self.key}{suffix}"


TARGETS: list[Target] = [
    Target(
        key="FY2026_IPO_prospectus",
        url="https://www.rockpointgs.com/docs/investorrelations/SEDAR/Final_Base_PREP_Prospectus_ENG.pdf",
        fiscal_period="FY2023-FY2025",
        doc_type="ipo_prospectus",
        notes="Supplemented PREP prospectus dated 2025-10-08. SOLE source of "
              "as-originally-reported FY2023/FY2024/FY2025 history. HIGHEST PRIORITY.",
    ),
]

# Hosts to probe before attempting anything.
PROBE_HOSTS = [
    "https://www.rockpointgs.com/",
    "https://rockpointgs.com/",
    "https://www.sedarplus.ca/landingpage/",
    "https://files.quartr.com/",
]


def session() -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,application/pdf,*/*",
        "Accept-Language": "en-CA,en;q=0.9",
    })
    return s


def probe(s: requests.Session) -> dict[str, str]:
    """Report reachability per host. Distinguishes policy denial from real errors."""
    out: dict[str, str] = {}
    for url in PROBE_HOSTS:
        try:
            r = s.get(url, timeout=20, stream=True)
            out[url] = f"HTTP {r.status_code}"
            r.close()
        except requests.exceptions.ProxyError as e:
            out[url] = f"EGRESS-BLOCKED (proxy denied CONNECT): {type(e).__name__}"
        except Exception as e:  # noqa: BLE001
            out[url] = f"ERROR {type(e).__name__}: {e}"
        time.sleep(SLEEP)
    return out


def audit(path: Path) -> tuple[bool, str]:
    """Audit a downloaded file. Returns (ok, reason)."""
    if not path.exists():
        return False, "missing"
    data = path.read_bytes()
    if len(data) < 2048:
        return False, f"suspiciously small ({len(data)} bytes)"
    for sig in BLOCK_SIGNATURES:
        if sig in data[:200_000]:
            return False, f"block-page signature present: {sig.decode(errors='replace')!r}"
    if path.suffix == ".pdf":
        if not data.startswith(b"%PDF-"):
            return False, "not a PDF (bad magic bytes)"
        try:
            import pymupdf
            with pymupdf.open(path) as doc:
                n = doc.page_count
            if n <= 3:
                return False, f"page count {n} <= 3"
            return True, f"ok, {n} pages, {len(data):,} bytes"
        except Exception as e:  # noqa: BLE001
            return False, f"unreadable PDF: {e}"
    return True, f"ok, {len(data):,} bytes"


def download(s: requests.Session, t: Target) -> tuple[bool, str]:
    t.dest.parent.mkdir(parents=True, exist_ok=True)
    if t.dest.exists():
        ok, why = audit(t.dest)
        if ok:
            return True, f"already present ({why})"
    try:
        r = s.get(t.url, timeout=TIMEOUT)
    except requests.exceptions.ProxyError:
        return False, "EGRESS-BLOCKED (proxy denied CONNECT)"
    except Exception as e:  # noqa: BLE001
        return False, f"ERROR {type(e).__name__}: {e}"
    finally:
        time.sleep(SLEEP)
    if r.status_code != 200:
        return False, f"HTTP {r.status_code}"
    t.dest.write_bytes(r.content)
    return audit(t.dest)


# ---------------------------------------------------------------------------
# Text conversion: tables preserved as `col | col | col` between [TABLE] markers.
# Extraction agents grep captions here and read narrow line ranges -- far cheaper
# and more reliable than paging through the PDF.
# ---------------------------------------------------------------------------

def pdf_to_text(src: Path, dst: Path) -> int:
    import pymupdf

    dst.parent.mkdir(parents=True, exist_ok=True)
    parts: list[str] = []
    with pymupdf.open(src) as doc:
        for pno, page in enumerate(doc, start=1):
            parts.append(f"\n[PAGE {pno}]\n")
            try:
                tables = page.find_tables()
            except Exception:  # noqa: BLE001
                tables = None
            table_boxes = []
            if tables and tables.tables:
                for tb in tables.tables:
                    table_boxes.append(tb.bbox)
                    parts.append("[TABLE]\n")
                    for row in tb.extract():
                        cells = ["" if c is None else re.sub(r"\s+", " ", str(c)).strip()
                                 for c in row]
                        parts.append(" | ".join(cells) + "\n")
                    parts.append("[/TABLE]\n")
            # narrative text outside detected tables
            for block in page.get_text("blocks"):
                x0, y0, x1, y1, txt = block[0], block[1], block[2], block[3], block[4]
                if any(x0 >= b[0] - 2 and y0 >= b[1] - 2 and x1 <= b[2] + 2 and y1 <= b[3] + 2
                       for b in table_boxes):
                    continue
                txt = re.sub(r"[ \t]+", " ", txt).strip()
                if txt:
                    parts.append(txt + "\n")
    dst.write_text("".join(parts), encoding="utf-8")
    return len(parts)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="probe reachability and exit")
    args = ap.parse_args()

    LOGS.mkdir(parents=True, exist_ok=True)
    s = session()

    print("== Reachability probe ==")
    results = probe(s)
    for url, status in results.items():
        print(f"  {url:<45} {status}")
    reachable = any("HTTP 2" in v or "HTTP 3" in v for v in results.values())
    if args.check:
        return 0 if reachable else 2
    if not reachable:
        print("\nNo filing host is reachable. This is an egress-policy denial, not a "
              "transient error -- see filings/UNOBTAINED.md. Nothing downloaded.")
        return 2

    print("\n== Download ==")
    rows = []
    for t in TARGETS:
        ok, why = download(s, t)
        flag = "OK " if ok else "FAIL"
        print(f"  [{flag}] {t.key}: {why}")
        rows.append({
            "key": t.key, "fiscal_period": t.fiscal_period, "doc_type": t.doc_type,
            "url": t.url, "dest": str(t.dest.relative_to(ROOT)) if t.dest.exists() else "",
            "ok": int(ok), "audit": why,
            "sha256": hashlib.sha256(t.dest.read_bytes()).hexdigest() if t.dest.exists() else "",
            "notes": t.notes,
        })

    # Uniform-size red flag
    sizes = [t.dest.stat().st_size for t in TARGETS if t.dest.exists()]
    if len(sizes) > 1 and len(set(sizes)) == 1:
        print("  !! RED FLAG: every downloaded file is exactly the same size -- "
              "likely all block pages. Investigate before extracting.")

    print("\n== Text conversion (from LOCAL files only) ==")
    for t in TARGETS:
        if not t.dest.exists():
            continue
        ok, _ = audit(t.dest)
        if not ok:
            print(f"  [SKIP] {t.key}: failed audit, not converting")
            continue
        if t.dest.suffix == ".pdf":
            out = TEXT / f"{t.key}.txt"
            n = pdf_to_text(t.dest, out)
            print(f"  [OK ] {t.key} -> {out.relative_to(ROOT)} ({n} blocks)")

    with (LOGS / "fetch_manifest.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"\nWrote {LOGS / 'fetch_manifest.csv'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
