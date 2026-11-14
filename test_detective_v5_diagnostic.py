"""
test_detective_v5_diagnostic.py
Banc d'essai comparatif direct : Détective v3 vs Détective v5
Sur 50 donnes réelles avec annonces fortes (>= 100).
"""
import time
import random
from regles import REGLES_STANDARD
from moteur import distribuer, COULEURS
from partie import phase_annonces
from ia_joueur import JoueurIA
from detective_v3 import imaginer_v3
from detective_v5 import imaginer_v5, STATS_V5

print("=== BANC D'ESSAI COMPARATIF : DÉTECTIVE v3 vs DÉTECTIVE v5 ===")
print("Objectif : vérifier la disparition des preneurs à 0 atout et la vitesse de convergence.")
print("-" * 75)

donnes_test = []
g = 50_000_000

while len(donnes_test) < 40:
    g += 1
    random.seed(g)
    m = distribuer()
    donn = g % 4
    bots_ench = [JoueurIA() for _ in range(4)]
    c = phase_annonces(m, donn, bots_ench, REGLES_STANDARD, afficher=False)
    if c is not None and c["valeur"] >= 100:
        ench = list(bots_ench[(donn + 1) % 4].encheres)
        donnes_test.append((g, m, c, ench, donn))

print(f"Jeu d'essai constitué : {len(donnes_test)} donnes avec contrats forts (>= 100).")
print("-" * 75)

for nom, fn_det in [("Détective v3 (Ancien)", imaginer_v3), ("Détective v5 (Guidé)", imaginer_v5)]:
    t0 = time.time()
    nb_atouts_preneur = []
    valet_present = 0
    zero_atout_count = 0
    total_tirages = 0

    for idx, (graine, mains, contrat, ench, donn) in enumerate(donnes_test):
        atout = contrat["atout"]
        preneur = contrat["joueur"]
        # On teste depuis la vue du joueur défenseur 0 (si preneur != 0)
        j_vue = 0 if preneur != 0 else 1

        for _ in range(10):  # 10 tirages par donne
            total_tirages += 1
            random.seed(graine * 100 + total_tirages)
            m_imag = fn_det(mains[j_vue], j_vue, [], ench, atout, REGLES_STANDARD)

            main_p = m_imag[preneur]
            atouts_p = [c for c in main_p if c[1] == atout]
            n_at = len(atouts_p)
            nb_atouts_preneur.append(n_at)

            if ('V', atout) in main_p:
                valet_present += 1
            if n_at == 0:
                zero_atout_count += 1

    dt = time.time() - t0
    m_atout = sum(nb_atouts_preneur) / total_tirages
    pct_valet = 100 * valet_present / total_tirages

    print(f"{nom:<25} :")
    print(f"  • Temps total ({total_tirages} tirages) : {dt:.2f} s ({1000*dt/total_tirages:.1f} ms/tirage)")
    print(f"  • Atouts moyens chez le preneur  : {m_atout:.2f} atouts")
    print(f"  • Preneur a le Valet d'atout     : {valet_present}/{total_tirages} ({pct_valet:.1f} %)")
    print(f"  • Mains aberrantes (0 atout)     : {zero_atout_count}/{total_tirages}")
    print()
