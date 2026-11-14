"""
analyser_donnees_reelles.py
Analyse statistique des 2 500 donnes jouées dans les deux sens à cartes réelles.
Révèle la vraie valeur marginale : atouts preneur, soutien partenaire, chicanes, As.
"""
import json
from collections import defaultdict
import numpy as np

FICHIER = "donnees_croisees_reelles.jsonl"

with open(FICHIER, encoding="utf-8") as f:
    donnes = [json.loads(l) for l in f]

N = len(donnes)
print(f"=== ANALYSE DE {N:,} DONNES DISPUTÉES JOUÉES DANS LES DEUX SENS ===")
print("=" * 80)

# 1. LA LOI DES LEVÉES TOTALES À LA COINCHE
sommes_pts = [d["pts_reels_0"] + d["pts_reels_1"] for d in donnes]
diff_pts = [d["pts_reels_0"] - d["pts_reels_1"] for d in donnes]
print("1. LOI DES LEVÉES TOTALES :")
print(f"   • Moyenne P0 (Camp 0 dans son atout) : {np.mean([d['pts_reels_0'] for d in donnes]):5.1f} pts")
print(f"   • Moyenne P1 (Camp 1 dans son atout) : {np.mean([d['pts_reels_1'] for d in donnes]):5.1f} pts")
print(f"   • Somme P0 + P1 (Total deux camps)   : {np.mean(sommes_pts):5.1f} pts (sur 324 pts max)")
print(f"     -> À la coinche, les deux camps font en moyenne {np.mean(sommes_pts):.0f} pts combinés.")
print(f"     -> 162 - ({np.mean(sommes_pts):.0f} - 162) : l'attaque génère un surplus offensif de +{np.mean(sommes_pts)-162:.1f} pts !")

# 2. VALEUR RÉELLE SELON LE NOMBRE D'ATOUTS DU PRENEUR
print("\n" + "-" * 80)
print("2. POINTS RÉELS FAITS SELON LE NOMBRE D'ATOUTS DU PRENEUR (Camp 0) :")
for n_at in [3, 4, 5, 6]:
    sous = [d for d in donnes if d["atouts_preneur_0"] == n_at]
    if not sous: continue
    pts = [d["pts_reels_0"] for d in sous]
    # Taux d'atteinte de 80, 90, 100, 110
    t80 = 100 * sum(1 for p in pts if p >= 80) / len(pts)
    t90 = 100 * sum(1 for p in pts if p >= 90) / len(pts)
    t100 = 100 * sum(1 for p in pts if p >= 100) / len(pts)
    t110 = 100 * sum(1 for p in pts if p >= 110) / len(pts)
    print(f"   Preneur avec {n_at} atouts ({len(sous):4d} cas) : {np.mean(pts):5.1f} pts réels | >=80: {t80:4.1f}% | >=90: {t90:4.1f}% | >=100: {t100:4.1f}% | >=110: {t110:4.1f}%")

# 3. VALEUR RÉELLE DU SOUTIEN DU PARTENAIRE (atouts chez le partenaire)
print("\n" + "-" * 80)
print("3. APPORT RÉEL DES ATOUTS DU PARTENAIRE :")
for n_part in [0, 1, 2, 3]:
    sous = [d for d in donnes if d["atouts_part_0"] == n_part]
    if not sous: continue
    pts = [d["pts_reels_0"] for d in sous]
    print(f"   Partenaire a {n_part} atout(s) ({len(sous):4d} cas) : {np.mean(pts):5.1f} pts réels (écart vs 0 atout: {np.mean(pts) - np.mean([d['pts_reels_0'] for d in donnes if d['atouts_part_0']==0]):+5.1f} pts)")

