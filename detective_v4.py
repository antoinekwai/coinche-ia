"""
detective_v4.py
Détective v3 + lecture des cartes jouées : chaque main imaginée est pondérée par
la probabilité, selon le réseau, que l'entame et les premières défausses aient été jouées.
"""
import math
import random
import numpy as np
import torch
from moteur import cartes_jouables
from ia_joueur import charger, FICHIER
from ia_encodage import encoder_situation, encoder_carte
from detective_v2 import coherente
from detective_v3 import tirage_naif, rejouer_encheres, nb_differences

PLANCHER = 0.05        # une main n'est jamais totalement exclue (erreurs, choix tactiques)
STATS_V4 = {"appels": 0, "echecs": 0}
ECARTS = []            # diagnostic : écart de note entre la carte jouée et la préférée



def moments_a_lire(historique, joueur, atout):
    """Positions des cartes riches en information : entame de la donne,
    puis première défausse de chaque autre joueur."""
    moments = []
    if historique and historique[0][0] != joueur:
        moments.append(0)
    deja = set()
    for i, (j, c) in enumerate(historique):
        if i % 4 == 0 or j == joueur or j in deja:
            continue
        demandee = historique[i - i % 4][1][1]
        if c[1] != demandee and c[1] != atout:
            moments.append(i)
            deja.add(j)
    return moments


def vraisemblance(imag, historique, i, contrat, encheres, regles, temperature):
    """Probabilité relative (entre PLANCHER et 1) que le joueur ait joué cette carte."""
    j, carte = historique[i]
    # Main du joueur à ce moment : cartes imaginées + cartes qu'il a jouées depuis
    main = list(imag[j]) + [c for k, (p, c) in enumerate(historique) if p == j and k >= i]
    pli = list(historique[i - i % 4:i])
    jouables = cartes_jouables(main, pli, contrat["atout"], j, regles)
    if len(jouables) < 2 or carte not in jouables:
        return 1.0
    s = encoder_situation(main, pli, list(historique[:i]), contrat, j, regles, encheres)
    vec = np.stack([encoder_carte(c, contrat["atout"]) for c in jouables])
    x = np.concatenate([np.repeat(s[None, :], len(jouables), axis=0), vec], axis=1)
    with torch.no_grad():
        notes = charger(FICHIER)(torch.from_numpy(x)).squeeze(1).numpy()
    ecart = notes[jouables.index(carte)] - notes.max()     # 0 si c'était la carte préférée
    ECARTS.append(float(ecart))
    return max(PLANCHER, math.exp(ecart / temperature))


def imaginer_v4(main, joueur, historique, encheres, atout, regles, contrat,
                temperature=0.1, tolerance=0.1, max_essais=300):
    STATS_V4["appels"] += 1
    donneur = (encheres[0][0] - 1) % 4 if encheres else 0
    moments = moments_a_lire(historique, joueur, atout)
    meilleure, meilleur_poids = None, -1.0
    for _ in range(max_essais):
        imag = tirage_naif(main, joueur, historique)
        if not coherente(imag, historique, atout, regles):
            continue                                    # contredit les règles du jeu
        depart = [list(m) for m in imag]
        for j, c in historique:
            depart[j].append(c)
        d = nb_differences(encheres, rejouer_encheres(depart, donneur, regles)) if encheres else 0
        poids = tolerance ** d
        if random.random() >= poids:                    # 1er filtre : les enchères (rapide)
            if poids > meilleur_poids:
                meilleure, meilleur_poids = imag, poids
            continue
        lu = 1.0                                        # 2e filtre : les cartes jouées
        for i in moments:
            lu *= vraisemblance(imag, historique, i, contrat, encheres, regles, temperature)
        if random.random() < lu:
            return imag
        if poids * lu > meilleur_poids:
            meilleure, meilleur_poids = imag, poids * lu
    STATS_V4["echecs"] += 1
    return meilleure if meilleure is not None else tirage_naif(main, joueur, historique)
