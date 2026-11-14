"""
benchmark_hybride_pli2.py
Compare les hybridations IA / Monte-Carlo (MC toujours à 20 simulations) :
- v3_std     : 100% MC (20 sim.) dès le Pli 1
- hyb_p1     : Pli 1 IA, Plis 2-8 MC (20 sim.) -> référence
- hyb_p1_p2  : Plis 1 et 2 IA, Plis 3-8 MC (20 sim.)
- hyb_mix_p2 : Pli 1 IA, Pli 2 Mix (MC 20 sim. + arbitrage IA si serré), Plis 3-8 MC
Mesure appariée sur 300 donnes neuves.
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
from bot_mc_ia_v3 import BotMCIAv3
from detective_v3 import imaginer_v3
from montecarlo import belote_imaginee, contrat_reussi
import bot_mc_ia

NB_DONNES = 300
PREMIERE_GRAINE = 9_500_000


class BotHybridePli1(BotMCIAv3):
    nom = "Hybride Pli 1"
    def __init__(self):
        super().__init__()
        self.ia = JoueurIA()

    def jouer_carte(self, main, jouables, pli, contrat, joueur, regles):
        if len(jouables) == 1:
            return jouables[0]
        if len(self.historique) < 4:
            self.ia.historique = list(self.historique)
            self.ia.encheres = list(self.encheres)
            return self.ia.jouer_carte(main, jouables, pli, contrat, joueur, regles)
        return super().jouer_carte(main, jouables, pli, contrat, joueur, regles)


class BotHybridePlis1et2(BotMCIAv3):
    nom = "Hybride Plis 1-2"
    def __init__(self):
        super().__init__()
        self.ia = JoueurIA()

    def jouer_carte(self, main, jouables, pli, contrat, joueur, regles):
        if len(jouables) == 1:
            return jouables[0]
        if len(self.historique) < 8:
            self.ia.historique = list(self.historique)
            self.ia.encheres = list(self.encheres)
            return self.ia.jouer_carte(main, jouables, pli, contrat, joueur, regles)
        return super().jouer_carte(main, jouables, pli, contrat, joueur, regles)


class BotHybrideMixPli2(BotMCIAv3):
    nom = "Hybride Mix Pli 2"
    def __init__(self):
        super().__init__()
        self.ia = JoueurIA()

    def jouer_carte(self, main, jouables, pli, contrat, joueur, regles):
        if len(jouables) == 1:
            return jouables[0]

        # Pli 1 : 100% IA
        if len(self.historique) < 4:
            self.ia.historique = list(self.historique)
            self.ia.encheres = list(self.encheres)
            return self.ia.jouer_carte(main, jouables, pli, contrat, joueur, regles)

        # Pli 2 : Mix 50/50 (MC 20 simulations + arbitrage IA si serré)
        if len(self.historique) < 8:
            ancien = bot_mc_ia.imaginer_donnes_contraintes
            bot_mc_ia.imaginer_donnes_contraintes = imaginer_v3
            try:
                atout = contrat["atout"]
                eq, attaque = joueur % 2, contrat["joueur"] % 2
                
                # 20 simulations complètes
                mains_ech = [imaginer_v3(main, joueur, self.historique, self.encheres, atout, regles)
                             for _ in range(self.nb_simulations)]
                
                victoires = {c: 0 for c in jouables}
                scores = {c: 0.0 for c in jouables}
                
                for m_sim in mains_ech:
                    bel = belote_imaginee(m_sim, self.historique, atout)
                    for c in jouables:
                        pts_tot, plis_tot = self.simuler_avec_ia(m_sim, pli, atout, contrat, joueur, c, regles)
                        reussi = contrat_reussi(contrat, pts_tot[attaque], plis_tot[attaque], bel == attaque, regles)
                        gagne = reussi if eq == attaque else not reussi
                        if gagne:
                            victoires[c] += 1
                        scores[c] += (1000.0 if gagne else -1000.0) + (pts_tot[eq] - pts_tot[1 - eq])

                c_top_mc = max(jouables, key=scores.get)
                tries = sorted(jouables, key=scores.get, reverse=True)
                
                # Si écart serré (<= 2 victoires sur 20) : l'IA départage
                c1, c2 = tries[0], tries[1]
                if abs(victoires[c1] - victoires[c2]) <= 2:
                    self.ia.historique = list(self.historique)
                    self.ia.encheres = list(self.encheres)
                    c_ia = self.ia.jouer_carte(main, jouables, pli, contrat, joueur, regles)
                    # Si l'IA préfère l'une des cartes du peloton de tête, on la suit
                    if c_ia in (c1, c2):
                        return c_ia
                return c_top_mc
            finally:
                bot_mc_ia.imaginer_donnes_contraintes = ancien

        # Plis 3 à 8 : 100% MC v3 standard
        return super().jouer_carte(main, jouables, pli, contrat, joueur, regles)


MOTS = {
    "hyb_p1": BotHybridePli1,
    "hyb_mix_p2": BotHybrideMixPli2,
    "hyb_p1_p2": BotHybridePlis1et2,
    "v3_std": BotMCIAv3,
}

print(f"=== BENCHMARK HYBRIDE PLI 2 : {NB_DONNES} donnes appariées ===")
print("Référence : hyb_p1 (IA au Pli 1, MC 20 sim. ensuite)")
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

    for nom, cls_bot in MOTS.items():
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
        marque_table, reussi = decompte(contrat, pts_eq, plis_eq, bel, REGLES_STANDARD)

        gagne = reussi if role == "attaque" else not reussi
        pts_faits = pts_eq[camp_teste]
        marque_camp = (valeur_contrat * mult_coinche) if gagne else (-valeur_contrat * mult_coinche)

        res_pts[nom].append(pts_faits)
        res_sec[nom].append(dt)
        res_ok[nom].append(gagne)
        res_marque[nom].append(marque_camp)

    if donnes_jouees % 25 == 0:
        ecoule = time.time() - t_debut
        m_p1 = np.mean(res_marque["hyb_p1"])
        m_mix = np.mean(res_marque["hyb_mix_p2"])
        m_p12 = np.mean(res_marque["hyb_p1_p2"])
        m_std = np.mean(res_marque["v3_std"])
        print(f"  {donnes_jouees:3d}/{NB_DONNES} donnes | {ecoule/60:4.1f} min | Marque: Hyb_P1={m_p1:+.1f} | Mix_P2={m_mix:+.1f} | Hyb_P1-2={m_p12:+.1f} | v3={m_std:+.1f}", flush=True)

print("\n" + "=" * 75)
print(f"RÉSULTATS SUR {donnes_jouees} DONNES APPARIÉES :")
print("=" * 75)
print(f"{'Moteur':<16} | {'Pts faits':>9} | {'Succès':>7} | {'Temps/partie':>12} | {'Marque moy.':>11} | {'Écart vs Hyb_P1':>16}")
print("-" * 75)

ref = np.array(res_marque["hyb_p1"], dtype=float)
for nom in ["hyb_p1", "hyb_mix_p2", "hyb_p1_p2", "v3_std"]:
    pts_m = np.mean(res_pts[nom])
    taux = 100 * np.mean(res_ok[nom])
    sec_m = np.mean(res_sec[nom])
    marq = np.array(res_marque[nom], dtype=float)
    marq_m = marq.mean()

    ecart = marq - ref
    marge = 1.96 * ecart.std(ddof=1) / np.sqrt(len(ecart)) if nom != "hyb_p1" else 0.0
    txt_ecart = f"{ecart.mean():+6.1f} ± {marge:4.1f}" if nom != "hyb_p1" else "référence"

    print(f"{nom:<16} | {pts_m:9.1f} | {taux:6.1f}% | {sec_m:10.2f}s | {marq_m:+11.1f} | {txt_ecart:>16}")
