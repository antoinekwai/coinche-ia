import random
from regles import REGLES_STANDARD, VARIANTE_POINTS_FAITS

# ============================================================
# 1. LES CARTES
# ============================================================

COULEURS = ["♠", "♥", "♦", "♣"]
RANGS = ["7", "8", "9", "10", "V", "D", "R", "A"]

ORDRE_ATOUT     = {"7": 0, "8": 1, "D": 2, "R": 3, "10": 4, "A": 5, "9": 6, "V": 7}
ORDRE_NON_ATOUT = {"7": 0, "8": 1, "9": 2, "V": 3, "D": 4, "R": 5, "10": 6, "A": 7}

POINTS_ATOUT     = {"7": 0, "8": 0, "D": 3, "R": 4, "10": 10, "A": 11, "9": 14, "V": 20}
POINTS_NON_ATOUT = {"7": 0, "8": 0, "9": 0, "V": 2, "D": 3, "R": 4, "10": 10, "A": 11}


def nouveau_paquet():
    paquet = []
    for couleur in COULEURS:
        for rang in RANGS:
            paquet.append((rang, couleur))
    return paquet


def distribuer():
    paquet = nouveau_paquet()
    random.shuffle(paquet)
    return [paquet[0:8], paquet[8:16], paquet[16:24], paquet[24:32]]


def points(carte, atout):
    rang, couleur = carte
    if couleur == atout:
        return POINTS_ATOUT[rang]
    return POINTS_NON_ATOUT[rang]


def texte_main(main):
    return " ".join(r + c for (r, c) in main)


# ============================================================
# 2. QUI GAGNE LE PLI ?
# ============================================================

def force(carte, atout, couleur_demandee):
    rang, couleur = carte
    if couleur == atout:
        return 100 + ORDRE_ATOUT[rang]
    if couleur == couleur_demandee:
        return ORDRE_NON_ATOUT[rang]
    return -1


def gagnant_pli(pli, atout):
    couleur_demandee = pli[0][1][1]
    meilleur = pli[0]
    for joueur_carte in pli:
        if force(joueur_carte[1], atout, couleur_demandee) > force(meilleur[1], atout, couleur_demandee):
            meilleur = joueur_carte
    return meilleur


# ============================================================
# 3. LES CARTES AUTORISÉES (dépendent des règles)
# ============================================================

def cartes_jouables(main, pli, atout, joueur, regles):
    if len(pli) == 0:
        return main[:]

    couleur_demandee = pli[0][1][1]
    partenaire = (joueur + 2) % 4
    joueur_maitre = gagnant_pli(pli, atout)[0]
    partenaire_maitre = (joueur_maitre == partenaire)

    atouts_main = [c for c in main if c[1] == atout]
    meme_couleur = [c for c in main if c[1] == couleur_demandee]

    atouts_pli = [c for (j, c) in pli if c[1] == atout]
    plus_fort_pli = max([ORDRE_ATOUT[c[0]] for c in atouts_pli], default=-1)
    atouts_plus_forts = [c for c in atouts_main if ORDRE_ATOUT[c[0]] > plus_fort_pli]

    # Cas 1 : atout demandé
    if couleur_demandee == atout:
        doit_monter = regles["monter_si_partenaire_maitre"] or not partenaire_maitre
        if doit_monter and atouts_plus_forts:
            return atouts_plus_forts
        if atouts_main:
            return atouts_main
        return main[:]

    # Cas 2 : on a la couleur demandée
    if meme_couleur:
        return meme_couleur

    # Cas 3 : on n'a pas la couleur
    if partenaire_maitre and not regles["couper_si_partenaire_maitre"]:
        return main[:]
    if atouts_plus_forts:
        return atouts_plus_forts
    if atouts_main:
        return atouts_main
    return main[:]


