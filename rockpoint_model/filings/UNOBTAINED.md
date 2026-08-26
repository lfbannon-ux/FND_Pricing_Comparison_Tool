# Documents NOT obtained, and why

Recorded per SPEC rule 10 and the brief's Phase 1 requirement to note explicitly anything that could not be obtained.

## Blocked by this environment's network egress policy
Every filing archive returns `403` at the CONNECT stage of the agent proxy. This is an organization
egress-policy denial, not a transient error; per `/root/.ccr/README.md` such denials must be reported,
not retried or routed around. Verified blocked hosts:

| Host | Purpose | Result |
|---|---|---|
| `www.sedarplus.ca`, `sedarplus.ca` | Authoritative Canadian filings archive (SEDAR+) | 403 CONNECT |
| `www.rockpointgs.com`, `rockpointgs.com` | Issuer IR site; hosts IPO Prospectus PDF directly | 403 CONNECT |
| `www.tsx.com` | Listing venue | 403 CONNECT |
| `www.sec.gov`, `data.sec.gov` | (checked; issuer is not an SEC registrant) | 403 CONNECT |
| `files.quartr.com` | Native PDF behind each Quartr record | 403 CONNECT |
| `annualreports.com`, `stockanalysis.com` | Secondary archives | 403 CONNECT |

The egress allowlist permits only GitHub and language package registries.

## Consequence for scope
- The **supplemented PREP Prospectus dated 2025-10-08** is the sole source of as-originally-reported
  **FY2023, FY2024 and FY2025** financial history. It is incorporated by reference into the FY2026 AIF
  but is not itself reproduced there. It could not be obtained.
- There is **no standalone FY2025 annual filing**: Rockpoint's IPO closed 2025-10-15, during FY2026, so
  FY2026 is its first annual reporting cycle as a public issuer. FY2025 therefore exists in reachable
  documents only as the **comparative column** of the FY2026 audited statements (flagged
  `is_comparative=1` throughout), never as an as-originally-reported primary column.

## What this leaves reachable
Full audited FY2026 + FY2025 comparative (Business 100% basis), Company-basis figures from 2025-10-15,
and four consecutive interim periods Q2 FY2026 -> Q1 FY2027. Sourced from the Quartr MCP connector,
which serves the filing text with per-page deep links.

## To lift this restriction
Add `sedarplus.ca`, `rockpointgs.com` and `files.quartr.com` to the environment's network egress
allowlist (Claude Code on the web -> environment settings), then re-run `scripts/fetch_primary.py`.
