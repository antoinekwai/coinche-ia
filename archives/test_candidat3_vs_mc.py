import sys
from regles import REGLES_STANDARD
from rapide import afficher_rapide
from test_mc_encheres import MCEncheres
from bot_mcts_pruned import BotCandidat3

if __name__ == "__main__":
    nb = int(sys.argv[1]) if len(sys.argv) > 1 else 600
    regles = REGLES_STANDARD
    
    print(f"=== DUEL : Candidat 3 (Élagage IA à 2 coups) vs MC-Enchères ({nb} donnes) ===")
    print("Même système d'annonces, comparaison pure du jeu de la carte.\n")
    
    # 600 donnes en duplicate pour comparer directement avec le Candidat 2
    afficher_rapide(BotCandidat3, MCEncheres, nb, regles, graine=654321)
