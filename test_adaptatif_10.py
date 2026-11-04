"""
test_adaptatif_10.py
Essai rapide sur 10 donnes neuves appariées :
v3 (20 sim.) vs v3x40 (40 sim.) vs v3 Adaptatif (15/50 sim.)
Mesure le temps, les points, et le ratio de décisions approfondies.
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
from bot_mc_ia_v3 import BotMCIAv3, BotMCIAv3x40
from bot_mc_ia_adaptatif import BotMCIAv3Adaptatif

NB_DONNES = 10
GRAINE_DEPART = 8_000_000

MOTS = {
    "v3": BotMCIAv3,
    "v3_40": BotMCIAv3x40,
    "v3_adapt": BotMCIAv3Adaptatif
}

print(f"=== TEST ADAPTATIF : {NB_DONNES} donnes appariées ===")
resultats = {m: {"pts": [], "sec": [], "ok": []} for m in MOTS}
stats_globales_adapt = {"rapides": 0, "approfondies": 0}

for g in range(GRAINE_DEPART, GRAINE_DEPART + NB_DONNES):
    random.seed(g)
    np.random.seed(g % (2**32))
    torch.manual_seed(g)

    mains_init = distribuer()
    donneur = g % 4
    joueurs_ench = [JoueurIA() for _ in range(4)]
    contrat = phase_annonces(mains_init, donneur, joueurs_ench, REGLES_STANDARD, afficher=False)

    if contrat is None:
        continue

    premier_parle = (donneur + 1) % 4
    encheres = list(joueurs_ench[premier_parle].encheres)

    camp_teste = 0
    role = "attaque" if contrat["joueur"] % 2 == camp_teste else "defense"

    for nom, cls_bot in MOTS.items():
        # Hasard déterministe par moteur pour comparaison appariée
        random.seed(g * 10 + 7)
        np.random.seed((g * 10 + 7) % (2**32))
        torch.manual_seed(g * 10 + 7)

        mains = [list(m) for m in mains_init]
        bot = cls_bot()
        adversaire = MCEncheres()

        historique, pts_eq, plis_eq = [], [0, 0], [0, 0]
        premier = (donneur + 1) % 4
        atout = contrat["atout"]

        t0 = time.time()
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

        dt = time.time() - t0
        bel = equipe_belote(mains_init, atout)
        marque, reussi = decompte(contrat, pts_eq, plis_eq, bel, REGLES_STANDARD)

        resultats[nom]["pts"].append(pts_eq[camp_teste])
        resultats[nom]["sec"].append(dt)
        resultats[nom]["ok"].append(reussi if role == "attaque" else not reussi)

        if nom == "v3_adapt":
            stats_globales_adapt["rapides"] += bot.stats_adaptatif["rapides"]
            stats_globales_adapt["approfondies"] += bot.stats_adaptatif["approfondies"]

    print(f"Donne {g} ({role:7s} {contrat['valeur']:3d} {contrat['atout']}) : "
          f"v3={resultats['v3']['pts'][-1]:3d} ({resultats['v3']['sec'][-1]:.1f}s) | "
          f"v3_40={resultats['v3_40']['pts'][-1]:3d} ({resultats['v3_40']['sec'][-1]:.1f}s) | "
          f"adapt={resultats['v3_adapt']['pts'][-1]:3d} ({resultats['v3_adapt']['sec'][-1]:.1f}s)")

print("\n" + "=" * 60)
print("BILAN SUR LES DONNES JOUÉES :")
print("=" * 60)
for nom in MOTS:
    pts_m = np.mean(resultats[nom]["pts"])
    sec_m = np.mean(resultats[nom]["sec"])
    taux_succes = 100 * np.mean(resultats[nom]["ok"])
    print(f"{nom:<10} | Pts moy: {pts_m:5.1f} | Succès: {taux_succes:5.1f}% | Temps moy: {sec_m:4.2f}s/partie")

tot_dec = stats_globales_adapt["rapides"] + stats_globales_adapt["approfondies"]
if tot_dec > 0:
    pct_rap = 100 * stats_globales_adapt["rapides"] / tot_dec
    pct_app = 100 * stats_globales_adapt["approfondies"] / tot_dec
    print("-" * 60)
    print(f"Décisions adaptatif : {tot_dec} au total")
    print(f"  • Décisions rapides (15 sim.)      : {stats_globales_adapt['rapides']:3d} ({pct_rap:.1f}%)")
    print(f"  • Décisions approfondies (50 sim.) : {stats_globales_adapt['approfondies']:3d} ({pct_app:.1f}%)")
