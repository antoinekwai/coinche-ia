from regles import REGLES_STANDARD
from systeme_corrige import SysCorrige
from ia_joueur import JoueurIA
from ia_evaluer import CorrigeMC
from test_mc_encheres import MCEncheres
from rapide import afficher_rapide

if __name__ == "__main__":
    regles, g = REGLES_STANDARD, 500000
    print("=== IA contre jeu à règles ===")
    afficher_rapide(JoueurIA, SysCorrige, 20000, regles, graine=g)
    print("=== IA contre Monte Carlo classique ===")
    afficher_rapide(JoueurIA, CorrigeMC, 6000, regles, graine=g)
    print("=== IA contre Monte Carlo enchères ===")
    afficher_rapide(JoueurIA, MCEncheres, 6000, regles, graine=g)
