"""
benchmark_ia_v1_vs_v2.py
Duel direct entre les deux réseaux de neurones purs (sans Monte-Carlo) :
- IA_V1 : Ancien réseau ia_carte.pt (313 entrées)
- IA_V2 : Nouveau réseau ia_carte_v2_amorce.pt (324 entrées avec descripteurs experts)
Sur 300 donnes neuves appariées face à MC-Enchères.
"""
import time
import random
import numpy as np
import torch
from regles import REGLES_STANDARD
from moteur import distribuer, cartes_jouables, gagnant_pli, points, equipe_belote, decompte
from partie import phase_annonces
from test_mc_encheres import MCEncheres
from ia_joueur import JoueurIA
from ia_modele_v2 import JoueurIA_V2

NB_DONNES = 300
PREMIERE_GRAINE = 25_000_000

MOTS = {
    "IA_V1": lambda: JoueurIA(),
    "IA_V2": lambda: JoueurIA_V2(fichier="ia_carte_v2_amorce.pt")
}

print(f"=== DUEL RÉSEAU PUR : V1 vs V2 ({NB_DONNES} donnes appariées) ===")
print("IA_V1 (313 entrées) vs IA_V2 (324 entrées avec descripteurs experts)")
print("-" * 75)

donnes_jouees = 0
res_pts = {m: [] for m in MOTS}
res_ok = {m: [] for m in MOTS}
res_marque = {m: [] for m in MOTS}

t_debut = time.time()

for g in range(PREMIERE_GRAINE, PREMIERE_GRAINE + NB_DONNES * 2):
    if donnes_jouees >= NB_DONNES:
        break

    random.seed(g); np.random.seed(g % (2**32)); torch.manual_seed(g)
    mains_init = distribuer()
    donneur = g % 4
    joueurs_ench = [JoueurIA() for _ in range(4)]
    contrat = phase_annonces(mains_init, donneur, joueurs_ench, REGLES_STANDARD, afficher=False)

    if contrat is None:
        continue

    donnes_jouees += 1
    premier_parle = (donneur + 1) % 4
    encheres = list(joueurs_ench[premier_parle].encheres)

    camp_teste = 0
    role = "attaque" if contrat["joueur"] % 2 == camp_teste else "defense"
    valeur_contrat = contrat["valeur"]
    mult_coinche = 2 if contrat.get("coinche", 0) > 0 else 1

    for nom, fabrique in MOTS.items():
        random.seed(g * 10 + 7)
        np.random.seed((g * 10 + 7) % (2**32))
        torch.manual_seed(g * 10 + 7)

        mains = [list(m) for m in mains_init]
        bot = fabrique()
        adversaire = MCEncheres()

        historique, pts_eq, plis_eq = [], [0, 0], [0, 0]
        premier = (donneur + 1) % 4
        atout = contrat["atout"]

        while len(historique) < 32:
            pli = []
            for k in range(4):
                j = (premier + k) % 4
                jouables = cartes_jouables(mains[j], pli, atout, j, REGLES_STANDARD)
                if j % 2 == camp_teste:
                    bot.historique = list(historique)
                    bot.encheres = list(encheres)
                    c = bot.jouer_carte(mains[j], jouables, pli, contrat, j, REGLES_STANDARD)
                else:
                    adversaire.historique = list(historique)
                    adversaire.encheres = list(encheres)
                    c = adversaire.jouer_carte(mains[j], jouables, pli, contrat, j, REGLES_STANDARD)
                mains[j].remove(c)
                pli.append((j, c))
                historique.append((j, c))

            gagnant = gagnant_pli(pli, atout)[0]
            premier = gagnant
            p = sum(points(c, atout) for _, c in pli)
            if len(historique) == 32:
                p += REGLES_STANDARD["dix_de_der"]
            pts_eq[gagnant % 2] += p
            plis_eq[gagnant % 2] += 1

        bel = equipe_belote(mains_init, atout)
        marque_table, reussi = decompte(contrat, pts_eq, plis_eq, bel, REGLES_STANDARD)

        gagne = reussi if role == "attaque" else not reussi
        pts_faits = pts_eq[camp_teste]
        marque_camp = (valeur_contrat * mult_coinche) if gagne else (-valeur_contrat * mult_coinche)

        res_pts[nom].append(pts_faits)
        res_ok[nom].append(gagne)
        res_marque[nom].append(marque_camp)

print("\n" + "=" * 75)
print(f"RÉSULTATS SUR {donnes_jouees} DONNES APPARIÉES (en {time.time()-t_debut:.1f}s) :")
print("=" * 75)
print(f"{'Moteur':<12} | {'Pts faits':>9} | {'Succès':>7} | {'Marque moy.':>11} | {'Écart vs V1':>16}")
print("-" * 75)

ref = np.array(res_marque["IA_V1"], dtype=float)
for nom in ["IA_V1", "IA_V2"]:
    pts_m = np.mean(res_pts[nom])
    taux = 100 * np.mean(res_ok[nom])
    marq = np.array(res_marque[nom], dtype=float)
    marq_m = marq.mean()

    ecart = marq - ref
    marge = 1.96 * ecart.std(ddof=1) / np.sqrt(len(ecart)) if nom != "IA_V1" else 0.0
    txt_ecart = f"{ecart.mean():+6.1f} ± {marge:4.1f}" if nom != "IA_V1" else "référence"

    print(f"{nom:<12} | {pts_m:9.1f} | {taux:6.1f}% | {marq_m:+11.1f} | {txt_ecart:>16}")
