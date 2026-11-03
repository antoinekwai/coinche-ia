"""Écarts en POINTS DE MARQUE (contrat sec) : +valeur si le camp testé gagne, -valeur sinon, x2 si coinché.
Limite : la surcoinche n'est pas enregistrée dans les enchères."""
import json
import sys
import numpy as np

FICHIER = sys.argv[1] if len(sys.argv) > 1 else "resultats_simulations_40.jsonl"
REFERENCE = "mcia_v3"

donnes = []
with open(FICHIER, encoding="utf-8") as f:
    for ligne in f:
        try:
            r = json.loads(ligne)
        except json.JSONDecodeError:
            continue
        if "role" in r:
            donnes.append(r)

moteurs = [k[:-3] for k in donnes[0] if k.endswith("_ok")]

def marque(d, mot):
    mult = 2 if any(dec == "coinche" for _, dec in d.get("encheres", [])) else 1
    return (1 if d[f"{mot}_ok"] else -1) * d["valeur"] * mult

print(f"Fichier : {FICHIER}   ({len(donnes)} donnes)\n")
for role in ["attaque", "defense", "tout"]:
    sel = [d for d in donnes if role == "tout" or d["role"] == role]
    print(f"--- {role.upper()} ({len(sel)} donnes) ---")
    print(f"{'Moteur':<14} | {'Marque moy.':>11} | {'Écart vs ' + REFERENCE:>18}")
    for mot in moteurs:
        m = np.array([marque(d, mot) for d in sel], dtype=float)
        e = np.array([marque(d, mot) - marque(d, REFERENCE) for d in sel], dtype=float)
        marge = 1.96 * e.std(ddof=1) / np.sqrt(len(e))
        print(f"{mot:<14} | {m.mean():11.1f} | {e.mean():+8.1f} ± {marge:5.1f}")
    print()
