"""
ia_encodage_v2.py
Encodage enrichi V2 pour le réseau de neurones :
- Reprend la base éprouvée de ia_encodage.py (281 nombres).
- AJOUTE 9 descripteurs de situation et 2 descripteurs par carte candidate :
  1. atouts_inconnus / 8.0 (1 float)
  2. defense_purgee (1 bit)
  3. couleur_demandee au pli (4 bits)
  4. pli_actuellement_a_nous (1 bit)
  5. pli_garanti_a_notre_camp (1 bit)
  6. points_du_pli / 45.0 (1 float)
  7. candidat_est_maitre_couleur (1 bit sur la carte candidate)
  8. candidat_est_maitre_absolu (1 bit sur la carte candidate)

Total :
  TAILLE_SITUATION_V2 = 290
  TAILLE_CARTE_V2     = 34
  ENTRÉE TOTALE       = 324 neurones (vs 313 en V1)
"""
import numpy as np
from moteur import COULEURS, RANGS, points, gagnant_pli
from montecarlo import manques, bilan_passe

TAILLE_CARTE_V2 = 34
TAILLE_SITUATION_V2 = 290


def ordre_couleurs(atout):
    """L'atout toujours en premier, puis ordre fixe des autres couleurs."""
    return [atout] + [c for c in COULEURS if c != atout]


def indice(carte, ordre):
    """Indice de la carte (0 à 31) dans le référentiel centré sur l'atout."""
    rang, couleur = carte
    rangs = (["V", "9", "A", "10", "R", "D", "8", "7"] if couleur == ordre[0]
             else ["A", "10", "R", "D", "V", "9", "8", "7"])
    return 8 * ordre.index(couleur) + rangs.index(rang)


def cartes_sont_vivantes_superieures(carte, atout, cartes_vues):
    """Vérifie s'il reste dans la nature (hors cartes_vues) une carte qui bat `carte`
    dans la MÊME couleur."""
    rang, couleur = carte
    ordre_rangs = (["V", "9", "A", "10", "R", "D", "8", "7"] if couleur == atout
                   else ["A", "10", "R", "D", "V", "9", "8", "7"])
    idx = ordre_rangs.index(rang)
    for r_sup in ordre_rangs[:idx]:
        if (r_sup, couleur) not in cartes_vues:
            return True  # Il reste une carte supérieure vivante dehors
    return False


def encoder_carte_v2(carte, atout, main, historique, pli, defense_purgee):
    """Encode la carte candidate (34 bits) :
    - 32 bits : one-hot de la carte
    - bit 32  : est maîtresse de sa couleur (1.0 ou 0.0)
    - bit 33  : est maîtresse absolue (1.0 ou 0.0)
    """
    v = np.zeros(TAILLE_CARTE_V2, dtype=np.float32)
    ordre = ordre_couleurs(atout)
    v[indice(carte, ordre)] = 1.0

    # Cartes connues de moi : celles déjà jouées + celles que j'ai moi-même en main
    cartes_connues = {c for _, c in historique} | {c for _, c in pli} | set(main)

    # 1. Maîtresse de sa couleur
    est_maitre_coul = not cartes_sont_vivantes_superieures(carte, atout, cartes_connues)
    v[32] = 1.0 if est_maitre_coul else 0.0

    # 2. Maîtresse absolue (imparable) :
    # Soit c'est de l'atout maître, soit c'est un maître de couleur ET la défense est purgée d'atouts
    est_maitre_abs = est_maitre_coul and ((carte[1] == atout) or defense_purgee)
    v[33] = 1.0 if est_maitre_abs else 0.0

    return v


def encoder_encheres(encheres, joueur, atout):
    """Encode les enchères du point de vue du joueur (32 bits)."""
    v = np.zeros(32, dtype=np.float32)
    personne_avant = True
    for j, d in encheres:
        k = 8 * ((j - joueur) % 4)
        if isinstance(d, tuple):
            valeur, couleur = d
            if v[k] == 0:
                v[k] = 1.0                    # a annoncé
                v[k + 1] = valeur / 250.0     # première annonce
            v[k + 2] = valeur / 250.0         # dernière annonce
            v[k + 3] += 0.25                  # nombre d'annonces
            if couleur == atout:
                v[k + 4] = 1.0                # a annoncé l'atout
            else:
                v[k + 5] = 1.0                # a annoncé une autre couleur
            personne_avant = False
        elif d == "coinche":
            v[k + 6] = 1.0
        elif d == "passe" and personne_avant:
            v[k + 7] = 1.0                    # a passé d'entrée
    return v


