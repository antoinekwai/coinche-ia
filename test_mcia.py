import sys
from regles import REGLES_STANDARD
from rapide import afficher_rapide
from mc_ia import JoueurMCIA
from ia_evaluer import CorrigeMC

if __name__ == "__main__":
    nb = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    print(f"=== Monte Carlo amélioré (IA) contre Monte Carlo classique ({nb} donnes) ===")
    afficher_rapide(JoueurMCIA, CorrigeMC, nb, REGLES_STANDARD, graine=600000)
