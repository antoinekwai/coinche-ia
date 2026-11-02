"""Taux de chute des contrats coinchés, à partir des résultats déjà calculés."""
import json
from collections import defaultdict

FICHIER = "resultats_confirmation_v3.jsonl"

def chute(d, mot):
    ok = d[f"{mot}_ok"]                     # succès du point de vue de l'équipe 0
    return (not ok) if d["role"] == "attaque" else ok

stats = defaultdict(lambda: {"n": 0, "v3": 0, "ia": 0})
with open(FICHIER, encoding="utf-8") as f:
    for ligne in f:
        try:
            d = json.loads(ligne)
        except json.JSONDecodeError:
            continue
        if "role" not in d or "encheres" not in d:
            continue
        coinche = any(dec == "coinche" for _, dec in d["encheres"])
        cle = ("COINCHÉ" if coinche else "normal", d["valeur"])
        s = stats[cle]
        s["n"] += 1
        s["v3"] += chute(d, "mcia_v3")
        s["ia"] += chute(d, "ia")

print(f"{'Contrat':<16} | {'Nombre':>6} | {'Chute (v3)':>10} | {'Chute (IA)':>10}")
print("-" * 52)
for (type_c, val), s in sorted(stats.items(), key=lambda x: (x[0][0], x[0][1])):
    print(f"{type_c + ' ' + str(val):<16} | {s['n']:6d} | "
          f"{100 * s['v3'] / s['n']:9.0f}% | {100 * s['ia'] / s['n']:9.0f}%")
