from regles import REGLES_STANDARD
from signaux import JoueurSignaux
from match_mc import SystemeMCContrat
from duplicate import afficher


def variante(conf, emettre=True):
    """Joueur à signaux avec une confiance donnée."""
    class J(JoueurSignaux):
        nom = f"Signaux-c{conf}"
        confiance = conf
    J.emettre = emettre
    return J


if __name__ == "__main__":
    regles = REGLES_STANDARD
    nb = 400

    print("=== 1. Coût de la convention (émet, mais ne lit pas) ===")
    afficher(variante(0), SystemeMCContrat, nb, regles, progression=True)

    print("=== 2. Apport de la lecture (confiance 0.8 contre 0) ===")
    afficher(variante(0.8), variante(0), nb, regles, progression=True)

    print("=== 3. Faut-il croire davantage les signaux ? (0.95 contre 0.5) ===")
    afficher(variante(0.95), variante(0.5), nb, regles, progression=True)

    print("=== 4. Bilan global : signaux (0.8) contre sans signaux ===")
    afficher(variante(0.8), SystemeMCContrat, nb, regles, progression=True)
