"""
benchmark_duel_encheres.py
Duel de doctrine d'enchères disputées sur 500 donnes appariées :
- v6_regles : Surenchère régie par les 4 critères objectifs (5 atouts / 4 atouts+chicane / Belote / soutien)
- v6_simul_combat : Surenchère décidée par simulation Monte-Carlo directe (espérance de marque sur 25 donnes)
Les deux bots ont STRICTEMENT le même jeu de la carte d'élite (v6).
"""
import os, sys, time, json, random
import numpy as np
import torch
from regles import REGLES_STANDARD
from moteur import distribuer, cartes_jouables, gagnant_pli, points, equipe_belote, decompte, COULEURS
from partie import phase_annonces
from test_mc_encheres import MCEncheres
from ia_modele_v2 import JoueurIA_V2
from bot_mc_ia_v6 import BotMCIAv6, FICHIER_V6_RESEAU
from detective_v3 import imaginer_v3
from detective_v5 import imaginer_v5
from montecarlo import belote_imaginee, contrat_reussi

NB_DONNES = 500
GRAINE_BASE = 500_000_000

# 1. Bot avec les 4 règles objectives (notre code actuel de systeme.py)
class BotV6_Regles(BotMCIAv6):
    nom = "v6 (Règles objectives)"


# 2. Bot avec simulation Monte-Carlo directe dès que l'adversaire surenchérit au-delà de +10
class BotV6_SimulCombat(BotMCIAv6):
    nom = "v6 (Simulation combat)"

    def decision_disputee(self, main, joueur, contrat, regles, coul_notre_camp, val_actuelle_camp):
        """Prend la décision de combat par simulation Monte-Carlo au lieu de la règle de marge."""
        if contrat is None or contrat["joueur"] % 2 == joueur % 2:
            return None # Pas d'adversaire à combattre
            
        val_suivante = contrat["valeur"] + regles["palier"]
        depassement = val_suivante - val_actuelle_camp
        
        # Si le dépassement est de 10 points : monter est standard (pas besoin de simuler)
        if depassement <= 10:
            return None # Laisse la règle de base faire
            
        # Si le dépassement est de +20 ou plus : ARBITRAGE PAR SIMULATION RÉELLE !
        if val_suivante <= 140:
            c_passe = dict(contrat)
            c_monter = {"valeur": val_suivante, "atout": coul_notre_camp, "joueur": joueur, "coinche": 0, "capot": False}
            
            # 20 simulations rapides avec réseau V2
            mains_sims = [imaginer_v3(main, joueur, [], list(self.encheres) if self.encheres else [], coul_notre_camp, regles) for _ in range(20)]
            
            gains_passe, gains_monter = [], []
            mult_p = 2 if c_passe.get("coinche", 0) > 0 else 1
            v_p = c_passe["valeur"]
            camp_adv = c_passe["joueur"] % 2
            
            for m_v in mains_sims:
                # Si on laisse jouer l'adversaire
                pts_p, pl_p = self.simuler_avec_ia_v2(m_v, [], c_passe["atout"], c_passe, joueur, m_v[joueur][0], regles)
                bel_p = belote_imaginee(m_v, [], c_passe["atout"])
                adv_reussit = contrat_reussi(c_passe, pts_p[camp_adv], pl_p[camp_adv], bel_p == camp_adv, regles)
                gains_passe.append(v_p * mult_p if not adv_reussit else -v_p * mult_p)
                
                # Si on surenchère à notre palier
                pts_m, pl_m = self.simuler_avec_ia_v2(m_v, [], coul_notre_camp, c_monter, joueur, m_v[joueur][0], regles)
                bel_m = belote_imaginee(m_v, [], coul_notre_camp)
                nous_reussissons = contrat_reussi(c_monter, pts_m[joueur % 2], pl_m[joueur % 2], bel_m == (joueur % 2), regles)
                gains_monter.append(val_suivante if nous_reussissons else -val_suivante)
                
            esp_passe = np.mean(gains_passe)
            esp_monter = np.mean(gains_monter)
            
            # On ne monte que si l'espérance de surenchère est STRICTEMENT MEILLEURE que de laisser jouer !
            if esp_monter > esp_passe and esp_monter >= -20:
                return (val_suivante, coul_notre_camp)
            else:
                return "passe"
                
        return "passe"


