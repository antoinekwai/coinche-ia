from regles import REGLES_STANDARD
from montecarlo import JoueurMonteCarloContrat
from systeme_corrige import SysCorrige
from dispute import JoueurDispute
from experience_coinche import variante
from rapide import afficher_rapide


class DisputeMC(JoueurMonteCarloContrat, JoueurDispute):
    nom = "Disputé-MC"


class CorrigeMC(JoueurMonteCarloContrat, SysCorrige):
    nom = "Corrigé-MC"


if __name__ == "__main__":
    regles = REGLES_STANDARD
    print("=== Confirmation avec Monte Carlo (20 000 donnes) ===")
    afficher_rapide(DisputeMC, CorrigeMC, 20000, regles)

