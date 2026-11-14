"""
benchmark_v4_pur.py
Teste l'approche pure sans dilution :
Le détective collecte entre 10 et 20 mains v4 pures (sans forcer 40 simuls, sans diluer avec du v3).
Mesure appariée sur 300 donnes neuves vs v3 (40 sim.).
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
from detective_v4_1 import moments_a_lire, coherente, tirage_naif, rejouer_encheres, nb_differences, vraisemblance_avec_ia
from montecarlo import belote_imaginee, contrat_reussi
import bot_mc_ia

NB_DONNES = 300
PREMIERE_GRAINE = 13_500_000


class BotHybrideV3_40(BotMCIA):
    nom = "Hybride v3 (40 sim.)"
    def __init__(self):
        super().__init__()
        self.nb_simulations = 40
        self.ia = JoueurIA()

    def jouer_carte(self, main, jouables, pli, contrat, joueur, regles):
        if len(jouables) == 1:
            return jouables[0]
        if len(self.historique) < 12:
            self.ia.historique = list(self.historique)
            self.ia.encheres = list(self.encheres)
            return self.ia.jouer_carte(main, jouables, pli, contrat, joueur, regles)
        
        ancien = bot_mc_ia.imaginer_donnes_contraintes
        bot_mc_ia.imaginer_donnes_contraintes = imaginer_v3
        try:
            return super().jouer_carte(main, jouables, pli, contrat, joueur, regles)
        finally:
            bot_mc_ia.imaginer_donnes_contraintes = ancien


class BotHybrideV4Pur(BotMCIA):
    nom = "Hybride v4 Pur (10-20 mains)"
    def __init__(self):
        super().__init__()
        self.ia = JoueurIA()
        self.stats_pool = []

    def _collecter_mains_pures(self, main, joueur, atout, contrat, regles, min_mains=10, max_mains=20, max_essais=300):
        moments = moments_a_lire(self.historique, joueur, atout)
        if not moments:
            return [imaginer_v3(main, joueur, self.historique, self.encheres, atout, regles) for _ in range(max_mains)]

        pures = []
        donneur = (self.encheres[0][0] - 1) % 4 if self.encheres else 0

        for _ in range(max_essais):
            imag = tirage_naif(main, joueur, self.historique)
            if not coherente(imag, self.historique, atout, regles):
                continue

            depart = [list(m) for m in imag]
            for j, c in self.historique:
                depart[j].append(c)

            d = nb_differences(self.encheres, rejouer_encheres(depart, donneur, regles)) if self.encheres else 0
            if random.random() >= (0.1 ** d):
                continue

            lu = 1.0
            for i in moments:
                lu *= vraisemblance_avec_ia(imag, self.historique, i, contrat, self.encheres, regles)

            if random.random() < lu:
                pures.append(imag)
                if len(pures) >= max_mains:
                    break

        # Si au moins min_mains trouvées : pool pur !
        if len(pures) >= min_mains:
            return pures

        # Cas rare (< min_mains) : compléter le reliquat avec v3 pour la stabilité
        while len(pures) < min_mains:
            pures.append(imaginer_v3(main, joueur, self.historique, self.encheres, atout, regles))
        return pures

    def jouer_carte(self, main, jouables, pli, contrat, joueur, regles):
        if len(jouables) == 1:
            return jouables[0]
        # Plis 1-3 en IA
        if len(self.historique) < 12:
            self.ia.historique = list(self.historique)
            self.ia.encheres = list(self.encheres)
            return self.ia.jouer_carte(main, jouables, pli, contrat, joueur, regles)

        # Plis 4 à 8 : Monte-Carlo sur le pool de mains pures (sans dilution)
        atout = contrat["atout"]
        eq, attaque = joueur % 2, contrat["joueur"] % 2

        mains_pool = self._collecter_mains_pures(main, joueur, atout, contrat, regles)
        self.stats_pool.append(len(mains_pool))

        scores = {c: 0.0 for c in jouables}
        for m_sim in mains_pool:
            bel = belote_imaginee(m_sim, self.historique, atout)
            for c in jouables:
                pts_tot, plis_tot = self.simuler_avec_ia(m_sim, pli, atout, contrat, joueur, c, regles)
                reussi = contrat_reussi(contrat, pts_tot[attaque], plis_tot[attaque], bel == attaque, regles)
                gagne = reussi if eq == attaque else not reussi
                scores[c] += (1000.0 if gagne else -1000.0) + (pts_tot[eq] - pts_tot[1 - eq])

        return max(jouables, key=scores.get)


MOTS = {
    "v3_40sim": BotHybrideV3_40,
    "v4_pur": BotHybrideV4Pur,
}

print(f"=== BENCHMARK V4 PUR (SANS DILUTION) : {NB_DONNES} donnes appariées ===")
print("v3 (40 sim.) vs v4 Pur (10 à 20 mains pures)")
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
        m_v3 = np.mean(res_marque["v3_40sim"])
        m_v4 = np.mean(res_marque["v4_pur"])
        diff = m_v4 - m_v3
        print(f"  {donnes_jouees:3d}/{NB_DONNES} donnes | {ecoule/60:4.1f} min | Marque: v3_40={m_v3:+.1f} vs v4_pur={m_v4:+.1f} (écart: {diff:+.1f})", flush=True)

print("\n" + "=" * 75)
print(f"RÉSULTATS SUR {donnes_jouees} DONNES APPARIÉES :")
print("=" * 75)
print(f"{'Moteur':<18} | {'Pts faits':>9} | {'Succès':>7} | {'Temps/partie':>12} | {'Marque moy.':>11} | {'Écart vs v3_40':>16}")
print("-" * 75)

ref = np.array(res_marque["v3_40sim"], dtype=float)
for nom in ["v3_40sim", "v4_pur"]:
    pts_m = np.mean(res_pts[nom])
    taux = 100 * np.mean(res_ok[nom])
    sec_m = np.mean(res_sec[nom])
    marq = np.array(res_marque[nom], dtype=float)
    marq_m = marq.mean()

    ecart = marq - ref
    marge = 1.96 * ecart.std(ddof=1) / np.sqrt(len(ecart)) if nom != "v3_40sim" else 0.0
    txt_ecart = f"{ecart.mean():+6.1f} ± {marge:4.1f}" if nom != "v3_40sim" else "référence"

    print(f"{nom:<18} | {pts_m:9.1f} | {taux:6.1f}% | {sec_m:10.2f}s | {marq_m:+11.1f} | {txt_ecart:>16}")
