"""
benchmark_duel_pli1.py
Duel direct dès le Pli 1 :
Monte-Carlo 20 simulations dès la première carte :
- v3_pli1 : Détective v3 classique (tirage naïf)
- v5_pli1 : Détective v5 (tirage guidé atouts + As pondérés)
Sur 200 donnes neuves appariées face à MC-Enchères.
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
from bot_mc_ia import BotMCIA
from detective_v3 import imaginer_v3
from detective_v5 import imaginer_v5
import bot_mc_ia

NB_DONNES = 200
PREMIERE_GRAINE = 96_000_000


class BotMC_V3(BotMCIA):
    nom = "BotMC (Det v3)"
    def __init__(self):
        super().__init__()
        self.nb_simulations = 20

    def jouer_carte(self, main, jouables, pli, contrat, joueur, regles):
        ancien = bot_mc_ia.imaginer_donnes_contraintes
        bot_mc_ia.imaginer_donnes_contraintes = imaginer_v3
        try:
            return super().jouer_carte(main, jouables, pli, contrat, joueur, regles)
        finally:
            bot_mc_ia.imaginer_donnes_contraintes = ancien


class BotMC_V5(BotMCIA):
    nom = "BotMC (Det v5)"
    def __init__(self):
        super().__init__()
        self.nb_simulations = 20

    def jouer_carte(self, main, jouables, pli, contrat, joueur, regles):
        ancien = bot_mc_ia.imaginer_donnes_contraintes
        bot_mc_ia.imaginer_donnes_contraintes = imaginer_v5
        try:
            return super().jouer_carte(main, jouables, pli, contrat, joueur, regles)
        finally:
            bot_mc_ia.imaginer_donnes_contraintes = ancien


MOTS = {
    "v3_pli1": BotMC_V3,
    "v5_pli1": BotMC_V5,
}

print(f"=== DUEL AU PLI 1 : DÉTECTIVE V3 vs V5 ({NB_DONNES} donnes) ===")
print("Monte-Carlo dès la première carte : v3 vs v5")
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
        m_v3 = np.mean(res_marque["v3_pli1"])
        m_v5 = np.mean(res_marque["v5_pli1"])
        diff = m_v5 - m_v3
        print(f"  {donnes_jouees:4d}/{NB_DONNES} donnes | {ec/60:4.1f} min | Marque: v3={m_v3:+.1f} vs v5={m_v5:+.1f} (écart: {diff:+.1f})", flush=True)

print("\n" + "=" * 75)
print(f"RÉSULTATS SUR {donnes_jouees} DONNES APPARIÉES :")
print("=" * 75)
print(f"{'Moteur':<18} | {'Pts faits':>9} | {'Succès':>7} | {'Temps/partie':>12} | {'Marque moy.':>11} | {'Écart vs v3':>16}")
print("-" * 75)

ref = np.array(res_marque["v3_pli1"], dtype=float)
for nom in ["v3_pli1", "v5_pli1"]:
    pts_m = np.mean(res_pts[nom])
    taux = 100 * np.mean(res_ok[nom])
    sec_m = np.mean(res_sec[nom])
    marq = np.array(res_marque[nom], dtype=float)
    marq_m = marq.mean()

    ecart = marq - ref
    marge = 1.96 * ecart.std(ddof=1) / np.sqrt(len(ecart)) if nom != "v3_pli1" else 0.0
    txt_ecart = f"{ecart.mean():+6.1f} ± {marge:4.1f}" if nom != "v3_pli1" else "référence"

    print(f"{nom:<18} | {pts_m:9.1f} | {taux:6.1f}% | {sec_m:10.2f}s | {marq_m:+11.1f} | {txt_ecart:>16}")
