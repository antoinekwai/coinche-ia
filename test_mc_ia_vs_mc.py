import sys
from regles import REGLES_STANDARD
from rapide import afficher_rapide
from test_mc_encheres import MCEncheres
from bot_mc_ia import BotMCIA

if __name__ == "__main__":
    nb = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    regles = REGLES_STANDARD
    
    print(f"=== DUEL : Bot-MC-IA (Candidat 2) vs MC-Enchères ({nb} donnes) ===")
    print("Même système d'annonces, comparaison pure du jeu de la carte.\n")
    
    afficher_rapide(BotMCIA, MCEncheres, nb, regles, graine=654321)
