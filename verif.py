from regles import REGLES_STANDARD
from joueurs import JoueurRegles
from montecarlo import JoueurMonteCarlo
from rapide import afficher_rapide

if __name__ == "__main__":
    afficher_rapide(JoueurMonteCarlo, JoueurRegles, 3000, REGLES_STANDARD)
