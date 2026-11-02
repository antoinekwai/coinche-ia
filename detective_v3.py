"""
detective_v3.py
Détective « Système v2 » : une donne imaginée est gardée si, en rejouant les enchères
avec les mains imaginées, on retrouve les vraies enchères.
"""
import random
from regles import REGLES_STANDARD
from moteur import COULEURS, RANGS, distribuer
from partie import phase_annonces
from ia_joueur import JoueurIA
from detective_v2 import coherente

STATS_V3 = {"appels": 0, "parfaites": 0, "approchees": 0}


def tirage_naif(main_joueur, joueur, historique):
    """Cartes inconnues distribuées au hasard (on vérifie la cohérence après)."""
    vues = set(main_joueur) | {c for _, c in historique}
    inconnues = [(r, c) for c in COULEURS for r in RANGS if (r, c) not in vues]
    random.shuffle(inconnues)
    mains = [None] * 4
    mains[joueur] = list(main_joueur)
    cur = 0
    for k in (1, 2, 3):
        p = (joueur + k) % 4
        n = 8 - sum(1 for j, _ in historique if j == p)
        mains[p] = inconnues[cur:cur + n]
        cur += n
    return mains


def rejouer_encheres(mains_depart, donneur, regles):
    """Rejoue la phase d'enchères avec ces mains et renvoie la liste des enchères."""
    joueurs = [JoueurIA() for _ in range(4)]
    phase_annonces([list(m) for m in mains_depart], donneur, joueurs, regles, afficher=False)
    return list(joueurs[(donneur + 1) % 4].encheres)


def nb_differences(vraies, rejouees):
    """Nombre de décisions différentes entre deux séquences d'enchères."""
    diff = sum(1 for a, b in zip(vraies, rejouees) if a != b)
    return diff + abs(len(vraies) - len(rejouees))


def imaginer_v3(main, joueur, historique, encheres, atout, regles,
                tolerance=0.1, max_essais=300):
    STATS_V3["appels"] += 1
    if not encheres:
        tolerance = 1.0                      # pas d'enchères connues : on ne filtre que le jeu
    donneur = (encheres[0][0] - 1) % 4 if encheres else 0
    meilleure, meilleur_diff = None, 999
    for _ in range(max_essais):
        imag = tirage_naif(main, joueur, historique)
        if not coherente(imag, historique, atout, regles):
            continue                         # contredit les cartes jouées : rejetée
        depart = [list(m) for m in imag]
        for j, c in historique:
            depart[j].append(c)
        d = nb_differences(encheres, rejouer_encheres(depart, donneur, regles)) if encheres else 0
        if d < meilleur_diff:
            meilleure, meilleur_diff = imag, d
        if random.random() < tolerance ** d:
            STATS_V3["parfaites" if d == 0 else "approchees"] += 1
            return imag
    return meilleure if meilleure is not None else imag   # secours : la plus proche trouvée


if __name__ == "__main__":
    # Vérification : les enchères sont-elles bien déterministes ?
    regles = REGLES_STANDARD
    identiques = 0
    for g in range(50):
        random.seed(g)
        mains = distribuer()
        random.seed(10_000 + g); e1 = rejouer_encheres(mains, g % 4, regles)
        random.seed(20_000 + g); e2 = rejouer_encheres(mains, g % 4, regles)
        identiques += (e1 == e2)
    print(f"Enchères identiques en rejouant : {identiques}/50 (il faut 50/50)")
