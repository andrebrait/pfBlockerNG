# Phase 2 Results — Split decision from side-effects

## DnsblDecision shape

```python
@dataclass
class DnsblDecision:
    is_found: bool
    in_whitelist: bool
    in_hsts: bool
    null_blocking: bool
    log_type: Any        # False | "1" | log value from data/zone entry
    b_type: str          # "Python" | "DNSBL" | "TLD" | any of the above + "_CNAME"
    p_type: str          # "Python" | "HSTS" | "HSTS_TLD"
    feed: Any            # "Unknown" | feed name string
    group: Any           # "Unknown" | group name string
    b_eval: str          # "" | q_name | matched zone parent
```

## evaluate_domain signature

```python
def evaluate_domain(
    q_name: str,
    q_name_original: str,
    tld: str,
    is_cname: bool,
    cfg: dict[str, Any],
    containers: dict[str, Any],
) -> DnsblDecision
```

### cfg keys threaded from pfb

| key | source |
|-----|--------|
| `python_blocking` | `pfb["python_blocking"]` |
| `dataDB` | `pfb["dataDB"]` (enable bit) |
| `zoneDB` | `pfb["zoneDB"]` (enable bit) |
| `python_tld` | `pfb["python_tld"]` |
| `python_tlds` | `pfb["python_tlds"]` |
| `dnsbl_ipv4` | `pfb["dnsbl_ipv4"]` |
| `dnsbl_ipv6` | `pfb["dnsbl_ipv6"]` |
| `python_idn` | `pfb["python_idn"]` |
| `regexDB` | `pfb["regexDB"]` (enable bit) |
| `whiteDB` | `pfb["whiteDB"]` (enable bit) |
| `python_tld_seg` | `pfb["python_tld_seg"]` |
| `hstsDB` | `pfb["hstsDB"]` (enable bit) |
| `hsts_tlds` | `pfb["hsts_tlds"]` |

### containers keys threaded as module globals

| key | module global |
|-----|---------------|
| `dataDB` | `dataDB` |
| `zoneDB` | `zoneDB` |
| `whiteDB` | `whiteDB` |
| `regexDB` | `regexDB` |
| `feedGroupIndexDB` | `feedGroupIndexDB` |
| `hstsDB` | `hstsDB` |

Note: `regexDB` matching is performed inline in `evaluate_domain` (iterating over
`regex_db.items()`) rather than calling `pfb_regex_match()` which reads the global.

`resolve_feed_group` was updated to accept `feed_group_index_db` as a second
parameter (instead of reading the module global), making it pure and callable from
`evaluate_domain`. Signature is now `resolve_feed_group(index, feed_group_index_db)`
and it is called for both the data and zone hit branches inside `evaluate_domain`.

## evaluate_noaaaa signature

```python
def evaluate_noaaaa(q_name: str, noaaaa_db: dict[str, Any]) -> bool
```

Returns `True` on exact hit OR wildcard-parent hit; `False` otherwise.

## noAAAA memo write location

Memo write (`noAAAADB[q_name] = True`) stays in `operate()`. After
`evaluate_noaaaa` returns `True`, operate() checks whether an exact entry already
exists (`noAAAADB.get(q_name_original) is None`). If no exact entry exists, the
hit was a wildcard-parent hit and the memo is written — preserving the original
behaviour exactly.

## Verification

- `python -m pytest`: 97/97 passed
- `ruff check .`: clean
- `ruff format . --check`: clean
- operate() side-effect order unchanged; decision now sourced from evaluate_domain /
  evaluate_noaaaa
