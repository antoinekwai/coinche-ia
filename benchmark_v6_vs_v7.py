"""
benchmark_v6_vs_v7.py
Duel direct entre v6 (Détective v3) et v7 (Détective v5 guidé)
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
from bot_mc_ia_v6 import BotMCIAv6
from bot_mc_ia_v7 import BotMCIAv7

NB_DONNES = 300
PREMIERE_GRAINE = 80_000_000

MOTS = {
    "v6_actuel": BotMCIAv6,
    "v7_guide": BotMCIAv7,
}

print(f"=== DUEL DES DÉTECTIVES : v6 (Det v3) vs v7 (Det v5 Guidé) : {NB_DONNES} donnes ===")
print("-" * 75)

donnes_jouees = 0
res_pts = {m: [] for m in MOTS}
res_sec = {m: [] for m in MOTS}
res_ok = {m: [] for m in MOTS}
res_marque = {m: [] for m in MOTS}

t_debut = time.time()

for g in range(PREMIERE_GRAINE, PREMIERE_GRAINE + NB_DONNES * 2):
    if donnes_jouees >= NB_DONNES:
        break

    random.seed(g); np.random.seed(g % 2**32); torch.manual_seed(g)
    mains_init = distribuer()
    donneur = g % 4
    joueurs_ench = [JoueurIA() for _ in range(4)]
    contrat = phase_annonces(mains_init, donneur, joueurs_ench, REGLES_STANDARD, afficher=False)
    if contrat is None:
        continue

    donnes_jouees += 1
    premier_parle = (donneur + 1) % 4
    encheres = list(joueurs_ench[premier_parle].encheres)
    camp = 0
    role = "attaque" if contrat["joueur"] % 2 == camp else "defense"
    val = contrat["valeur"]
    mult = 2 if contrat.get("coinche", 0) > 0 else 1
    atout = contrat["atout"]

    for nom, cls_m in MOTS.items():
        random.seed(g * 10 + 7); np.random.seed((g * 10 + 7) % 2**32); torch.manual_seed(g * 10 + 7)
        mains_c = [list(m) for m in mains_init]
        bot = cls_m()
        adv = MCEncheres()
        hist, p_eq, pl_eq = [], [0, 0], [0, 0]
        prem = (donneur + 1) % 4

        t0 = time.time()
        while len(hist) < 32:
            pli = []
            for k in range(4):
                j = (prem + k) % 4
                jbs = cartes_jouables(mains_c[j], pli, atout, j, REGLES_STANDARD)
                if j % 2 == camp:
                    bot.historique = list(hist)
                    bot.encheres = list(encheres)
                    c = bot.jouer_carte(mains_c[j], jbs, pli, contrat, j, REGLES_STANDARD)
                else:
                    adv.historique = list(hist)
                    adv.encheres = list(encheres)
                    c = adv.jouer_carte(mains_c[j], jbs, pli, contrat, j, REGLES_STANDARD)
                mains_c[j].remove(c)
                pli.append((j, c))
                hist.append((j, c))
            g = gagnant_pli(pli, atout)[0]
            prem = g
            p = sum(points(c, atout) for _, c in pli)
            if len(hist) == 32: p += REGLES_STANDARD["dix_de_der"]
            p_eq[g % 2] += p
            pl_eq[g % 2] += 1

        dt = time.time() - t0
        bel = equipe_belote(mains_init, atout)
        _, reussi = decompte(contrat, p_eq, pl_eq, bel, REGLES_STANDARD)
        gagne = reussi if role == "attaque" else not reussi
        marque_camp = (val * mult) if gagne else (-val * mult)

        res_pts[nom].append(p_eq[camp])
        res_sec[nom].append(dt)
        res_ok[nom].append(gagne)
        res_marque[nom].append(marque_camp)

    if donnes_jouees % 50 == 0:
        ec = time.time() - t_debut
        m_v6 = np.mean(res_marque["v6_actuel"])
        m_v7 = np.mean(res_marque["v7_guide"])
        diff = m_v7 - m_v6
        print(f"  {donnes_jouees:4d}/{NB_DONNES} donnes | {ec/60:4.1f} min | Marque: v6={m_v6:+.1f} vs v7={m_v7:+.1f} (écart: {diff:+.1f})", flush=True)

print("\n" + "=" * 75)
print(f"RÉSULTATS SUR {donnes_jouees} DONNES APPARIÉES :")
print("=" * 75)
print(f"{'Moteur':<18} | {'Pts faits':>9} | {'Succès':>7} | {'Temps/partie':>12} | {'Marque moy.':>11} | {'Écart vs v6':>16}")
print("-" * 75)

ref = np.array(res_marque["v6_actuel"], dtype=float)
for nom in ["v6_actuel", "v7_guide"]:
    pts_m = np.mean(res_pts[nom])
    taux = 100 * np.mean(res_ok[nom])
    sec_m = np.mean(res_sec[nom])
    marq = np.array(res_marque[nom], dtype=float)
    marq_m = marq.mean()

    ecart = marq - ref
    marge = 1.96 * ecart.std(ddof=1) / np.sqrt(len(ecart)) if nom != "v6_actuel" else 0.0
    txt_ecart = f"{ecart.mean():+6.1f} ± {marge:4.1f}" if nom != "v6_actuel" else "référence"

    print(f"{nom:<18} | {pts_m:9.1f} | {taux:6.1f}% | {sec_m:10.2f}s | {marq_m:+11.1f} | {txt_ecart:>16}")
