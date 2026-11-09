"""
coinche_champion.py
Décision officielle de Coinche par simulation avec Partenaire Minimaliste :
1. Place le partenaire dans le pire scénario (main blanche, 0 As extérieur).
2. Place le preneur dans sa version haute via Détective v5.
3. Déroule 25 simulations avec le réseau neuronal V2 de BotMCIAv6.
4. Seuil de décision : 70% de chutes prouvées.
   -> Refuse les coinches prématurées à 80 (laisse parler ou monter l'adversaire).
   -> Déclenche les coinches ravageuses dès 90-100+.
"""
import random
import numpy as np
import torch
from regles import REGLES_STANDARD
from moteur import COULEURS, cartes_jouables, gagnant_pli, points, decompte, equipe_belote
from detective_v5 import tirage_guide_v5
from bot_mc_ia_v6 import BotMCIAv6, FICHIER_V6_RESEAU
from montecarlo import belote_imaginee, contrat_reussi

_BOT_EVALUATEUR = BotMCIAv6(nb_simulations=1, fichier_reseau=FICHIER_V6_RESEAU)


def veut_coincher_champion(main, joueur, contrat, encheres, regles=None, nb_simuls=25, seuil_chute=0.70):
    """
    Évalue si le joueur doit coincher le contrat adverse.
    Ne compte JAMAIS sur le partenaire (partenaire minimaliste, zéro As extérieur).
    """
    if contrat is None:
        return False

    camp_preneur = contrat["joueur"] % 2
    mon_camp = joueur % 2
    if camp_preneur == mon_camp:
        return False  # On ne coinche jamais son propre camp !

    atout = contrat["atout"]
    partenaire = (joueur + 2) % 4
    r = regles or REGLES_STANDARD

    # Règle de bon sens préalable : avoir au moins 2 atouts ou 1 maître (V ou 9)
    atouts_main = [c for c in main if c[1] == atout]
    if len(atouts_main) < 2 and not any(c[0] in ("V", "9") for c in atouts_main):
        return False

    chutes_comptees = 0
    contrat_sim = dict(contrat)
    contrat_sim["coinche"] = 1

    for s_idx in range(nb_simuls):
        random.seed(123456 + s_idx * 19)
        mains_sim = tirage_guide_v5(main, joueur, [], encheres, atout, r)

        # Application du partenaire minimaliste (échange propre d'As avec l'adversaire Est)
        adv_est = (mon_camp + 3) % 4
        as_part = [c for c in mains_sim[partenaire] if c[0] == "A" and c[1] != atout]
        for a_carte in as_part:
            petites_est = [c for c in mains_sim[adv_est] if c[0] in ("7", "8", "9") and c[1] != atout]
            if petites_est:
                carte_ech = petites_est[0]
                mains_sim[partenaire].remove(a_carte)
                mains_sim[adv_est].remove(carte_ech)
                mains_sim[partenaire].append(carte_ech)
                mains_sim[adv_est].append(a_carte)

        # Simulation de la donne complète par le réseau V2 d'élite
        m_jeu = [list(mm) for mm in mains_sim]
        hist = []
        pts_eq = [0, 0]
        premier = (contrat["joueur"]) % 4

        while len(hist) < 32:
            pli = []
            for step in range(4):
                j = (premier + step) % 4
                jbs = cartes_jouables(m_jeu[j], pli, atout, j, r)
                c = _BOT_EVALUATEUR.ia_v2.jouer_carte(m_jeu[j], jbs, pli, contrat_sim, j, r)
                m_jeu[j].remove(c)
                pli.append((j, c))
                hist.append((j, c))
            g = gagnant_pli(pli, atout)[0]
            premier = g
            p = sum(points(cc, atout) for _, cc in pli)
            if len(hist) == 32: p += r["dix_de_der"]
            pts_eq[g % 2] += p

        bel = equipe_belote(mains_sim, atout)
        _, reussi = decompte(contrat_sim, pts_eq, [0, 0], bel, r)
        
        # Le preneur adverse a-t-il chuté ?
        if not reussi:
            chutes_comptees += 1

    taux_chute = chutes_comptees / nb_simuls
    return taux_chute >= seuil_chute
