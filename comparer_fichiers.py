"""Gain apporté par les enchères, mesuré donne par donne."""
import json
import numpy as np

MOTEURS = ["oracle", "mcia", "mc_encheres", "coop", "ia", "regles"]

def lire(fichier):
    donnes = {}
    with open(fichier, encoding="utf-8") as f:
        for ligne in f:
            try:
                r = json.loads(ligne)
            except json.JSONDecodeError:
                continue
            if "role" in r:
                donnes[r["graine"]] = r
    return donnes

A = lire("resultats_benchmark.jsonl")            # sans enchères
B = lire("resultats_benchmark_encheres.jsonl")   # avec enchères
communes = [g for g in A if g in B and A[g]["role"] == B[g]["role"]]
print(f"{len(communes)} donnes communes\n")

for role in ["attaque", "defense", "tout"]:
    sel = [g for g in communes if role == "tout" or A[g]["role"] == role]
    print(f"--- {role.upper()} ({len(sel)} donnes) ---")
    for mot in MOTEURS:
        d = np.array([B[g][f"{mot}_pts"] - A[g][f"{mot}_pts"] for g in sel], dtype=float)
        marge = 1.96 * d.std(ddof=1) / np.sqrt(len(d))
        print(f"  {mot:12} gain avec enchères : {d.mean():+5.1f} ± {marge:4.1f}")
    print()
