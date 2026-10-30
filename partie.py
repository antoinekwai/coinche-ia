from moteur import distribuer, cartes_jouables, gagnant_pli, points, equipe_belote, decompte, texte_main


def annonce_valide(decision, contrat, regles):
    """Vérifie qu'une annonce (valeur, couleur) respecte les règles."""
    valeur, couleur = decision
    if contrat is not None and contrat["capot"]:
        return False
    if regles["capot_autorise"] and valeur == regles["valeur_capot"]:
        return True
    minimum = regles["annonce_min"] if contrat is None else contrat["valeur"] + regles["palier"]
    return minimum <= valeur <= regles["annonce_max"] and valeur % regles["palier"] == 0


def phase_annonces(mains, donneur, joueurs, regles, afficher=False):
    contrat = None
    j = (donneur + 1) % 4
    passes = 0
    encheres = []   # historique des enchères : (joueur, décision)

    while True:
        joueurs[j].encheres = encheres   # chaque joueur peut consulter l'historique
        decision = joueurs[j].annoncer(mains[j], j, contrat, regles)

        # --- Coinche (seulement contre l'équipe adverse) ---
        if decision == "coinche" and contrat is not None and contrat["joueur"] % 2 != j % 2:
            contrat["coinche"] = 1
            encheres.append((j, "coinche"))
            if afficher:
                print(f"  J{j} : COINCHE !")
            for i in range(1, 4):
                p = (j + i) % 4
                if p % 2 == contrat["joueur"] % 2 and joueurs[p].surcoincher(mains[p], p, contrat, regles):
                    contrat["coinche"] = 2
                    if afficher:
                        print(f"  J{p} : SURCOINCHE !")
                    break
            return contrat

        # --- Annonce ---
        if isinstance(decision, tuple) and annonce_valide(decision, contrat, regles):
            valeur, couleur = decision
            capot = regles["capot_autorise"] and valeur == regles["valeur_capot"]
            contrat = {"valeur": valeur, "atout": couleur, "joueur": j, "coinche": 0, "capot": capot}
            passes = 0
            encheres.append((j, decision))
            if afficher:
                print(f"  J{j} : {'CAPOT' if capot else valeur} {couleur}")

        # --- Passe (ou annonce invalide, traitée comme une passe) ---
        else:
            passes += 1
            encheres.append((j, "passe"))
            if afficher:
                print(f"  J{j} : passe")

        if contrat is None and passes == 4:
            return None
        if contrat is not None and passes == 3:
            return contrat
        j = (j + 1) % 4



def jouer_manche(mains, contrat, premier, joueurs, regles, afficher=False):
    atout = contrat["atout"]
    points_eq = [0, 0]
    plis_eq = [0, 0]
    historique = []   # toutes les cartes jouées depuis le début : (joueur, carte)

    for numero in range(1, 9):
        pli = []
        for i in range(4):
            j = (premier + i) % 4
            jouables = cartes_jouables(mains[j], pli, atout, j, regles)
            joueurs[j].historique = historique   # chaque joueur peut consulter l'historique
            carte = joueurs[j].jouer_carte(mains[j], jouables, pli, contrat, j, regles)
            if carte not in jouables:
                carte = jouables[0]
            mains[j].remove(carte)
            pli.append((j, carte))
            historique.append((j, carte))

        gagnant = gagnant_pli(pli, atout)[0]
        equipe = gagnant % 2
        plis_eq[equipe] += 1
        points_eq[equipe] += sum(points(c, atout) for (_, c) in pli)
        if numero == 8:
            points_eq[equipe] += regles["dix_de_der"]

        if afficher:
            print(f"  Pli {numero} : " + "  ".join(f"J{jj}:{r}{c}" for (jj, (r, c)) in pli) + f"  -> J{gagnant}")
        premier = gagnant

    return points_eq, plis_eq



def jouer_donne(donneur, joueurs, regles, afficher=False, mains=None):
    """Joue une donne. Renvoie un résumé (dictionnaire), ou None si tout le monde passe.
    On peut fournir des mains précises (utile plus tard pour le format duplicate)."""
    if mains is None:
        mains = distribuer()
    mains = [m[:] for m in mains]  # copie : les mains d'origine ne sont pas modifiées

    if afficher:
        for j in range(4):
            print(f"  Main J{j} ({joueurs[j].nom}) : {texte_main(mains[j])}")

    contrat = phase_annonces(mains, donneur, joueurs, regles, afficher)
    if contrat is None:
        if afficher:
            print("  Tout le monde passe.\n")
        return None

    belote = equipe_belote(mains, contrat["atout"])
    points_eq, plis_eq = jouer_manche(mains, contrat, (donneur + 1) % 4, joueurs, regles, afficher)
    scores, reussi = decompte(contrat, points_eq, plis_eq, belote, regles)

    if afficher:
        print(f"  Points faits : {points_eq}  plis : {plis_eq}  -> {'RÉUSSI' if reussi else 'CHUTÉ'}, marque {scores}\n")

    return {"scores": scores, "contrat": contrat, "reussi": reussi, "points": points_eq}


def jouer_partie(joueurs, regles, afficher=False):
    """Joue jusqu'au score objectif. Renvoie (équipe gagnante, scores, nombre de donnes)."""
    scores = [0, 0]
    donneur = 0
    nb_donnes = 0

    while True:
        resultat = jouer_donne(donneur, joueurs, regles, afficher)
        donneur = (donneur + 1) % 4
        if resultat is None:
            continue

        nb_donnes += 1
        scores[0] += resultat["scores"][0]
        scores[1] += resultat["scores"][1]

        if max(scores) >= regles["score_objectif"] and scores[0] != scores[1]:
            return (0 if scores[0] > scores[1] else 1), scores, nb_donnes
