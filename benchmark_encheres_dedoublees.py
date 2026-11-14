"""
benchmark_encheres_dedoublees.py
VRAI PROTOCOLE DE DUEL D'ENCHÈRES :
Chaque table déroule sa propre phase d'annonces sur les mêmes cartes de départ !
- Table A : Sud et Nord annoncent avec les RÈGLES OBJECTIVES (4 critères).
- Table B : Sud et Nord annoncent avec la SIMULATION COMBAT (Monte-Carlo si > +10).
Les adversaires (Ouest et Est) annoncent avec JoueurIA_V2.
Le jeu de la carte est résolu pour les deux par le champion BotMCIAv6.
"""
import os, sys, time, json, random
import numpy as np
import torch
from regles import REGLES_STANDARD
from moteur import distribuer, cartes_jouables, gagnant_pli, points, equipe_belote, decompte
from partie import phase_annonces
from test_mc_encheres import MCEncheres
from ia_modele_v2 import JoueurIA_V2
from bot_mc_ia_v6 import BotMCIAv6, FICHIER_V6_RESEAU
from detective_v3 import imaginer_v3
from montecarlo import belote_imaginee, contrat_reussi

NB_DONNES = 250
GRAINE_BASE = 600_000_000


# Joueur pour la Table A : Annonces selon les règles objectives de systeme.py
class JoueurEnchereRegles(JoueurIA_V2):
    nom = "Ench_Regles"


# Joueur pour la Table B : Simule dès que la surenchère dépasse de plus de 10 points
class JoueurEnchereSimul(JoueurIA_V2):
    nom = "Ench_Simul"
    bot_sim = BotMCIAv6(nb_simulations=1, fichier_reseau=FICHIER_V6_RESEAU)

    def decision_disputee(self, main, joueur, contrat, regles, coul_notre_camp, val_actuelle_camp):
        if contrat is None or contrat["joueur"] % 2 == joueur % 2:
            return None

        val_suivante = contrat["valeur"] + regles["palier"]
        depassement = val_suivante - val_actuelle_camp

        # Si le combat exige de monter à +20 ou plus : simulation réelle !
        if depassement >= 20 and val_suivante <= 140:
            c_passe = dict(contrat)
            c_monter = {"valeur": val_suivante, "atout": coul_notre_camp, "joueur": joueur, "coinche": 0, "capot": False}

            # 20 simulations avec réseau V2
            mains_sims = [imaginer_v3(main, joueur, [], list(self.encheres) if self.encheres else [], coul_notre_camp, regles) for _ in range(20)]

            gains_passe, gains_monter = [], []
            mult_p = 2 if c_passe.get("coinche", 0) > 0 else 1
            v_p = c_passe["valeur"]
            camp_adv = c_passe["joueur"] % 2

            for m_v in mains_sims:
                # Option 1 : Laisser jouer
                pts_p, pl_p = self.bot_sim.simuler_avec_ia_v2(m_v, [], c_passe["atout"], c_passe, joueur, m_v[joueur][0], regles)
                bel_p = belote_imaginee(m_v, [], c_passe["atout"])
                adv_reussit = contrat_reussi(c_passe, pts_p[camp_adv], pl_p[camp_adv], bel_p == camp_adv, regles)
                gains_passe.append(v_p * mult_p if not adv_reussit else -v_p * mult_p)

                # Option 2 : Monter
                pts_m, pl_m = self.bot_sim.simuler_avec_ia_v2(m_v, [], coul_notre_camp, c_monter, joueur, m_v[joueur][0], regles)
                bel_m = belote_imaginee(m_v, [], coul_notre_camp)
                nous_ok = contrat_reussi(c_monter, pts_m[joueur % 2], pl_m[joueur % 2], bel_m == (joueur % 2), regles)
                gains_monter.append(val_suivante if nous_ok else -val_suivante)

            esp_p = np.mean(gains_passe)
            esp_m = np.mean(gains_monter)

            if esp_m > esp_p and esp_m >= -20:
                return (val_suivante, coul_notre_camp)
            else:
                return "passe"

        return None


def jouer_carte_partie(mains_init, contrat, encheres, donneur, graine):
    """Fait jouer la manche par le champion BotMCIAv6 en camp 0 face à MCEncheres."""
    random.seed(graine * 10 + 7); np.random.seed((graine * 10 + 7) % 2**32); torch.manual_seed(graine * 10 + 7)
    mains_c = [list(m) for m in mains_init]
    bot = BotMCIAv6(nb_simulations=40)
    adv = MCEncheres()
    hist = []
    p_eq = [0, 0]
    prem = (donneur + 1) % 4
    atout = contrat["atout"]
    val = contrat["valeur"]
    mult = 2 if contrat.get("coinche", 0) > 0 else 1
    role = "attaque" if contrat["joueur"] % 2 == 0 else "defense"

    while len(hist) < 32:
        pli = []
        for step in range(4):
            j = (prem + step) % 4
            jbs = cartes_jouables(mains_c[j], pli, atout, j, REGLES_STANDARD)
            if j % 2 == 0:
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

    bel = equipe_belote(mains_init, atout)
    _, reussi = decompte(contrat, p_eq, [0, 0], bel, REGLES_STANDARD)
    gagne = reussi if role == "attaque" else not reussi
    marque = (val * mult) if gagne else (-val * mult)
    return p_eq[0], marque, gagne


