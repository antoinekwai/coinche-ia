from regles import REGLES_STANDARD
from joueurs import JoueurRegles
from montecarlo import JoueurMonteCarlo, JoueurMonteCarloContrat
from systeme_corrige import SysCorrige
from rapide import afficher_rapide


class CorrigeSansCoinche(SysCorrige):
    nom = "Corrigé-sans-coinche"
    seuil = 99                       # ne coinche jamais


class MCPointsRegles(JoueurMonteCarlo):
    nom = "MC-points (annonces prudentes)"


class MCContratRegles(JoueurMonteCarloContrat):
    nom = "MC-contrat (annonces prudentes)"


class MCContratSansCoinche(JoueurMonteCarloContrat, CorrigeSansCoinche):
    nom = "MC-contrat (corrigé sans coinche)"


class MCPointsCorrige(JoueurMonteCarlo, SysCorrige):
    nom = "MC-points (corrigé)"
    objectif = "points"


if __name__ == "__main__":
    regles = REGLES_STANDARD
    g, nb = 500000, 4000            # mêmes donnes que le test précédent

    print("=== A. Annonces prudentes, pas de coinche ===")
    afficher_rapide(MCPointsRegles, JoueurRegles, nb, regles, graine=g)
    afficher_rapide(MCContratRegles, JoueurRegles, nb, regles, graine=g)

    print("=== B. Annonces corrigées, sans coinche ===")
    afficher_rapide(MCContratSansCoinche, CorrigeSansCoinche, nb, regles, graine=g)

    print("=== C. Annonces corrigées, avec coinche, objectif points ===")
    afficher_rapide(MCPointsCorrige, SysCorrige, nb, regles, graine=g)
