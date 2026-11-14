"""
detective_v5.py (Version 5.1 Réparée & Assouplie)
Corrections scientifiques clés :
1. Suppression du bug de sur-allocation d'atouts au Pli 4 (la présence du V ou du 9
   prend en compte les cartes déjà jouées par le preneur lui-même !).
2. Assouplissement à 80-90 : réserve 1 seul honneur (V ou 9 au sort) au lieu des deux,
   laissant la défense espérer un honneur chez le partenaire.
3. Reste du pot distribué avec respect strict des coupes avérées.
"""
import random
from moteur import COULEURS, RANGS
from montecarlo import manques
from detective_v2 import coherente
from detective_v3 import rejouer_encheres, nb_differences

STATS_V5 = {"appels": 0, "essais_totaux": 0, "parfaites": 0, "secours": 0}


def trouver_preneur_atout(encheres, atout):
    """Retrouve le premier déclarant de l'atout dans le camp ayant l'enchère la plus haute."""
    max_val = 0
    camp_preneur = None
    for j, d in encheres:
        if isinstance(d, tuple) and d[1] == atout and d[0] > max_val:
            max_val = d[0]
            camp_preneur = j % 2

    if camp_preneur is None:
        return None, 0

    for j, d in encheres:
        if isinstance(d, tuple) and d[1] == atout and (j % 2 == camp_preneur):
            return j, d[0]

    return None, 0


def tirage_guide_v5(main_joueur, joueur, historique, encheres, atout, regles):
    """Distribue les cartes inconnues avec guidage assoupli et réaliste."""
    cartes_vues = set(main_joueur) | {c for _, c in historique}
    inconnues = [(r, c) for c in COULEURS for r in RANGS if (r, c) not in cartes_vues]

    # Nombre de cartes à donner à chaque joueur
    nb_a_donner = {}
    for k in (1, 2, 3):
        p = (joueur + k) % 4
        nb_a_donner[p] = 8 - sum(1 for j_h, _ in historique if j_h == p)

    coupes = manques(historique, atout, regles)
    autres_joueurs = [p for p in nb_a_donner if nb_a_donner[p] > 0]

    mains = [None] * 4
    mains[joueur] = list(main_joueur)
    for p in autres_joueurs:
        mains[p] = []

    preneur, valeur_atout = trouver_preneur_atout(encheres, atout)

    atouts_dispos = [c for c in inconnues if c[1] == atout]
    autres_dispos = [c for c in inconnues if c[1] != atout]
    random.shuffle(atouts_dispos)

    # 1. RÉSERVATION DES ATOUTS DU PRENEUR
    if preneur is not None and preneur != joueur and preneur in autres_joueurs:
        if atout not in coupes[preneur]:
            # Cible de base réaliste
            if valeur_atout >= 120:
                cible_depart = 4
            elif valeur_atout >= 100:
                cible_depart = 3
            else:
                cible_depart = 2  # 80-90 : preneur peut avoir seulement 2 ou 3 atouts

            # Déduction exacte des atouts que le preneur a DÉJÀ posés sur la table
            atouts_deja_joues_par_preneur = sum(
                1 for j_h, c_h in historique if j_h == preneur and c_h[1] == atout
            )

            # Cartes d'honneurs connues de l'observateur (en main ou jouées par autrui)
            honneurs_vus_hors_preneur = {
                c[0] for _, c in historique if c[1] == atout and _ != preneur
            } | {c[0] for c in main_joueur if c[1] == atout}

            # Si l'observateur a vu le V ET le 9 HORS du preneur :
            # le preneur n'avait aucun honneur majeur -> il a ouvert sur la longueur !
            if "V" in honneurs_vus_hors_preneur and "9" in honneurs_vus_hors_preneur:
                cible_depart = max(cible_depart, 4)

            cible_restante = max(0, cible_depart - atouts_deja_joues_par_preneur)
            n_reserve = min(cible_restante, len(atouts_dispos), nb_a_donner[preneur])

            atouts_p = []

            # Choix des honneurs réservés selon le palier :
            if valeur_atout >= 100:
                # Contrats 100+ : Valet et 9 prioritaires
                honneurs_cibles = ["V", "9"]
            else:
                # Contrats 80-90 : un seul honneur prioritaire tiré au sort (souplesse)
                honneurs_cibles = [random.choice(["V", "9"])]

            for h in honneurs_cibles:
                if (h, atout) in atouts_dispos and len(atouts_p) < n_reserve:
                    atouts_dispos.remove((h, atout))
                    atouts_p.append((h, atout))

            # Compléter la réserve d'atouts avec les atouts disponibles au hasard
            while len(atouts_p) < n_reserve and atouts_dispos:
                atouts_p.append(atouts_dispos.pop())

            mains[preneur].extend(atouts_p)
            nb_a_donner[preneur] -= len(atouts_p)

    # 2. TOUT LE RESTE DISTRIBUÉ AU HASARD
    pot_restant = atouts_dispos + autres_dispos
    random.shuffle(pot_restant)

    curseur = 0
    for p in autres_joueurs:
        besoin = nb_a_donner[p]
        if besoin > 0:
            mains[p].extend(pot_restant[curseur : curseur + besoin])
            curseur += besoin

    return mains


def imaginer_v5(main, joueur, historique, encheres, atout, regles,
                tolerance=0.1, max_essais=150):
    """Détective v5.1 : Tirage guidé assoupli + rejeu des enchères."""
    STATS_V5["appels"] += 1
    donneur = (encheres[0][0] - 1) % 4 if encheres else 0
    meilleure, meilleur_diff = None, 999

    for essai in range(1, max_essais + 1):
        STATS_V5["essais_totaux"] += 1
        imag = tirage_guide_v5(main, joueur, historique, encheres, atout, regles)

        if not coherente(imag, historique, atout, regles):
            continue

        if not encheres:
            STATS_V5["parfaites"] += 1
            return imag

        depart = [list(m) for m in imag]
        for j, c in historique:
            depart[j].append(c)

        d = nb_differences(encheres, rejouer_encheres(depart, donneur, regles))
        if d < meilleur_diff:
            meilleure, meilleur_diff = imag, d

        if d == 0:
            STATS_V5["parfaites"] += 1
            return imag
        elif random.random() < (tolerance ** d):
            return imag

    STATS_V5["secours"] += 1
    return meilleure if meilleure is not None else imag
