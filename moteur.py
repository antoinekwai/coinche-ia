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
    valeur *= multi

    scores = [0, 0]
    if regles["mode_score"] == "contrat":
        if reussi:
            scores[attaque] += valeur
        else:
            chute = regles.get("valeur_chute")
            if chute is not None and not contrat["capot"]:
                scores[defense] += max(chute, contrat["valeur"]) * multi
            else:
                scores[defense] += valeur

    elif reussi:
        scores[attaque] += valeur + points_cartes[attaque]
        scores[defense] += points_cartes[defense]
    else:
        scores[defense] += valeur + sum(points_cartes)

    if belote is not None and regles["belote_au_score"]:
        scores[belote] += regles["points_belote"]
    return scores, reussi
