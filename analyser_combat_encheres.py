"""
analyser_combat_encheres.py
Analyse statistique croisée des 500 décisions de combat d'enchères.
Extrait les règles objectives : quand monter à +20, +30, et quand coincher ?
"""
import json
from collections import defaultdict
import numpy as np

FICHIER = "donnees_combat_encheres.jsonl"

with open(FICHIER, encoding="utf-8") as f:
    donnes = [json.loads(l) for l in f]

print(f"=== ANALYSE STATISTIQUE DE {len(donnes)} DÉCISIONS DE COMBAT D'ENCHÈRES ===")
print("=" * 80)

# 1. RÉPARTITION GLOBALE DU CHOIX OPTIMAL
actions = defaultdict(int)
for d in donnes:
    actions[d["meilleure_action"]] += 1

print("1. CHOIX OPTIMAL GLOBAL (selon l'espérance simulée) :")
for act in ["passe", "surenchere", "coinche"]:
    n = actions[act]
    print(f"   • {act.upper():<12} : {n:3d} cas ({100*n/len(donnes):5.1f} %)")

# 2. SELON LE DÉPASSEMENT EXIGÉ (+20 vs +30 vs +40)
print("\n" + "-" * 80)
print("2. CHOIX SELON LE DÉPASSEMENT EXIGÉ AU-DELÀ DE L'OUVERTURE :")
for dep in [20, 30, 40]:
    sous = [d for d in donnes if d["depassement"] == dep]
    if not sous: continue
    p = sum(1 for d in sous if d["meilleure_action"] == "passe")
    s = sum(1 for d in sous if d["meilleure_action"] == "surenchere")
    c = sum(1 for d in sous if d["meilleure_action"] == "coinche")
    tot = len(sous)
    print(f"   Dépassement +{dep} ({tot:3d} cas) -> Surenchère: {s:3d} ({100*s/tot:4.1f}%) | Passe: {p:3d} ({100*p/tot:4.1f}%) | Coinche: {c:3d} ({100*c/tot:4.1f}%)")

# 3. SELON LE NOMBRE D'ATOUTS EN MAIN PROPRE
print("\n" + "-" * 80)
print("3. TAUX DE SURENCHÈRE SELON LE NOMBRE D'ATOUTS PROPRES :")
for n_at in [2, 3, 4, 5, 6]:
    sous = [d for d in donnes if d["morphologie"]["atouts_nb"] == n_at]
    if not sous: continue
    s = sum(1 for d in sous if d["meilleure_action"] == "surenchere")
    p = sum(1 for d in sous if d["meilleure_action"] == "passe")
    c = sum(1 for d in sous if d["meilleure_action"] == "coinche")
    tot = len(sous)
    print(f"   {n_at} atouts ({tot:3d} cas) -> Surenchère: {s:3d} ({100*s/tot:4.1f}%) | Passe: {p:3d} ({100*p/tot:4.1f}%) | Coinche: {c:3d} ({100*c/tot:4.1f}%)")

# 4. LE CAS CRITIQUE : 3 ATOUTS PROPRES (quand peut-on monter ?)
print("\n" + "-" * 80)
print("4. FOCUS : PRENEUR AVEC 3 ATOUTS SEULEMENT (quand peut-il monter ?) :")
sous_3at = [d for d in donnes if d["morphologie"]["atouts_nb"] == 3]
for label, cond in [
    ("Avec V ou 9 d'atout", lambda d: d["morphologie"]["atout_valet"] or d["morphologie"]["atout_neuf"]),
    ("Sans V ni 9 d'atout", lambda d: not (d["morphologie"]["atout_valet"] or d["morphologie"]["atout_neuf"])),
    ("Partenaire a PARLÉ", lambda d: d["partenaire_a_parle"]),
    ("Partenaire a PASSÉ", lambda d: d["partenaire_a_passe"]),
    ("Partenaire a PASSÉ ET Sans V/9", lambda d: d["partenaire_a_passe"] and not (d["morphologie"]["atout_valet"] or d["morphologie"]["atout_neuf"])),
    ("Partenaire a PASSÉ MAIS avec 2 As ext.", lambda d: d["partenaire_a_passe"] and d["morphologie"]["as_ext"] >= 2),
]:
    cas = [d for d in sous_3at if cond(d)]
    if not cas: continue
    s = sum(1 for d in cas if d["meilleure_action"] == "surenchere")
    tot = len(cas)
    print(f"   • {label:<35} ({tot:3d} cas) -> Surenchère rentable : {s:2d}/{tot:2d} ({100*s/tot:4.1f} %)")

# 5. L'IMPACT DE LA FORME (CHICANES & BICOLORES)
print("\n" + "-" * 80)
print("5. IMPACT DE LA DISTRIBUTION (Chicanes et Longues annexes) :")
for label, cond in [
    ("Sans chicane ni singleton", lambda d: d["morphologie"]["chicanes"] == 0 and d["morphologie"]["singletons"] == 0),
    ("Au moins 1 singleton", lambda d: d["morphologie"]["singletons"] >= 1),
    ("Au moins 1 chicane franche", lambda d: d["morphologie"]["chicanes"] >= 1),
    ("Bicolore (longue 4e annexe)", lambda d: d["morphologie"]["a_longue_4"]),
]:
    cas = [d for d in donnes if cond(d)]
    if not cas: continue
    s = sum(1 for d in cas if d["meilleure_action"] == "surenchere")
    tot = len(cas)
    print(f"   • {label:<32} ({tot:3d} cas) -> Taux de surenchère : {s:2d}/{tot:2d} ({100*s/tot:4.1f} %)")

# 6. CONDITIONS DE LA COINCHE RENTABLE
print("\n" + "-" * 80)
print("6. PROFIL DES DONNES OÙ LA COINCHE EST OPTIMALE :")
coinches = [d for d in donnes if d["meilleure_action"] == "coinche"]
print(f"Total cas de coinche optimale : {len(coinches)}")
if coinches:
    at_moy = np.mean([d["morphologie"]["atouts_nb"] for d in coinches])
    hon_adv = np.mean([d["morphologie"]["honneurs_couleur_adverse"] for d in coinches])
    cart_adv = np.mean([d["morphologie"]["cartes_couleur_adverse"] for d in coinches])
    c_val_moy = np.mean([d["valeur_adverse"] for d in coinches])
    print(f"   • Niveau moyen du contrat adverse coinché : {c_val_moy:.1f}")
    print(f"   • Nombre moyen de cartes dans la couleur adverse : {cart_adv:.1f} cartes (dont {hon_adv:.1f} honneurs)")
    print(f"   • Atouts propres moyens dans notre couleur        : {at_moy:.1f} atouts")
print("=" * 80)
