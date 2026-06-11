#!/usr/bin/env python3
"""Verify all brand CUI-uri against ANAF Platitor TVA v9 API.
Usage: python3 scripts/verify_cuis.py
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.anaf_cui import check_cui
from services.brand_registry import BRAND_REGISTRY


async def verify():
    seen_cuis: dict[str, list[str]] = {}
    for brand_key, entry in BRAND_REGISTRY.items():
        for cui in entry.cuis:
            seen_cuis.setdefault(cui, []).append(brand_key)

    if not seen_cuis:
        print("No CUIs found in brand registry.")
        return

    print(f"Verifying {len(seen_cuis)} unique CUI(s) against ANAF API...\n")

    results = []
    for cui, brands in sorted(seen_cuis.items()):
        result = await check_cui(cui)
        ok = result.exists and result.activ
        results.append((cui, brands, result, ok))
        status = "OK" if ok else "ISSUE"
        if result.exists:
            print(f"  [{status}] CUI {cui} ({result.denumire}) - {'ACTIV' if result.activ else 'INACTIV'} - TVA: {result.platitor_tva}")
        else:
            print(f"  [{status}] CUI {cui} - NEGASIT in ANAF registry")
        print(f"         Brands: {', '.join(brands)}")

    ok_count = sum(1 for _, _, _, ok in results if ok)
    issue_count = len(results) - ok_count
    print(f"\n=== Rezumat: {ok_count} OK, {issue_count} probleme ===")

    if issue_count > 0:
        print("\nProbleme:")
        for cui, brands, result, ok in results:
            if not ok:
                print(f"  CUI {cui} ({', '.join(brands)}) - {'NEGASIT' if not result.exists else 'INACTIV'}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(verify())
