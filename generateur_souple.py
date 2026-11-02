import random
from collections import defaultdict
from moteur import COULEURS, RANGS
from montecarlo import manques

def calculer_poids_joueurs(autres, encheres, couleur, atout, manque, places_libres):
    """
    Calcule la probabilité relative (poids) de chaque joueur pour recevoir une carte de cette couleur.
    """
    poids = {}
    for p in autres:
        # S'il a déjà montré qu'il n'avait plus de cette couleur, ou s'il n'a plus de place en main
        if couleur in manque[p] or places_libres[p] <= 0:
            poids[p] = 0.0
            continue

        annonces_p = [(val, coul) for j, d in encheres if j == p and isinstance(d, tuple) for val, coul in [d]]
        base_poids = 1.0

        if couleur == atout:
            # Poids d'attraction pour l'atout selon les enchères
            a_ouvert_atout = any(coul == atout for _, coul in annonces_p[:1])
            max_atout = max([val for val, coul in annonces_p if coul == atout], default=0)
            
            if a_ouvert_atout:
                if max_atout >= 120: base_poids = 3.5
                elif max_atout >= 110: base_poids = 2.8
                else: base_poids = 2.2
            elif any(coul == atout for _, coul in annonces_p):
                base_poids = 1.8 # A soutenu à l'atout
            elif any(d == "passe" for j, d in encheres if j == p and encheres.index((j, d)) < 4):
                base_poids = 0.6 # A passé d'entrée
        else:
            # Poids pour une couleur hors-atout
            a_ouvert_coul = any(coul == couleur for _, coul in annonces_p[:1])
            if a_ouvert_coul:
                base_poids = 2.5 # A ouvert cette couleur hors-atout
            # Si le preneur a pris très haut à l'atout, ses places hors-atout sont rares -> poids réduit
            preneur_gros_atout = any(coul == atout and val >= 110 for val, coul in annonces_p)
            if preneur_gros_atout:
                base_poids = 0.7

        # Moduler par le nombre de places libres restantes
        poids[p] = base_poids * (places_libres[p] ** 1.2)

    return poids

def imaginer_donnes_souples(main_joueur, joueur, historique, encheres, atout, regles):
    autres = [(joueur + k) % 4 for k in (1, 2, 3)]
    manque = manques(historique, atout, regles)
    cartes_jouees = {p: [c for j, c in historique if j == p] for p in autres}
    places_libres = {p: 8 - len(cartes_jouees[p]) for p in autres}
    
    toutes_vues = set(main_joueur) | {c for _, c in historique}
    inconnues = [(r, c) for c in COULEURS for r in RANGS if (r, c) not in toutes_vues]
    
    # Séparer atouts et autres couleurs
    atouts = [c for c in inconnues if c[1] == atout]
    autres_cartes = [c for c in inconnues if c[1] != atout]
    
    mains = {joueur: list(main_joueur)}
    for p in autres:
        mains[p] = []
        
    # 1. Distribuer les atouts avec pondération souple
    random.shuffle(atouts)
    for c in atouts:
        poids = calculer_poids_joueurs(autres, encheres, atout, atout, manque, places_libres)
        total_p = sum(poids.values())
        if total_p <= 0:
            # Secours : n'importe qui ayant de la place
            candidats = [p for p in autres if places_libres[p] > 0]
        else:
            candidats = autres
            w = [poids[p] for p in autres]
            p_choisi = random.choices(candidats, weights=w)[0]
            
        mains[p_choisi].append(c)
        places_libres[p_choisi] -= 1

    # 2. Distribuer les couleurs secondaires ouvertes aux enchères
    couleurs_secondaires = set()
    for p in autres:
        for val, coul in [(d[0], d[1]) for j, d in encheres if j == p and isinstance(d, tuple)]:
            if coul != atout:
                couleurs_secondaires.add(coul)

    cartes_secondaires = [c for c in autres_cartes if c[1] in couleurs_secondaires]
    cartes_restantes = [c for c in autres_cartes if c[1] not in couleurs_secondaires]

    random.shuffle(cartes_secondaires)
    for c in cartes_secondaires:
        poids = calculer_poids_joueurs(autres, encheres, c[1], atout, manque, places_libres)
        total_p = sum(poids.values())
        if total_p <= 0:
            candidats = [p for p in autres if places_libres[p] > 0]
            p_choisi = random.choice(candidats)
        else:
            p_choisi = random.choices(autres, weights=[poids[p] for p in autres])[0]
            
        mains[p_choisi].append(c)
        places_libres[p_choisi] -= 1

    # 3. Distribuer le reste
    random.shuffle(cartes_restantes)
    for c in cartes_restantes:
        poids = calculer_poids_joueurs(autres, encheres, c[1], atout, manque, places_libres)
        total_p = sum(poids.values())
        if total_p <= 0:
            candidats = [p for p in autres if places_libres[p] > 0]
            p_choisi = random.choice(candidats)
        else:
            p_choisi = random.choices(autres, weights=[poids[p] for p in autres])[0]
            
        mains[p_choisi].append(c)
        places_libres[p_choisi] -= 1

    return [mains[i] for i in range(4)]
