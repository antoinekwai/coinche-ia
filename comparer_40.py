"""Écart apparié : v3 à 40 simulations contre v3 à 20 simulations."""
import json
import numpy as np

donnes = []
with open("resultats_simulations_40.jsonl", encoding="utf-8") as f:
    for ligne in f:
        try:
            r = json.loads(ligne)
        except json.JSONDecodeError:
            continue
        if "role" in r:
            donnes.append(r)

for role in ["attaque", "defense", "tout"]:
    sel = [d for d in donnes if role == "tout" or d["role"] == role]
    e = np.array([d["mcia_v3_40_pts"] - d["mcia_v3_pts"] for d in sel], dtype=float)
    marge = 1.96 * e.std(ddof=1) / np.sqrt(len(e))
    print(f"{role:8} ({len(sel)} donnes) : 40 sim. - 20 sim. = {e.mean():+5.1f} ± {marge:4.1f}")
