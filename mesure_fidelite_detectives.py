"""
mesure_fidelite_detectives.py
Mesure objective de fidélité aux enchères : Détective v3 vs v5
Sur 60 donnes réelles avec contrats >= 90 :
Teste aux Plis 2, 3 et 4 :
- Taux de d=0 (accord parfait avec les vraies enchères)
- d moyen final de la main renvoyée
- Nombre moyen d'essais avant acceptation
"""
import random
import numpy as np
from regles import REGLES_STANDARD
from moteur import distribuer, cartes_jouables, gagnant_pli
from partie import phase_annonces
from ia_joueur import JoueurIA
from detective_v3 import rejouer_encheres, nb_differences, coherente, tirage_naif
from detective_v5 import tirage_guide_v5

NB_DONNES = 60
GRAINE_BASE = 95_000_000

# Générer les donnes de test
donnes_test = []
g = GRAINE_BASE
while len(donnes_test) < NB_DONNES:
    g += 1
    random.seed(g)
    m = distribuer()
    donn = g % 4
    bots_ench = [JoueurIA() for _ in range(4)]
    c = phase_annonces(m, donn, bots_ench, REGLES_STANDARD, afficher=False)
    if c is not None and c["valeur"] >= 90:
        ench = list(bots_ench[(donn + 1) % 4].encheres)
        donnes_test.append((g, m, c, ench, donn))

print(f"=== MESURE DE FIDÉLITÉ DÉTECTIVE V3 vs V5 ({NB_DONNES} donnes, contrats >= 90) ===")
print("-" * 75)


def tester_detective(mode_tirage, main_j, j, hist, ench, atout, donneur, regles, max_essais=150, tol=0.1):
    """Fait un appel complet et renvoie (d_trouve, nb_essais_faits, est_parfait)."""
    meilleur_d = 999
    meilleure_imag = None

    for essai in range(1, max_essais + 1):
        if mode_tirage == "v3":
            imag = tirage_naif(main_j, j, hist)
        else:
            imag = tirage_guide_v5(main_j, j, hist, ench, atout, regles)

        if not coherente(imag, hist, atout, regles):
            continue

        depart = [list(mm) for mm in imag]
        for jj, cc in hist:
            depart[jj].append(cc)

        d = nb_differences(ench, rejouer_encheres(depart, donneur, regles))
        if d < meilleur_d:
            meilleur_d = d
            meilleure_imag = imag

        if d == 0:
            return 0, essai, True
        if random.random() < (tol ** d):
            return d, essai, False

    return meilleur_d, max_essais, (meilleur_d == 0)


stats = {
    pli: {
        "v3": {"d_list": [], "essais": [], "parfaits": 0, "total": 0},
        "v5": {"d_list": [], "essais": [], "parfaits": 0, "total": 0}
    }
    for pli in [2, 3, 4]
}

ia = JoueurIA()

for idx, (graine, mains, contrat, ench, donn) in enumerate(donnes_test, 1):
    atout = contrat["atout"]
    mains_c = [list(mm) for mm in mains]
    hist = []
    prem = (donn + 1) % 4

    # Dérouler les 3 premiers plis
    for p_num in range(1, 4):
        pli = []
        for step in range(4):
            j = (prem + step) % 4
            jbs = cartes_jouables(mains_c[j], pli, atout, j, REGLES_STANDARD)
            ia.historique = list(hist)
            ia.encheres = list(ench)
            c = ia.jouer_carte(mains_c[j], jbs, pli, contrat, j, REGLES_STANDARD)
            mains_c[j].remove(c)
            pli.append((j, c))
            hist.append((j, c))
        prem = gagnant_pli(pli, atout)[0]

        # Tester les détectives au début du pli suivant (pli p_num + 1)
        pli_cible = p_num + 1  # 2, 3, ou 4
        j_qui_teste = prem

        for mode in ["v3", "v5"]:
            random.seed(graine * 1000 + pli_cible * 10 + (0 if mode == "v3" else 1))
            d_final, n_essais, est_parfait = tester_detective(
                mode, mains_c[j_qui_teste], j_qui_teste, hist, ench, atout, donn, REGLES_STANDARD
            )
            s = stats[pli_cible][mode]
            s["d_list"].append(d_final)
            s["essais"].append(n_essais)
            s["parfaits"] += int(est_parfait)
            s["total"] += 1

print(f"{'Pli testé':<10} | {'Moteur':<8} | {'Taux d=0 (parfait)':>20} | {'d moyen final':>14} | {'Essais moyens':>14}")
print("-" * 75)

for p in [2, 3, 4]:
    for mode in ["v3", "v5"]:
        s = stats[p][mode]
        pct_p = 100 * s["parfaits"] / s["total"]
        d_moy = np.mean(s["d_list"])
        ess_moy = np.mean(s["essais"])
        print(f"Pli {p:<6} | {mode:<8} | {s['parfaits']:2d}/{s['total']:2d} ({pct_p:5.1f} %) | {d_moy:14.2f} | {ess_moy:14.1f}")
    if p < 4:
        print("-" * 75)
