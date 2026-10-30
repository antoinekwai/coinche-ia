import time
import numpy as np
from moteur import COULEURS, RANGS, gagnant_pli, distribuer
from montecarlo import manques, bilan_passe

TAILLE_ENCHERES = 4 * 8
TAILLE_SITUATION = 32 + 3 * 32 + 3 * 32 + 3 * 4 + 13 + TAILLE_ENCHERES   # 281

TAILLE_CARTE = 32


def ordre_couleurs(atout):
    """L'atout d'abord, puis les 3 autres couleurs."""
    return [atout] + [c for c in COULEURS if c != atout]


def indice(carte, ordre):
    rang, couleur = carte
    return 8 * ordre.index(couleur) + RANGS.index(rang)


def encoder_carte(carte, atout):
    v = np.zeros(TAILLE_CARTE, dtype=np.float32)
    v[indice(carte, ordre_couleurs(atout))] = 1.0
    return v

def encoder_encheres(encheres, joueur, atout):
    """8 nombres par joueur : moi, gauche, partenaire, droite."""
    v = np.zeros(TAILLE_ENCHERES, dtype=np.float32)
    personne_avant = True
    for j, d in encheres:
        k = 8 * ((j - joueur) % 4)
        if isinstance(d, tuple):
            valeur, couleur = d
            if v[k] == 0:
                v[k] = 1.0                    # a annoncé
                v[k + 1] = valeur / 250       # première annonce
            v[k + 2] = valeur / 250           # dernière annonce
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

def encoder_situation(main, pli, historique, contrat, joueur, regles, encheres=None):

    atout = contrat["atout"]
    ordre = ordre_couleurs(atout)
    autres = [(joueur + k) % 4 for k in (1, 2, 3)]      # gauche, partenaire, droite
    x = np.zeros(TAILLE_SITUATION, dtype=np.float32)

    for c in main:                                       # ma main
        x[indice(c, ordre)] = 1.0
    for j, c in historique:                              # cartes jouées par les autres
        if j != joueur:
            x[32 + 32 * autres.index(j) + indice(c, ordre)] = 1.0
    for j, c in pli:                                     # pli en cours
        if j != joueur:
            x[128 + 32 * autres.index(j) + indice(c, ordre)] = 1.0
    manque = manques(historique, atout, regles)          # couleurs manquantes
    for k, j in enumerate(autres):
        for couleur in manque[j]:
            x[224 + 4 * k + ordre.index(couleur)] = 1.0

    eq = joueur % 2                                      # contexte
    pts, plis = bilan_passe(historique, atout)
    x[236] = 1.0 if contrat["joueur"] % 2 == eq else 0.0
    x[237] = contrat["valeur"] / 160
    x[238] = 1.0 if contrat["capot"] else 0.0
    x[239] = contrat["coinche"] / 2
    x[240] = pts[eq] / 162
    x[241] = pts[1 - eq] / 162
    x[242] = plis[eq] / 8
    x[243] = plis[1 - eq] / 8
    if pli and gagnant_pli(pli, atout)[0] == (joueur + 2) % 4:
        x[244] = 1.0
    x[245 + len(pli)] = 1.0                              # rang dans le pli (0 à 3)
    x[249:] = encoder_encheres(encheres or [], joueur, atout)

    return x


if __name__ == "__main__":
    from regles import REGLES_STANDARD
    from joueurs import JoueurRegles
    from partie import jouer_donne

    erreurs, nb, avec_encheres, duree = 0, 0, 0, 0.0

    class Espion(JoueurRegles):
        historique = []
        encheres = []

        def jouer_carte(self, main, jouables, pli, contrat, joueur, regles):
            global erreurs, nb, avec_encheres, duree
            t = time.time()
            x = encoder_situation(main, pli, self.historique, contrat, joueur, regles, self.encheres)
            duree += time.time() - t
            nb += 1
            vus = sum(1 for j, _ in self.historique if j != joueur)
            if x[:32].sum() != len(main) or x[32:128].sum() != vus or x.shape != (TAILLE_SITUATION,):
                erreurs += 1
            if x[249:].sum() > 0:
                avec_encheres += 1
            return super().jouer_carte(main, jouables, pli, contrat, joueur, regles)

    donnes, i = 0, 0
    while donnes < 200:
        if jouer_donne(i % 4, [Espion() for _ in range(4)], REGLES_STANDARD) is not None:
            donnes += 1
        i += 1

    print(f"Taille d'une situation : {TAILLE_SITUATION} + carte candidate {TAILLE_CARTE} "
          f"= {TAILLE_SITUATION + TAILLE_CARTE} nombres")
    print(f"{nb} situations encodées, {erreurs} incohérence(s), "
          f"{avec_encheres} avec des enchères encodées")
    print(f"Temps moyen par situation : {1e6 * duree / nb:.0f} microsecondes")
