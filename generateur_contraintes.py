import random
from moteur import COULEURS, RANGS
from montecarlo import manques

def deduire_bornes_atout(p, encheres, atout, cartes_jouees_p, manque_p, place_libre_p):
    """Déduit le min et max d'atouts restant en main pour le joueur p."""
    if atout in manque_p or place_libre_p == 0:
        return 0, 0

    atouts_deja_joues = sum(1 for c in cartes_jouees_p if c[1] == atout)
    annonces_p = [(val, coul) for j, d in encheres if j == p and isinstance(d, tuple) for val, coul in [d]]
    a_ouvert_atout = any(coul == atout for _, coul in annonces_p[:1])
    max_annonce_atout = max([val for val, coul in annonces_p if coul == atout], default=0)
    
    min_atouts_init = 0
    max_atouts_init = 5

    if a_ouvert_atout:
        if max_annonce_atout >= 120: min_atouts_init, max_atouts_init = 5, 7
        elif max_annonce_atout >= 110: min_atouts_init, max_atouts_init = 4, 6
        else: min_atouts_init, max_atouts_init = 3, 5
    elif any(coul == atout for _, coul in annonces_p):
        min_atouts_init, max_atouts_init = 2, 4
    elif any(d == "passe" for j, d in encheres if j == p and encheres.index((j, d)) < 4):
        min_atouts_init, max_atouts_init = 0, 3

    # Bornes strictement limitées par les cartes restantes en main
    min_restant = max(0, min(min_atouts_init - atouts_deja_joues, place_libre_p))
    max_restant = max(0, min(max_atouts_init - atouts_deja_joues, place_libre_p))
    if min_restant > max_restant:
        min_restant = max_restant
    return min_restant, max_restant

def partitions_possibles(joueurs, bornes, places_libres, total_atouts):
    solutions = []
    j0, j1, j2 = joueurs
    for n0 in range(bornes[j0][0], min(bornes[j0][1], places_libres[j0]) + 1):
        for n1 in range(bornes[j1][0], min(bornes[j1][1], places_libres[j1]) + 1):
            n2 = total_atouts - n0 - n1
            if bornes[j2][0] <= n2 <= min(bornes[j2][1], places_libres[j2]):
                solutions.append({j0: n0, j1: n1, j2: n2})
    return solutions

def imaginer_donnes_contraintes(main_joueur, joueur, historique, encheres, atout, regles):
    autres = [(joueur + k) % 4 for k in (1, 2, 3)]
    manque = manques(historique, atout, regles)
    cartes_jouees = {p: [c for j, c in historique if j == p] for p in autres}
    places_libres = {p: 8 - len(cartes_jouees[p]) for p in autres}
    
    toutes_vues = set(main_joueur) | {c for _, c in historique}
    inconnues = [(r, c) for c in COULEURS for r in RANGS if (r, c) not in toutes_vues]
    
    # Sécurité absolue : si le nombre de cartes inconnues ne colle pas
    total_places = sum(places_libres.values())
    if len(inconnues) != total_places:
        # Fallback de secours basique
        random.shuffle(inconnues)
        m = {joueur: list(main_joueur)}
        cur = 0
        for p in autres:
            m[p] = inconnues[cur:cur + places_libres[p]]
            cur += places_libres[p]
        return [m[i] for i in range(4)]

    atouts_inconnus = [c for c in inconnues if c[1] == atout]
    hors_atout_inconnus = [c for c in inconnues if c[1] != atout]
    total_atouts = len(atouts_inconnus)
    
    # 1. Bornes d'atouts réalistes pour chaque joueur
    bornes = {}
    for p in autres:
        bornes[p] = deduire_bornes_atout(p, encheres, atout, cartes_jouees[p], manque[p], places_libres[p])

    # 2. Partitions valides
    soluces = partitions_possibles(autres, bornes, places_libres, total_atouts)
    
    if not soluces:
        # Relâcher les contraintes min en gardant les places libres
        bornes_souples = {p: (0, min(places_libres[p], total_atouts)) for p in autres}
        soluces = partitions_possibles(autres, bornes_souples, places_libres, total_atouts)

    if not soluces:
        # Répartition équitable des atouts selon les places libres
        repart_atouts = {p: 0 for p in autres}
        rest = total_atouts
        for p in sorted(autres, key=lambda x: places_libres[x], reverse=True):
            donne = min(rest, places_libres[p])
            repart_atouts[p] = donne
            rest -= donne
    else:
        repart_atouts = random.choice(soluces)

    # 3. Distribution des atouts
    random.shuffle(atouts_inconnus)
    mains = {joueur: list(main_joueur)}
    for p in autres:
        mains[p] = []
    
    cur_at = 0
    for p in autres:
        n_at = repart_atouts[p]
        mains[p].extend(atouts_inconnus[cur_at:cur_at + n_at])
        cur_at += n_at

    # 4. Couleurs secondaires ouvertes aux enchères
    couleurs_ouvertes = {}
    for p in autres:
        for val, coul in [(d[0], d[1]) for j, d in encheres if j == p and isinstance(d, tuple)]:
            if coul != atout and coul not in couleurs_ouvertes:
                couleurs_ouvertes[coul] = p

    for coul_sec, p_ouvreur in couleurs_ouvertes.items():
        cartes_coul = [c for c in hors_atout_inconnus if c[1] == coul_sec]
        deja_jouees = sum(1 for c in cartes_jouees[p_ouvreur] if c[1] == coul_sec)
        besoin = max(0, 3 - deja_jouees)
        dispo = places_libres[p_ouvreur] - len(mains[p_ouvreur])
        nb_donne = min(len(cartes_coul), besoin, dispo)
        
        if nb_donne > 0:
            random.shuffle(cartes_coul)
            cartes_donnees = cartes_coul[:nb_donne]
            mains[p_ouvreur].extend(cartes_donnees)
            for c in cartes_donnees:
                hors_atout_inconnus.remove(c)

    # 5. Distribution des cartes restantes pour remplir EXACTEMENT chaque main
    random.shuffle(hors_atout_inconnus)
    for c in hors_atout_inconnus:
        receveurs = [p for p in autres if c[1] not in manque[p] and len(mains[p]) < places_libres[p]]
        if not receveurs:
            receveurs = [p for p in autres if len(mains[p]) < places_libres[p]]
        p_choisi = random.choice(receveurs)
        mains[p_choisi].append(c)

    return [mains[i] for i in range(4)]