MOTS = {
    "v6_regles": BotV6_Regles,
    "v6_simul_combat": BotV6_SimulCombat,
}

print(f"=== DUEL D'ENCHÈRES DISPUTÉES : {NB_DONNES} donnes appariées ===")
print("v6 (Règles objectives) vs v6 (Simulation Monte-Carlo combat)")
print("-" * 75)

donnes_jouees = 0
res_pts = {m: [] for m in MOTS}
res_sec = {m: [] for m in MOTS}
res_ok = {m: [] for m in MOTS}
res_marque = {m: [] for m in MOTS}

t_debut = time.time()

for g in range(GRAINE_BASE, GRAINE_BASE + NB_DONNES * 3):
    if donnes_jouees >= NB_DONNES:
        break

    random.seed(g); np.random.seed(g % 2**32); torch.manual_seed(g)
    mains_init = distribuer()
    donneur = g % 4
    joueurs_ench = [JoueurIA_V2(fichier=FICHIER_V6_RESEAU) for _ in range(4)]
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
        hist, p_eq = [], [0, 0]
        prem = (donneur + 1) % 4

        t0 = time.time()
        while len(hist) < 32:
            pli = []
            for step in range(4):
                j = (prem + step) % 4
                jbs = cartes_jouables(mains_c[j], pli, atout, j, REGLES_STANDARD)
                if j % 2 == camp:
                    bot.historique = list(hist); bot.encheres = list(encheres)
                    c = bot.jouer_carte(mains_c[j], jbs, pli, contrat, j, REGLES_STANDARD)
                else:
                    adv.historique = list(hist); adv.encheres = list(encheres)
                    c = adv.jouer_carte(mains_c[j], jbs, pli, contrat, j, REGLES_STANDARD)
                mains_c[j].remove(c)
                pli.append((j, c))
                hist.append((j, c))
            g_pli = gagnant_pli(pli, atout)[0]
            prem = g_pli
            p_eq[g_pli % 2] += sum(points(cc, atout) for _, cc in pli)
            if len(hist) == 32: p_eq[g_pli % 2] += REGLES_STANDARD["dix_de_der"]

        dt = time.time() - t0
        bel = equipe_belote(mains_init, atout)
        _, reussi = decompte(contrat, p_eq, [0,0], bel, REGLES_STANDARD)
        gagne = reussi if role == "attaque" else not reussi
        marque_camp = (val * mult) if gagne else (-val * mult)

        res_pts[nom].append(p_eq[camp])
        res_sec[nom].append(dt)
        res_ok[nom].append(gagne)
        res_marque[nom].append(marque_camp)

    if donnes_jouees % 50 == 0:
        ec = time.time() - t_debut
        m_reg = np.mean(res_marque["v6_regles"])
        m_sim = np.mean(res_marque["v6_simul_combat"])
        diff = m_sim - m_reg
        print(f"  {donnes_jouees:3d}/{NB_DONNES} donnes | {ec/60:4.1f} min | Marque: Règles={m_reg:+.1f} vs Simul={m_sim:+.1f} (diff: {diff:+.1f})", flush=True)

print("\n" + "=" * 75)
print(f"RÉSULTATS SUR {donnes_jouees} DONNES APPARIÉES :")
print("=" * 75)
m_reg_arr = np.array(res_marque["v6_regles"], dtype=float)
m_sim_arr = np.array(res_marque["v6_simul_combat"], dtype=float)
ecart = m_sim_arr - m_reg_arr
marge = 1.96 * ecart.std(ddof=1) / np.sqrt(len(ecart))

for nom in MOTS:
    p_m = np.mean(res_pts[nom])
    tx = 100 * np.mean(res_ok[nom])
    sc_m = np.mean(res_sec[nom])
    mq = np.mean(res_marque[nom])
    txt_diff = f"{ecart.mean():+.1f} ± {marge:.1f}" if nom == "v6_simul_combat" else "référence"
    print(f"{nom:<18} | Pts faits: {p_m:5.1f} | Succès: {tx:5.1f}% | Temps: {sc_m:4.2f}s | Marque: {mq:+6.1f} | Diff: {txt_diff}")
