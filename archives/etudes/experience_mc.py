from regles import REGLES_STANDARD
from montecarlo import JoueurMonteCarloContrat
from rapide import afficher_rapide


def mc(n):
    class J(JoueurMonteCarloContrat):
        def __init__(self):
            super().__init__(n)
    J.nom = f"MC{n}"
    return J


if __name__ == "__main__":
    regles = REGLES_STANDARD
    print("=== Plus de réflexion = meilleur jeu ? ===\n")
    afficher_rapide(mc(50), mc(20), 1000, regles)
    afficher_rapide(mc(100), mc(50), 1000, regles)