# ============================================================
# 4. LES ANNONCES
# ============================================================
# Un contrat est un dictionnaire :
#   {"valeur": 100, "atout": "♥", "joueur": 2, "coinche": 0}
#   coinche : 0 = normal, 1 = coinché, 2 = surcoinché
def annonce_aleatoire(main, joueur, contrat, regles):
    """Joueur qui annonce au hasard (provisoire, il sera remplacé par une IA)."""
    if contrat is not None and contrat["joueur"] % 2 != joueur % 2:
        if random.random() < 0.05:
            return "coinche"

    if random.random() < 0.7:
        return "passe"

    if contrat is None:
        valeur = regles["annonce_min"]
    else:
        valeur = contrat["valeur"] + regles["palier"]

    if valeur > regles["annonce_max"]:
        # Au-delà de 160, seule l'annonce du capot est encore possible
        if regles["capot_autorise"] and not contrat["capot"]:
            valeur = regles["valeur_capot"]
        else:
            return "passe"
    return (valeur, random.choice(COULEURS))



def surcoinche_aleatoire(main, joueur, contrat, regles):
    return random.random() < 0.2


def phase_annonces(mains, donneur, regles, afficher=True):
    """Déroule les enchères. Renvoie le contrat, ou None si tout le monde passe."""
    contrat = None
    joueur = (donneur + 1) % 4
    passes_consecutives = 0

    while True:
        decision = annonce_aleatoire(mains[joueur], joueur, contrat, regles)

        if decision == "passe":
            passes_consecutives += 1
            if afficher:
                print(f"  J{joueur} : passe")

        elif decision == "coinche":
            contrat["coinche"] = 1
            if afficher:
                print(f"  J{joueur} : COINCHE !")
            equipe_attaque = contrat["joueur"] % 2
            for i in range(1, 4):
                p = (joueur + i) % 4
                if p % 2 == equipe_attaque and surcoinche_aleatoire(mains[p], p, contrat, regles):
                    contrat["coinche"] = 2
                    if afficher:
                        print(f"  J{p} : SURCOINCHE !")
                    break
            return contrat

        else:
            valeur, couleur = decision
            est_capot = regles["capot_autorise"] and valeur == regles["valeur_capot"]
            contrat = {"valeur": valeur, "atout": couleur, "joueur": joueur,
                       "coinche": 0, "capot": est_capot}
            passes_consecutives = 0
            if afficher:
                nom = "CAPOT" if est_capot else valeur
                print(f"  J{joueur} : {nom} {couleur}")


        if contrat is None and passes_consecutives == 4:
            return None
        if contrat is not None and passes_consecutives == 3:
            return contrat

        joueur = (joueur + 1) % 4


# ============================================================
# 5. JOUER LES 8 PLIS
# ============================================================

def jouer_manche(mains, atout, premier_joueur, regles, afficher=False):
    points_equipes = [0, 0]
    plis_equipes = [0, 0]

    for numero_pli in range(1, 9):
        pli = []
        for i in range(4):
            joueur = (premier_joueur + i) % 4
            choix = cartes_jouables(mains[joueur], pli, atout, joueur, regles)
            carte = random.choice(choix)
            mains[joueur].remove(carte)
            pli.append((joueur, carte))

        gagnant, carte_gagnante = gagnant_pli(pli, atout)
        equipe = gagnant % 2
        plis_equipes[equipe] += 1
        points_equipes[equipe] += sum(points(c, atout) for (j, c) in pli)
        if numero_pli == 8:
            points_equipes[equipe] += regles["dix_de_der"]

        if afficher:
            cartes = "  ".join(f"J{j}:{c[0]}{c[1]}" for (j, c) in pli)
            print(f"  Pli {numero_pli} : {cartes}  ->  J{gagnant}")

        premier_joueur = gagnant

    return points_equipes, plis_equipes

# ============================================================
# 6. BELOTE ET DÉCOMPTE (dépendent des règles)
# ============================================================

def equipe_belote(mains, atout):
    """Renvoie l'équipe (0 ou 1) qui a Roi + Dame d'atout, ou None."""
    for joueur in range(4):
        if ("R", atout) in mains[joueur] and ("D", atout) in mains[joueur]:
            return joueur % 2
    return None


