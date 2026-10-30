from regles import REGLES_STANDARD
from joueurs import JoueurRegles
from systeme import JoueurSysteme
from duplicate import afficher
from experience_audace import joueur_audace
from diagnostic import diagnostic


def systeme_marge(valeur):
    """Fabrique votre système avec une marge donnée (quand les adversaires parlent)."""
    class Joueur(JoueurSysteme):
        nom = f"Marge{valeur}"
        marge = valeur
    return Joueur


if __name__ == "__main__":
    regles = REGLES_STANDARD

    print("=== Test de contrôle (doit donner 0) ===")
    afficher(JoueurSysteme, JoueurSysteme, 2000, regles)

    print("=== Votre système contre le joueur à règles ===")
    afficher(JoueurSysteme, JoueurRegles, 5000, regles)

    print("=== Votre système contre le meilleur joueur à règles (audace +20) ===")
    afficher(JoueurSysteme, joueur_audace(20), 5000, regles)

    print("=== Quelle marge quand les adversaires parlent ? (contre audace +20) ===")
    for m in [0, 20, 30]:
        afficher(systeme_marge(m), joueur_audace(20), 5000, regles)

    print("=== Diagnostic de votre système (4 joueurs Système) ===")
    diagnostic(JoueurSysteme, 20000, regles)