# 4. LE CAS PRÉCIS : PRENEUR 3 ATOUTS (SUD) SELON LE SOUTIEN DU PARTENAIRE
print("\n" + "-" * 80)
print("4. FOCUS CRITIQUE : PRENEUR AVEC 3 ATOUTS (que fait-il selon le partenaire ?) :")
sous_p3 = [d for d in donnes if d["atouts_preneur_0"] == 3]
for n_part in [0, 1, 2]:
    s = [d for d in sous_p3 if d["atouts_part_0"] == n_part]
    if not s: continue
    pts = [d["pts_reels_0"] for d in s]
    t90 = 100 * sum(1 for p in pts if p >= 90) / len(s)
    t100 = 100 * sum(1 for p in pts if p >= 100) / len(s)
    t110 = 100 * sum(1 for p in pts if p >= 110) / len(s)
    print(f"   Preneur 3 atouts + Partenaire {n_part} atout(s) ({len(s):3d} cas) : {np.mean(pts):5.1f} pts | >=90: {t90:4.1f}% | >=100: {t100:4.1f}% | >=110: {t110:4.1f}%")

# 5. APPORT D'UNE CHICANE FRANCHE ET DES AS DU PRENEUR
print("\n" + "-" * 80)
print("5. APPORT MARGINAL DES AS EXTÉRIEURS ET DES CHICANES :")
for as_nb in [0, 1, 2, 3]:
    s = [d for d in donnes if d["as_ext_0"] == as_nb]
    if not s: continue
    pts = [d["pts_reels_0"] for d in s]
    print(f"   Preneur avec {as_nb} As extérieur(s) ({len(s):4d} cas) : {np.mean(pts):5.1f} pts réels")

print()
for chic in [0, 1, 2]:
    s = [d for d in donnes if d["chicanes_0"] == chic]
    if not s: continue
    pts = [d["pts_reels_0"] for d in s]
    print(f"   Preneur avec {chic} chicane(s) franche(s) ({len(s):4d} cas) : {np.mean(pts):5.1f} pts réels")

# 6. LA RÈGLE D'OR DE DÉFENSE : QUAND DOIT-ON SURENCHÉRIR ?
print("\n" + "=" * 80)
print("6. RÈGLE D'OR DU DUEL : QUAND LE CAMP 0 GAGNE-T-IL À MONTER PLUTÔT QU'À LAISSER JOUER ?")
print("On compare : la marque si on laisse l'adversaire jouer son contrat V1")
print("          vs la marque si on surenchère à V0 (notre palier suivant).")
print("-" * 80)

# Scénario type : Adversaire a un contrat V1 (ex: 90 ou 100)
# Camp 0 doit décider s'il monte à V0 = V1 + 10 (ex: 100 ou 110)
for val_adv in [80, 90, 100]:
    val_surenchere = val_adv + 10
    
    # Donnes où l'adversaire a un niveau d'annonce compatible avec val_adv
    donnes_conflit = [d for d in donnes if d["niv_1"] >= val_adv]
    if not donnes_conflit: continue
    
    gains_laisser = []
    gains_monter = []
    
    for d in donnes_conflit:
        # Si on laisse jouer :
        adv_reussit = (d["pts_reels_1"] >= val_adv)
        gain_laisser = -val_adv if adv_reussit else val_adv
        gains_laisser.append(gain_laisser)
        
        # Si on surenchère à val_surenchere :
        nous_reussissons = (d["pts_reels_0"] >= val_surenchere)
        gain_monter = val_surenchere if nous_reussissons else -val_surenchere
        gains_monter.append(gain_monter)
        
    diff = np.mean(gains_monter) - np.mean(gains_laisser)
    print(f"Adversaire est à {val_adv:3d} -> Doit-on surenchérir à {val_surenchere:3d} ?")
    print(f"   • Marque moyenne si on LAISSE JOUER : {np.mean(gains_laisser):+5.1f} pts")
    print(f"   • Marque moyenne si on SURENCHÈRE   : {np.mean(gains_monter):+5.1f} pts")
    verdict = "✅ OUI, MONTER EST RENTABLE !" if diff > 0 else "❌ NON, LAISSER JOUER EST MEILLEUR !"
    print(f"   👉 Différence nette : {diff:+5.1f} pts/donne  ==>  {verdict}\n")
