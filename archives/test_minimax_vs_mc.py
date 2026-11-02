import sys
from regles import REGLES_STANDARD
from rapide import afficher_rapide
from test_mc_encheres import MCEncheres
from bot_minimax import BotMinimax

if __name__ == "__main__":
    nb = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    regles = REGLES_STANDARD
    
    print(f"=== DUEL : Bot-Minimax (Double Dummy) vs MC-Enchères ({nb} donnes) ===")
    print("Même système d'annonces, comparaison pure du jeu de la carte face à la défense parfaite.\n")
    
    # 300 donnes en duplicate pour voir l'effet net
    afficher_rapide(BotMinimax, MCEncheres, nb, regles, graine=777777)
