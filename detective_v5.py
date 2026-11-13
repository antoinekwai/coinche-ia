"""
detective_v5.py (Version Épurée : Guidage Atout Seul)
Principe strict : UNE SEULE VARIABLE.
1. Réservation des atouts du preneur selon son annonce (avec Valet/9 en priorité si dispos).
2. Déduction exacte des atouts déjà posés sur la table aux plis passés.
3. TOUT LE RESTE (y compris les As) est mélangé dans le pot commun et distribué au hasard pur.
4. Validation par rejeu des enchères.
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
            return j, d[0]  # Sa première annonce personnelle dans la couleur !

    return None, 0


def tirage_guide_v5(main_joueur, joueur, historique, encheres, atout, regles):
    """Distribue les cartes inconnues : réservation d'atouts au preneur, reste 100% aléatoire."""
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

    # 1. RÉSERVATION DES ATOUTS DU PRENEUR (avec déduction des plis passés)
    if preneur is not None and preneur != joueur and preneur in autres_joueurs:
        if atout not in coupes[preneur]:
            if valeur_atout >= 130:
                cible_depart = 4
            elif valeur_atout >= 110:
                cible_depart = 3
            else:
                cible_depart = 2

            # COMPENSATION PAR LA LONGUEUR :
            # Si le Valet ET le 9 sont déjà vus (ex: dans ma main de défenseur),
            # le preneur a nécessairement ouvert avec une couleur 5e ou 6e !
            v_ou_9_dispo = any(h in ("V", "9") for h, c in atouts_dispos)
            if not v_ou_9_dispo:
                cible_depart += 2  # Un preneur sans V ni 9 a au moins 4 ou 5 atouts !
            atouts_deja_joues = sum(1 for j_h, c_h in historique if j_h == preneur and c_h[1] == atout)
            cible_restante = max(0, cible_depart - atouts_deja_joues)

            n_reserve = min(cible_restante, len(atouts_dispos), nb_a_donner[preneur])

            atouts_p = []
            for h in ("V", "9"):
                if (h, atout) in atouts_dispos and len(atouts_p) < n_reserve:
                    atouts_dispos.remove((h, atout))
                    atouts_p.append((h, atout))

            while len(atouts_p) < n_reserve and atouts_dispos:
                atouts_p.append(atouts_dispos.pop())

            mains[preneur].extend(atouts_p)
            nb_a_donner[preneur] -= len(atouts_p)

    # 2. TOUT LE RESTE AU HASARD PUR (les As sont dans autres_dispos, traités comme n'importe quelle carte)
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
    """Détective v5 : Tirage guidé par les atouts seuls + rejeu des enchères."""
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