def decompte(contrat, points_cartes, plis, belote, regles):
    """Calcule le score de la donne. Renvoie ([score eq0, score eq1], réussi)."""
    attaque = contrat["joueur"] % 2
    defense = 1 - attaque

    multiplicateur = 1
    if contrat["coinche"] == 1:
        multiplicateur = regles["multi_coinche"]
    elif contrat["coinche"] == 2:
        multiplicateur = regles["multi_surcoinche"]

    capot_realise = (plis[attaque] == 8)

    if contrat["capot"]:
        # Capot annoncé : il faut faire les 8 plis (la belote n'aide pas)
        reussi = capot_realise
    else:
        points_attaque = points_cartes[attaque]
        if belote == attaque and regles["belote_pour_contrat"]:
            points_attaque += regles["points_belote"]
        reussi = points_attaque >= contrat["valeur"]

    valeur = contrat["valeur"]
    # Capot réalisé sans avoir été annoncé (si la règle l'autorise)
    if not contrat["capot"] and capot_realise and regles["capot_non_annonce"]:
        valeur = max(valeur, regles["valeur_capot"])
    valeur = valeur * multiplicateur

    scores = [0, 0]
    if regles["mode_score"] == "contrat":
        if reussi:
            scores[attaque] += valeur
        else:
            scores[defense] += valeur
    else:
        if reussi:
            scores[attaque] += valeur + points_cartes[attaque]
            scores[defense] += points_cartes[defense]
        else:
            scores[defense] += valeur + sum(points_cartes)

    if belote is not None and regles["belote_au_score"]:
        scores[belote] += regles["points_belote"]

    return scores, reussi


# ============================================================
# 7. UNE DONNE, PUIS UNE PARTIE COMPLÈTE
# ============================================================

def jouer_donne(donneur, regles, afficher=True):
    """Joue une donne. Renvoie les scores, ou None si tout le monde a passé."""
    mains = distribuer()
    contrat = phase_annonces(mains, donneur, regles, afficher)
    if contrat is None:
        if afficher:
            print("  Tout le monde passe, on redistribue.\n")
        return None

    atout = contrat["atout"]
    belote = equipe_belote(mains, atout)
    points_cartes, plis = jouer_manche(mains, atout, (donneur + 1) % 4, regles)
    scores, reussi = decompte(contrat, points_cartes, plis, belote, regles)

    if afficher:
        etat = ["", " coinché", " surcoinché"][contrat["coinche"]]
        nom = "CAPOT" if contrat["capot"] else contrat["valeur"]
        print(f"  Contrat : {nom} {atout}{etat} par J{contrat['joueur']}")
        print(f"  Points faits : équipe 0 = {points_cartes[0]}, équipe 1 = {points_cartes[1]}"
              f"  (plis : {plis[0]} / {plis[1]})"
              + (f"  (belote : équipe {belote})" if belote is not None else ""))
        print(f"  {'RÉUSSI' if reussi else 'CHUTÉ'} -> marque : {scores}\n")
    return scores


def jouer_partie(regles, afficher=True):
    """Joue jusqu'au score objectif. Renvoie (équipe gagnante, scores, nombre de donnes)."""
    scores = [0, 0]
    donneur = 0
    nb_donnes = 0

    while True:
        if afficher:
            print(f"--- Donne (donneur J{donneur}) ---")
        resultat = jouer_donne(donneur, regles, afficher)
        donneur = (donneur + 1) % 4

        if resultat is None:
            continue

        nb_donnes += 1
        scores[0] += resultat[0]
        scores[1] += resultat[1]
        if afficher:
            print(f"  SCORE : équipe 0 = {scores[0]}  |  équipe 1 = {scores[1]}\n")

        if max(scores) >= regles["score_objectif"] and scores[0] != scores[1]:
            gagnant = 0 if scores[0] > scores[1] else 1
            return gagnant, scores, nb_donnes


# ============================================================
# 8. PROGRAMME PRINCIPAL
# ============================================================

if __name__ == "__main__":
    # Une partie détaillée avec vos règles
    gagnant, scores, nb = jouer_partie(REGLES_STANDARD, afficher=True)
    print(f"=== L'équipe {gagnant} gagne {scores[gagnant]} à {scores[1 - gagnant]} en {nb} donnes ===\n")

    # Démonstration de la flexibilité : 1000 parties par variante
    for nom, regles in [("Standard", REGLES_STANDARD), ("Points faits", VARIANTE_POINTS_FAITS)]:
        total_donnes = 0
        for _ in range(1000):
            total_donnes += jouer_partie(regles, afficher=False)[2]
        print(f"{nom} : {total_donnes / 1000:.1f} donnes par partie en moyenne")