print(f"=== DUEL D'ENCHÈRES EN DUPLICATE SÉPARÉ ({NB_DONNES} donnes) ===")
print("Table A (Règles objectives) vs Table B (Simulation combat Monte-Carlo)")
print("-" * 75)

marques_A = []
marques_B = []
contrats_differents = 0
donnes_jouees = 0
t0 = time.time()

for g in range(GRAINE_BASE, GRAINE_BASE + NB_DONNES * 3):
    if donnes_jouees >= NB_DONNES:
        break

    random.seed(g); np.random.seed(g % 2**32); torch.manual_seed(g)
    mains_init = distribuer()
    donneur = g % 4

    # --- TABLE A : Sud et Nord annoncent avec RÈGLES OBJECTIVES ---
    random.seed(g * 100 + 1)
    joueurs_A = [
        JoueurEnchereRegles(),          # Sud (0)
        JoueurIA_V2(fichier=FICHIER_V6_RESEAU),  # Ouest (1, adv)
        JoueurEnchereRegles(),          # Nord (2)
        JoueurIA_V2(fichier=FICHIER_V6_RESEAU),  # Est (3, adv)
    ]
    contrat_A = phase_annonces(mains_init, donneur, joueurs_A, REGLES_STANDARD, afficher=False)
    if contrat_A is None:
        continue

    # --- TABLE B : Sud et Nord annoncent avec SIMULATION COMBAT ---
    random.seed(g * 100 + 1)
    joueurs_B = [
        JoueurEnchereSimul(),           # Sud (0)
        JoueurIA_V2(fichier=FICHIER_V6_RESEAU),  # Ouest (1, adv)
        JoueurEnchereSimul(),           # Nord (2)
        JoueurIA_V2(fichier=FICHIER_V6_RESEAU),  # Est (3, adv)
    ]
    contrat_B = phase_annonces(mains_init, donneur, joueurs_B, REGLES_STANDARD, afficher=False)
    if contrat_B is None:
        continue

    donnes_jouees += 1
    ench_A = list(joueurs_A[(donneur + 1) % 4].encheres)
    ench_B = list(joueurs_B[(donneur + 1) % 4].encheres)

    # Vérifier si les deux tables ont abouti à un contrat différent
    contrat_diff = (contrat_A["valeur"] != contrat_B["valeur"] or
                    contrat_A["atout"] != contrat_B["atout"] or
                    contrat_A["joueur"] != contrat_B["joueur"] or
                    contrat_A.get("coinche", 0) != contrat_B.get("coinche", 0))

    if contrat_diff:
        contrats_differents += 1

    # Jouer la carte pour la Table A
    _, marq_A, _ = jouer_carte_partie(mains_init, contrat_A, ench_A, donneur, g)
    # Jouer la carte pour la Table B
    _, marq_B, _ = jouer_carte_partie(mains_init, contrat_B, ench_B, donneur, g)

    marques_A.append(marq_A)
    marques_B.append(marq_B)

    if donnes_jouees % 25 == 0:
        ec = time.time() - t0
        mA = np.mean(marques_A)
        mB = np.mean(marques_B)
        diff = mB - mA
        print(f"  {donnes_jouees:3d}/{NB_DONNES} donnes | {ec/60:4.1f} min | Règles={mA:+5.1f} vs Simul={mB:+5.1f} (diff: {diff:+5.1f}) [Contrats diff: {contrats_differents}]", flush=True)

print("\n" + "=" * 75)
print(f"RÉSULTATS DUEL D'ENCHÈRES SÉPARÉES SUR {donnes_jouees} DONNES :")
print("=" * 75)
mA_arr = np.array(marques_A, dtype=float)
mB_arr = np.array(marques_B, dtype=float)
ecart = mB_arr - mA_arr
marge = 1.96 * ecart.std(ddof=1) / np.sqrt(len(ecart))

print(f"Donnes avec décision d'enchère divergente : {contrats_differents}/{donnes_jouees} ({100*contrats_differents/donnes_jouees:.1f} %)")
print(f"Marque moyenne Table A (Règles objectives) : {mA_arr.mean():+5.1f} pts")
print(f"Marque moyenne Table B (Simulation combat) : {mB_arr.mean():+5.1f} pts")
print(f"Écart net (Simulation - Règles) : {ecart.mean():+5.1f} ± {marge:.1f} pts de marque")
print("-" * 75)
print(f"Donnes où la Simulation bat les Règles : {sum(1 for e in ecart if e > 0)}")
print(f"Donnes où les Règles battent la Simulation : {sum(1 for e in ecart if e < 0)}")
print(f"Donnes identiques en marque : {sum(1 for e in ecart if e == 0)}")
