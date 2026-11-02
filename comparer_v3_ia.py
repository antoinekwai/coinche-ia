"""Écart apparié Bot-MC-IA v3 contre IA pure, donne par donne."""
import json
import numpy as np

donnes = []
with open("resultats_confirmation_v3.jsonl", encoding="utf-8") as f:
    for ligne in f:
        try:
            r = json.loads(ligne)
        except json.JSONDecodeError:
            continue
        if "role" in r:
            donnes.append(r)

for role in ["attaque", "defense", "tout"]:
    sel = [d for d in donnes if role == "tout" or d["role"] == role]
    e = np.array([d["mcia_v3_pts"] - d["ia_pts"] for d in sel], dtype=float)
    marge = 1.96 * e.std(ddof=1) / np.sqrt(len(e))
    print(f"{role:8} ({len(sel)} donnes) : v3 - IA pure = {e.mean():+5.1f} ± {marge:4.1f}")
