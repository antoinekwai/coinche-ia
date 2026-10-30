import random
from moteur import COULEURS, POINTS_ATOUT, points, gagnant_pli, force


def valeur_suivante(contrat, regles):
    """Plus petite annonce encore autorisée."""
    if contrat is None:
        return regles["annonce_min"]
    return contrat["valeur"] + regles["palier"]


# ============================================================
# JOUEUR ALÉATOIRE (sert de référence)
# ============================================================

class JoueurAleatoire:
    nom = "Aléatoire"

    def annoncer(self, main, joueur, contrat, regles):
        if contrat is not None and contrat["joueur"] % 2 != joueur % 2:
            if random.random() < 0.05:
                return "coinche"
        if random.random() < 0.7:
            return "passe"
        valeur = valeur_suivante(contrat, regles)
        if valeur > regles["annonce_max"]:
            if regles["capot_autorise"] and not contrat["capot"]:
                valeur = regles["valeur_capot"]
            else:
                return "passe"
        return (valeur, random.choice(COULEURS))

    def surcoincher(self, main, joueur, contrat, regles):
        return random.random() < 0.2

    def jouer_carte(self, main, jouables, pli, contrat, joueur, regles):
        return random.choice(jouables)


# ============================================================
# JOUEUR À RÈGLES (un peu de bon sens)
# ============================================================

def estimer(main, atout):
    """Estimation grossière des points qu'on peut faire avec cet atout."""
    total = 0
    for rang, couleur in main:
        if couleur == atout:
            total += POINTS_ATOUT[rang] + 10       # chaque atout vaut ses points + 10
        elif rang == "A":
            total += 11                            # as à côté
        elif rang == "10" and ("A", couleur) in main:
            total += 10                            # 10 protégé par l'as
    if ("R", atout) in main and ("D", atout) in main:
        total += 20                                # belote
    return total


class JoueurRegles:
    nom = "Règles"
    audace = 0

    def annoncer(self, main, joueur, contrat, regles):
        # Coincher l'adversaire si on tient ses atouts
        if contrat is not None and contrat["joueur"] % 2 != joueur % 2:
            a = contrat["atout"]
            nb_atouts = len([c for c in main if c[1] == a])
            nb_as = len([c for c in main if c[0] == "A" and c[1] != a])
            if ("V", a) in main and nb_atouts >= 3 and nb_as >= 1 and contrat["valeur"] >= 100:
                return "coinche"

        # On ne surenchérit pas sur son partenaire (simplification)
        if contrat is not None and (contrat["joueur"] % 2 == joueur % 2 or contrat["capot"]):
            return "passe"

        couleur = max(COULEURS, key=lambda c: estimer(main, c))
        annonce = (estimer(main, couleur) + self.audace) // regles["palier"] * regles["palier"]
        annonce = min(annonce, regles["annonce_max"])

        if annonce >= valeur_suivante(contrat, regles) and annonce >= regles["annonce_min"]:
            return (annonce, couleur)
        return "passe"

    def surcoincher(self, main, joueur, contrat, regles):
        return estimer(main, contrat["atout"]) >= contrat["valeur"] + 20

    def jouer_carte(self, main, jouables, pli, contrat, joueur, regles):
        atout = contrat["atout"]
        if len(jouables) == 1:
            return jouables[0]

        # --- On entame ---
        if not pli:
            attaque = contrat["joueur"] % 2 == joueur % 2
            if attaque and ("V", atout) in jouables:
                return ("V", atout)                       # faire tomber les atouts
            as_cote = [c for c in jouables if c[0] == "A" and c[1] != atout]
            if as_cote:
                return as_cote[0]                         # encaisser ses as
            return min(jouables, key=lambda c: (c[1] == atout, points(c, atout)))

        # --- On suit ---
        couleur_demandee = pli[0][1][1]
        partenaire_maitre = gagnant_pli(pli, atout)[0] == (joueur + 2) % 4
        gagnantes = [c for c in jouables
                     if gagnant_pli(pli + [(joueur, c)], atout)[0] == joueur]

        if partenaire_maitre and len(pli) == 3:
            # Dernier à jouer et partenaire maître : on charge des points (hors atout)
            return max(jouables, key=lambda c: (c[1] != atout, points(c, atout)))
        if partenaire_maitre:
            return min(jouables, key=lambda c: (points(c, atout), c[1] == atout))
        if gagnantes:
            # On prend le pli avec la carte la plus faible possible
            return min(gagnantes, key=lambda c: force(c, atout, couleur_demandee))
        # On ne peut pas gagner : on donne le moins de points possible
        return min(jouables, key=lambda c: (points(c, atout), c[1] == atout))
