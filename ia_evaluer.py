from regles import REGLES_STANDARD
from systeme_corrige import SysCorrige
from montecarlo import JoueurMonteCarloContrat
from ia_joueur import JoueurIA
from rapide import afficher_rapide


class CorrigeMC(JoueurMonteCarloContrat, SysCorrige):
    nom = "Corrigé-MC"


if __name__ == "__main__":
    regles = REGLES_STANDARD
    g = 500000   # donnes jamais utilisées pendant l'entraînement ni les évaluations

    print("=== 1. Confirmation sur de nouvelles donnes : IA contre jeu à règles ===")
    afficher_rapide(JoueurIA, SysCorrige, 20000, regles, graine=g)

    print("=== 2. Repère : Monte Carlo contre jeu à règles (mêmes donnes) ===")
    afficher_rapide(CorrigeMC, SysCorrige, 6000, regles, graine=g)

    print("=== 3. Le duel : IA contre Monte Carlo ===")
    afficher_rapide(JoueurIA, CorrigeMC, 6000, regles, graine=g)