def encoder_situation_v2(main, pli, historique, contrat, joueur, regles, encheres=None, belote_declaree=None):
    atout = contrat["atout"]
    ordre = ordre_couleurs(atout)
    autres = [(joueur + k) % 4 for k in (1, 2, 3)]      # gauche, partenaire, droite
    x = np.zeros(TAILLE_SITUATION_V2, dtype=np.float32)

    # 1. Ma main (32 bits : 0 à 31)
    for c in main:
        x[indice(c, ordre)] = 1.0

    # 2. Cartes jouées par les autres dans l'historique (96 bits : 32 à 127)
    for j, c in historique:
        if j != joueur:
            x[32 + 32 * autres.index(j) + indice(c, ordre)] = 1.0

    # 3. Pli en cours (96 bits : 128 à 223)
    for j, c in pli:
        if j != joueur:
            x[128 + 32 * autres.index(j) + indice(c, ordre)] = 1.0

    # 4. Couleurs manquantes / coupes avérées (12 bits : 224 à 235)
    manque = manques(historique, atout, regles)
    for k, j in enumerate(autres):
        for couleur in manque[j]:
            x[224 + 4 * k + ordre.index(couleur)] = 1.0

    # 5. Rôle, contrat, scores (13 bits : 236 à 248)
    eq = joueur % 2
    pts, plis = bilan_passe(historique, atout)

    if contrat["joueur"] == joueur:
        x[236] = 1.0
    elif contrat["joueur"] % 2 == eq:
        x[236] = 0.5
    else:
        x[236] = 0.0

    x[237] = contrat["valeur"] / 160.0
    x[238] = 1.0 if contrat["capot"] else 0.0
    x[239] = contrat["coinche"] / 2.0
    x[240] = pts[eq] / 162.0
    x[241] = pts[1 - eq] / 162.0
    x[242] = plis[eq] / 8.0
    x[243] = plis[1 - eq] / 8.0
    if pli and gagnant_pli(pli, atout)[0] == (joueur + 2) % 4:
        x[244] = 1.0
    x[245 + len(pli)] = 1.0

    # 6. Enchères (32 bits : 249 à 280)
    x[249:281] = encoder_encheres(encheres or [], joueur, atout)

    # =========================================================================
    # NOUVEAUX DESCRIPTEURS EXPERTS V2 (9 bits : 281 à 289)
    # =========================================================================
    # A. Atouts inconnus en circulation hors de ma main (1 float normalisé : case 281)
    atouts_vus_ou_en_main = sum(1 for _, c in historique if c[1] == atout) + \
                            sum(1 for _, c in pli if c[1] == atout) + \
                            sum(1 for c in main if c[1] == atout)
    atouts_inconnus = 8 - atouts_vus_ou_en_main
    x[281] = max(0.0, atouts_inconnus / 8.0)

    # B. Statut certain : La défense a-t-elle 0 atout garanti ? (1 bit : case 282)
    adv_gauche = (joueur + 1) % 4
    adv_droite = (joueur + 3) % 4

    # Déduction par défaut (coupes avérées ou zéro atout dehors)
    defense_sans_atout = (atout in manque[adv_gauche] and atout in manque[adv_droite]) or (atouts_inconnus == 0)

    # Déduction experte par la Belote annoncée :
    if belote_declaree is not None:
        j_bel, etape_bel = belote_declaree
        # etape == 1 : la 1ère carte (R ou D) a été posée, la 2ème est encore en main
        if etape_bel == 1:
            if j_bel % 2 == joueur % 2:
                # La Belote a été annoncée par notre camp (le partenaire) !
                # Le partenaire a donc obligatoirement la carte complémentaire en main.
                # Cette carte est comptée dans atouts_inconnus, mais elle n'est PAS chez l'adversaire.
                atouts_adverses_inconnus = atouts_inconnus - 1
                if atouts_adverses_inconnus <= 0:
                    defense_sans_atout = True
            else:
                # La Belote a été annoncée par un adversaire : il a obligatoirement un atout !
                defense_sans_atout = False

    defense_purgee_bool = bool(defense_sans_atout)
    x[282] = 1.0 if defense_purgee_bool else 0.0
    

    # C. Contexte précis du pli en cours (7 bits : cases 283 à 289)
    if pli:
        # Couleur demandée au premier coup du pli (4 bits : 283 à 286)
        coul_demandee = pli[0][1][1]
        x[283 + ordre.index(coul_demandee)] = 1.0

        # Pli actuellement tenu par mon camp ? (1 bit : case 287)
        gagnant_actuel, c_gag = gagnant_pli(pli, atout)
        pli_actuel_a_nous = (gagnant_actuel % 2 == eq)
        x[287] = 1.0 if pli_actuel_a_nous else 0.0

        # Pli GARANTI à notre camp ? (1 bit : case 288)
        # Garanti si :
        # - soit on joue en 4e position (len(pli) == 3) et la carte du partenaire mène
        # - soit la carte gagnante actuelle sur le tapis est un maître absolu
        cartes_connues = {c for _, c in historique} | {c for _, c in pli} | set(main)
        c_gag_est_maitre = not cartes_sont_vivantes_superieures(c_gag, atout, cartes_connues)
        c_gag_imparable = c_gag_est_maitre and ((c_gag[1] == atout) or defense_purgee_bool)

        garanti = (len(pli) == 3 and pli_actuel_a_nous) or (pli_actuel_a_nous and c_gag_imparable)
        x[288] = 1.0 if garanti else 0.0

        # Points en jeu sur le tapis (1 float : case 289)
        pts_pli = sum(points(c, atout) for _, c in pli)
        x[289] = min(1.0, pts_pli / 45.0)

    return x
