"""
detective_v4_1.py (Architecture Unifiée)
Détective v4 assaini :
1. Utilise directement JoueurIA pour juger la plausibilité des cartes jouées :
   toutes les conventions et règles d'arbitrage de l'IA (As-10, etc.) sont
   automatiquement appliquées par le détective !
2. Repli de sécurité garanti sur imaginer_v3 en cas de dépassement (ZÉRO tirage naïf)
3. Mesure précise du taux d'acceptation
"""
import random
from moteur import cartes_jouables
from ia_joueur import JoueurIA
from detective_v2 import coherente
from detective_v3 import tirage_naif, rejouer_encheres, nb_differences, imaginer_v3

PLANCHER = 0.10        # Une main n'est jamais totalement exclue (bluff, écart)
STATS_V4_1 = {"appels": 0, "succes_v4": 0, "replis_v3": 0}

# Instance singleton pour éviter de réinstancier l'IA à chaque boucle
_IA_ARBITRE = JoueurIA()


def moments_a_lire(historique, joueur, atout):
    """Identifie les moments riches en information : entame et 1res défausses."""
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


def vraisemblance_avec_ia(imag, historique, i, contrat, encheres, regles):
    """Demande à JoueurIA si la carte réellement jouée correspond à son choix."""
    j, carte_reelle = historique[i]
    # Reconstituer la main du joueur j à l'instant du pli i
    main_moment = list(imag[j]) + [c for k, (p, c) in enumerate(historique) if p == j and k >= i]
    pli_moment = list(historique[i - i % 4:i])
    atout = contrat["atout"]
    jouables = cartes_jouables(main_moment, pli_moment, atout, j, regles)

    if len(jouables) <= 1 or carte_reelle not in jouables:
        return 1.0

    # Interroger JoueurIA avec son contexte exact
    _IA_ARBITRE.historique = list(historique[:i])
    _IA_ARBITRE.encheres = list(encheres) if encheres else []
    
    carte_attendue = _IA_ARBITRE.jouer_carte(main_moment, jouables, pli_moment, contrat, j, regles)

    # Si le joueur a joué exactement la carte attendue par l'IA : cohérence totale !
    if carte_reelle == carte_attendue:
        return 1.0

    # Sinon, la main imaginée n'explique pas le coup joué -> pénalité
    return PLANCHER


def imaginer_v4_1(main, joueur, historique, encheres, atout, regles, contrat,
                  tolerance=0.1, max_essais=150):
    STATS_V4_1["appels"] += 1
    donneur = (encheres[0][0] - 1) % 4 if encheres else 0
    moments = moments_a_lire(historique, joueur, atout)

    # Si aucun pli informatif n'est encore joué, le v3 suffit
    if not moments:
        STATS_V4_1["succes_v4"] += 1
        return imaginer_v3(main, joueur, historique, encheres, atout, regles)

    meilleure, meilleur_poids = None, -1.0
    for _ in range(max_essais):
        imag = tirage_naif(main, joueur, historique)
        if not coherente(imag, historique, atout, regles):
            continue

        depart = [list(m) for m in imag]
        for j, c in historique:
            depart[j].append(c)

        d = nb_differences(encheres, rejouer_encheres(depart, donneur, regles)) if encheres else 0
        poids_encheres = tolerance ** d
        if random.random() >= poids_encheres:
            if poids_encheres > meilleur_poids:
                meilleure, meilleur_poids = imag, poids_encheres
            continue

        # 2e filtre : Vérification directe par JoueurIA
        lu = 1.0
        for i in moments:
            lu *= vraisemblance_avec_ia(imag, historique, i, contrat, encheres, regles)

        if random.random() < lu:
            STATS_V4_1["succes_v4"] += 1
            return imag

        if poids_encheres * lu > meilleur_poids:
            meilleure, meilleur_poids = imag, poids_encheres * lu

    # Si max_essais atteint : REPLI SÉCURISÉ SUR IMAGINER_V3 (ZÉRO TIRAGE NAÏF !)
    STATS_V4_1["replis_v3"] += 1
    if meilleure is not None:
        return meilleure
    return imaginer_v3(main, joueur, historique, encheres, atout, regles)
