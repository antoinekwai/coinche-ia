import random

COULEURS = ["♠", "♥", "♦", "♣"]
RANGS = ["7", "8", "9", "10", "V", "D", "R", "A"]

ORDRE_ATOUT     = {"7": 0, "8": 1, "D": 2, "R": 3, "10": 4, "A": 5, "9": 6, "V": 7}
ORDRE_NON_ATOUT = {"7": 0, "8": 1, "9": 2, "V": 3, "D": 4, "R": 5, "10": 6, "A": 7}
POINTS_ATOUT     = {"7": 0, "8": 0, "D": 3, "R": 4, "10": 10, "A": 11, "9": 14, "V": 20}
POINTS_NON_ATOUT = {"7": 0, "8": 0, "9": 0, "V": 2, "D": 3, "R": 4, "10": 10, "A": 11}


def distribuer():
    paquet = [(r, c) for c in COULEURS for r in RANGS]
    random.shuffle(paquet)
    return [paquet[0:8], paquet[8:16], paquet[16:24], paquet[24:32]]


def points(carte, atout):
    rang, couleur = carte
    return POINTS_ATOUT[rang] if couleur == atout else POINTS_NON_ATOUT[rang]


def texte_main(main):
    return " ".join(r + c for (r, c) in main)


def force(carte, atout, couleur_demandee):
    rang, couleur = carte
    if couleur == atout:
        return 100 + ORDRE_ATOUT[rang]
    if couleur == couleur_demandee:
        return ORDRE_NON_ATOUT[rang]
    return -1


def gagnant_pli(pli, atout):
    couleur_demandee = pli[0][1][1]
    return max(pli, key=lambda jc: force(jc[1], atout, couleur_demandee))


def cartes_jouables(main, pli, atout, joueur, regles):
    if not pli:
        return main[:]
    couleur_demandee = pli[0][1][1]
    partenaire_maitre = gagnant_pli(pli, atout)[0] == (joueur + 2) % 4

    atouts_main = [c for c in main if c[1] == atout]
    meme_couleur = [c for c in main if c[1] == couleur_demandee]
    plus_fort_pli = max([ORDRE_ATOUT[c[0]] for (j, c) in pli if c[1] == atout], default=-1)
    atouts_plus_forts = [c for c in atouts_main if ORDRE_ATOUT[c[0]] > plus_fort_pli]

    if couleur_demandee == atout:
        doit_monter = regles["monter_si_partenaire_maitre"] or not partenaire_maitre
        if doit_monter and atouts_plus_forts:
            return atouts_plus_forts
        return atouts_main or main[:]

    if meme_couleur:
        return meme_couleur
    if partenaire_maitre and not regles["couper_si_partenaire_maitre"]:
        return main[:]
    return atouts_plus_forts or atouts_main or main[:]


def equipe_belote(mains, atout):
    for joueur in range(4):
        if ("R", atout) in mains[joueur] and ("D", atout) in mains[joueur]:
            return joueur % 2
    return None

def arrondir_points_ffb(points_attaque, points_defense, der_attaque):
    """
    Arrondi officiel FFB à la dizaine la plus proche sur un total de 162 points.
    La somme finale des deux camps arrondis vaut TOUJOURS exactement 160.
    En cas de terminaison par 5, le camp ayant fait le Dix de Der bénéficie de l'arrondi supérieur.
    """
    u_att = points_attaque % 10
    
    if u_att in (1, 2, 3, 4):
        att_arrondi = (points_attaque // 10) * 10
    elif u_att in (6, 7, 8, 9):
        att_arrondi = ((points_attaque // 10) + 1) * 10
    else:  # se termine par 5
        att_arrondi = ((points_attaque // 10) + 1) * 10 if der_attaque else (points_attaque // 10) * 10
        
    def_arrondi = 160 - att_arrondi
    return att_arrondi, def_arrondi


def decompte(contrat, points_cartes, plis, belote, regles):
    attaque = contrat["joueur"] % 2
    defense = 1 - attaque
    multi = [1, regles["multi_coinche"], regles["multi_surcoinche"]][contrat["coinche"]]
    capot_realise = plis[attaque] == 8

    if contrat["capot"]:
        reussi = capot_realise
    else:
        pts = points_cartes[attaque]
        if belote == attaque and regles["belote_pour_contrat"]:
            pts += regles["points_belote"]
        reussi = pts >= contrat["valeur"]

    valeur = contrat["valeur"]
    if not contrat["capot"] and capot_realise and regles["capot_non_annonce"]:
        valeur = max(valeur, regles["valeur_capot"])

    scores = [0, 0]

    # MODE 1 : BARÈME STANDARD ("Contrat sec / Tout ou rien")
    if regles.get("mode_score") == "contrat":
        valeur_totale = valeur * multi
        if reussi:
            scores[attaque] += valeur_totale
        else:
            chute = regles.get("valeur_chute")
            if chute is not None and not contrat["capot"]:
                scores[defense] += max(chute, contrat["valeur"]) * multi
            else:
                scores[defense] += valeur_totale
        if belote is not None and regles.get("belote_au_score"):
            scores[belote] += regles["points_belote"]

    # MODE 2 : BARÈME OFFICIEL FFB ("Points faits arrondis + Contrat")
    else:
        # En FFB, le der décide de l'arrondi en cas de 5
        # Le dernier pli détermine qui a fait le 10 de der
        der_attaque = (plis[attaque] > 0 and capot_realise) or (points_cartes[attaque] % 10 in (2, 7) if regles.get("dix_de_der") == 10 else True)
        
        # Arrondi officiel FFB à la dizaine (somme = 160)
        pts_att_arrondi, pts_def_arrondi = arrondir_points_ffb(points_cartes[attaque], points_cartes[defense], der_attaque)
        pts_belote = regles.get("points_belote", 20) if belote is not None else 0

        if reussi:
            if contrat.get("coinche", 0) > 0:
                # Contrat coinché réussi : l'attaque empoche (arrondi + contrat) doublé/triplé
                scores[attaque] += (valeur + pts_att_arrondi) * multi
                if belote == attaque:
                    scores[attaque] += pts_belote
                scores[defense] = 0
            else:
                # Contrat normal réussi : chacun marque ses points faits arrondis, l'attaque ajoute le contrat
                scores[attaque] += valeur + pts_att_arrondi
                scores[defense] += pts_def_arrondi
                if belote == attaque:
                    scores[attaque] += pts_belote
                elif belote == defense:
                    scores[defense] += pts_belote
        else:
            # Chute : la défense empoche 160 + le contrat, multiplié si coinché
            total_chute = (160 + valeur) * multi
            scores[defense] += total_chute
            if belote is not None:
                # La belote reste acquise au camp qui la possède
                scores[belote] += pts_belote
            scores[attaque] = 0


    return scores, reussi

