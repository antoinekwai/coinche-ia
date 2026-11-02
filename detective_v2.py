"""
detective_v2.py
Détective avec filtre : on jette les donnes imaginées qui contredisent le jeu.
Le juge est le moteur lui-même (cartes_jouables) : toutes les règles sont respectées
(fournir, couper, monter à l'atout, sous-couper).
"""
from moteur import cartes_jouables
from generateur_contraintes import imaginer_donnes_contraintes

STATS = {"appels": 0, "echecs": 0}


def coherente(imag, historique, atout, regles):
    """True si la donne imaginée est possible, d'après les cartes déjà jouées."""
    # 1. Chaque joueur doit avoir le bon nombre de cartes
    for p in range(4):
        if len(imag[p]) != 8 - sum(1 for j, _ in historique if j == p):
            return False
    # 2. Reconstituer les mains de départ
    mains = [list(m) for m in imag]
    for j, c in historique:
        mains[j].append(c)
    # 3. Rejouer l'historique : chaque carte jouée devait être autorisée
    for debut in range(0, len(historique), 4):
        pli = []
        for j, c in historique[debut:debut + 4]:
            if c not in cartes_jouables(mains[j], pli, atout, j, regles):
                return False
            mains[j].remove(c)
            pli.append((j, c))
    return True


def imaginer_filtre(main, joueur, historique, encheres, atout, regles, max_essais=50):
    """Comme imaginer_donnes_contraintes, mais recommence si la donne est impossible."""
    STATS["appels"] += 1
    imag = None
    for _ in range(max_essais):
        imag = imaginer_donnes_contraintes(main, joueur, historique, encheres, atout, regles)
        if coherente(imag, historique, atout, regles):
            return imag
    STATS["echecs"] += 1      # aucun essai valable : on garde le dernier (rare)
    return imag
