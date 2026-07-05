# ANAF CUI discrepancy triage — payment_destination_registry (2026-07-05)

Ran `verify_registry_cui_anaf.py` (with the batch-isolation fix, see below) against the
live ANAF v9 web service. **348 unique CUIs → 329 OK, 43 discrepancies.**

> Tool fix in this branch: `query_anaf` now sub-divides a failing batch recursively so
> one malformed CUI no longer marks a whole batch of good CUIs as "not found". Before the
> fix, batch 4 never ran and ~48 CUIs were false negatives (88 "discrepancies"); after,
> 43 real ones remain. The offending value was a corrupted 23-digit Aquatim CUI.

## ✅ Corrected in this branch
| brand | old CUI | new CUI | source of truth |
|---|---|---|---|
| altex_romania | `13831166` (not in ANAF) | **`2864518`** | photographed invoice + `brand_registry.py` + Codex live SAFE + ANAF confirms `2864518 → ALTEX ROMANIA SRL` |

This was the CUI behind the Altex/Media Galaxy false PERICULOS. **Not** flipped blindly — 4 independent confirmations.

## ⚠️ Real wrong CUI — CUI resolves to a *different* company (needs the correct CUI, do NOT guess)
| CUI | registry says | ANAF says | file |
|---|---|---|---|
| 29241635 | Bijuteria Briliant | ANCA SILVER GOLD SRL | agent_batch |
| 34738429 | SaniStore | BANYO DESIGN SHOP SRL | agent_batch |
| 34896844 | SellWeb | BARSIGALEX SRL | agent_batch |
| 29531752 | Mobigor | SORGOR ALEX SRL | wave4_research |
| 2167162 | Doctorul Animalelor | SELLA IMPEX COM SRL | wave6_verified |
| 11152462 | Euro Instal | POLTERGEIST SRL | wave6_verified |
| 26811251 | Dumitru Monden PFA | MOLDOVAN TEODOR-ALIN II | wave6_verified |
| 38742210 | RefillHouse | REFILL HOUSE COMPANY SRL | agent_batch (likely same, verify) |

These need an ANAF **name→CUI** lookup (the v9/tva endpoint is CUI→record only) to find the right CUI. Flagged, not auto-corrected.

## 🗑️ Corrupted CUI (garbage value)
| CUI | brand | file |
|---|---|---|
| `30414808989948389989483` (23 digits) | aquatim | supplemental_2026_06_15 |

Clearly corrupted seed data. Needs the real Aquatim SA CUI.

## 🕳️ Placeholder CUI `0` (gov entities without a CUI in the seed)
`anaf`, `politia_romana` (government_admin). Not "wrong" — missing. Fill with the real institution CUI or drop from the payment-destination match.

## 🟡 Likely FALSE POSITIVE — same entity, name spelling only (verify, probably OK)
Municipiul Constanța / Orașul Mizil / TopGarage / Mobistore17 / Voltatec / Mobilex Grup /
SophieVet / RSD Grup / SOFAMOB / CoraVet / Cu Sufletul Vet — ANAF name differs only by
spacing/legal-form. Rompetrol Downstream vs Rompetrol Rafinare and the Sector 5/6 tax
directorates are entity-relationship nuances, not necessarily wrong.

## ⚠️ ANAF endpoint caveat (NOT_FOUND ≠ wrong)
The `PlatitorTvaRest/v9/tva` endpoint is the **VAT-payer** registry. Non-VAT-paying public
bodies (Municipiul Timișoara/Iași, some regional water companies: Apa Someș/Arad/Brașov,
Apa Canal 2000, Distrigaz Vest, Hydrokov, Termoenergetica) can legitimately return
"not found" while their CUI is valid. Confirm these against ANAF's general registry
(`PlatitorTvaRest/v9/persoana` or the RECOM/OpenAPI company endpoint) before treating them
as wrong — the README's suggested crawler integration should use that endpoint, not tva.

## 🔴 Inactive / radiat (verify still-valid destination)
| CUI | registry | ANAF status |
|---|---|---|
| 35099609 | FluxIT Software & Consulting | inactive/radiat |
| 40050130 | Metaled Steel Materials | inactive/radiat |

Full machine-readable list: `anaf_cui_discrepancies_2026-07-05.csv` (this dir).
