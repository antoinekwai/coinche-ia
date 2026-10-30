from regles import REGLES_STANDARD
from montecarlo import JoueurMonteCarloContrat
from systeme_corrige import SysCorrige
from experience_coinche import variante
from joueur_reseau import joueur_reseau
from rapide import afficher_rapide


class ActuelMC(JoueurMonteCarloContrat, variante(4)):
    nom = "Actuel-MC"


class CorrigeMC(JoueurMonteCarloContrat, SysCorrige):
    nom = "Corrigé-MC"


class ReseauMC(JoueurMonteCarloContrat, joueur_reseau(0.8)):
    nom = "Réseau-MC"


if __name__ == "__main__":
    regles = REGLES_STANDARD
    print("=== Avec Monte Carlo au jeu de la carte (pour tous) ===\n")
    afficher_rapide(CorrigeMC, ActuelMC, 3000, regles)
    afficher_rapide(ReseauMC, ActuelMC, 3000, regles)
    afficher_rapide(ReseauMC, CorrigeMC, 3000, regles)
