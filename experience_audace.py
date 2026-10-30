from regles import REGLES_STANDARD
from joueurs import JoueurRegles
from duplicate import afficher


def joueur_audace(valeur):
    """Fabrique un joueur à règles avec une audace donnée."""
    class Joueur(JoueurRegles):
        nom = f"Audace{valeur:+d}"
        audace = valeur
    return Joueur


if __name__ == "__main__":
    regles = REGLES_STANDARD
    print("=== Chaque audace contre le joueur à règles normal (audace 0) ===\n")
    for a in [-20, -10, 10, 20, 30, 40, 50]:
        afficher(joueur_audace(a), JoueurRegles, 3000, regles)
