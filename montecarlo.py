import random
from moteur import COULEURS, RANGS, cartes_jouables, gagnant_pli, points
from joueurs import JoueurRegles


def manques(historique, atout, regles):
    """Déduit les couleurs que chaque joueur n'a plus, d'après les cartes jouées."""
    manque = {j: set() for j in range(4)}
    for debut in range(0, len(historique), 4):
        pli = historique[debut:debut + 4]
        demandee = pli[0][1][1]
        for k in range(1, len(pli)):
            j, (rang, couleur) = pli[k]
            if couleur != demandee:
                manque[j].add(demandee)          # il n'a pas fourni : il n'en a plus
                partenaire_maitre = gagnant_pli(pli[:k], atout)[0] == (j + 2) % 4
                obligation_couper = not partenaire_maitre or regles["couper_si_partenaire_maitre"]
                if couleur != atout and obligation_couper:
                    manque[j].add(atout)         # il devait couper et ne l'a pas fait
    return manque


def imaginer_mains(main, joueur, historique, manque):
    """Invente une répartition des cartes cachées compatible avec ce qu'on sait."""
    jouees = {c for (_, c) in historique}
    inconnues = [(r, c) for c in COULEURS for r in RANGS
                 if (r, c) not in jouees and (r, c) not in main]
    places = {j: 8 - sum(1 for (jj, _) in historique if jj == j)
              for j in range(4) if j != joueur}

    for essai in range(20):
        random.shuffle(inconnues)
        # On place d'abord les cartes qui ont le moins de destinataires possibles
        tri = sorted(inconnues, key=lambda c: sum(1 for j in places if c[1] not in manque[j]))
        reste = dict(places)
        mains = [[] for _ in range(4)]
        reussi = True
        for carte in tri:
            possibles = [j for j in reste if reste[j] > 0 and carte[1] not in manque[j]]
            if not possibles:
                reussi = False
                break
            j = random.choices(possibles, weights=[reste[p] for p in possibles])[0]
            mains[j].append(carte)
            reste[j] -= 1
        if reussi:
            mains[joueur] = main[:]
            return mains

    # Secours (très rare) : on distribue sans tenir compte des couleurs manquantes
    random.shuffle(inconnues)
    mains = [[] for _ in range(4)]
    i = 0
    for j, n in places.items():
        mains[j] = inconnues[i:i + n]
        i += n
    mains[joueur] = main[:]
    return mains


def simuler(mains, pli, contrat, joueur, carte, plis_faits, regles):
    """Joue la fin de la donne 'dans sa tête' après avoir posé `carte`.
    Renvoie (points par équipe, plis par équipe) à partir de maintenant."""
    atout = contrat["atout"]
    robot = JoueurRegles()
    mains = [m[:] for m in mains]
    mains[joueur].remove(carte)
    pli = pli + [(joueur, carte)]
    prochain = (joueur + 1) % 4
    pts_eq, plis_eq = [0, 0], [0, 0]

    while plis_faits < 8:
        while len(pli) < 4:
            j = prochain
            jouables = cartes_jouables(mains[j], pli, atout, j, regles)
            c = robot.jouer_carte(mains[j], jouables, pli, contrat, j, regles)
            mains[j].remove(c)
            pli.append((j, c))
            prochain = (j + 1) % 4

        gagnant = gagnant_pli(pli, atout)[0]
        plis_faits += 1
        pts = sum(points(c, atout) for (_, c) in pli)
        if plis_faits == 8:
            pts += regles["dix_de_der"]
        pts_eq[gagnant % 2] += pts
        plis_eq[gagnant % 2] += 1
        pli = []
        prochain = gagnant

    return pts_eq, plis_eq


def bilan_passe(historique, atout):
    """Points et plis déjà gagnés par chaque équipe (plis terminés uniquement)."""
    pts_eq, plis_eq = [0, 0], [0, 0]
    for k in range(len(historique) // 4):
        pli = historique[4 * k:4 * k + 4]
        e = gagnant_pli(pli, atout)[0] % 2
        pts_eq[e] += sum(points(c, atout) for (_, c) in pli)
        plis_eq[e] += 1
    return pts_eq, plis_eq


def belote_imaginee(mains, historique, atout):
    """Équipe qui a la belote dans cette répartition imaginée (cartes en main + déjà jouées)."""
    for j in range(4):
        cartes = mains[j] + [c for (jj, c) in historique if jj == j]
        if ("R", atout) in cartes and ("D", atout) in cartes:
            return j % 2
    return None


def contrat_reussi(contrat, pts_attaque, plis_attaque, belote_attaque, regles):
    if contrat["capot"]:
        return plis_attaque == 8
    if belote_attaque and regles["belote_pour_contrat"]:
        pts_attaque += regles["points_belote"]
    return pts_attaque >= contrat["valeur"]


class JoueurMonteCarlo(JoueurRegles):
    """Annonce comme le joueur à règles, mais joue la carte par simulation."""
    nom = "MonteCarlo"
    historique = []
    objectif = "points"     # "points" ou "contrat"

    def __init__(self, nb_simulations=20):
        self.nb_simulations = nb_simulations

    def imaginer(self, main, joueur, manque, atout):
        """Imagine les mains cachées (sera enrichi par la lecture des signaux)."""
        return imaginer_mains(main, joueur, self.historique, manque)

    def jouer_carte(self, main, jouables, pli, contrat, joueur, regles):
        if len(jouables) == 1:
            return jouables[0]

        atout = contrat["atout"]
        equipe = joueur % 2
        attaque = contrat["joueur"] % 2
        manque = manques(self.historique, atout, regles)
        plis_faits = (len(self.historique) - len(pli)) // 4
        passe_pts, passe_plis = bilan_passe(self.historique, atout)
        totaux = {carte: 0 for carte in jouables}

        for _ in range(self.nb_simulations):
            mains = self.imaginer(main, joueur, manque, atout)
            belote = belote_imaginee(mains, self.historique, atout)
            for carte in jouables:
                pts, plis = simuler(mains, pli, contrat, joueur, carte, plis_faits, regles)
                if self.objectif == "points":
                    totaux[carte] += pts[equipe]
                else:
                    reussi = contrat_reussi(contrat,
                                            passe_pts[attaque] + pts[attaque],
                                            passe_plis[attaque] + plis[attaque],
                                            belote == attaque, regles)
                    gagne = reussi if equipe == attaque else not reussi
                    # 1000 par contrat gagné (priorité absolue), les points départagent
                    totaux[carte] += 1000 * gagne + pts[equipe]

        return max(jouables, key=lambda c: totaux[c])


class JoueurMonteCarloContrat(JoueurMonteCarlo):
    nom = "MCContrat"
    objectif = "contrat"
