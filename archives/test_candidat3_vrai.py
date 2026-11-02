import sys
from regles import REGLES_STANDARD
from rapide import afficher_rapide
from test_mc_encheres import MCEncheres
from bot_candidat3_vrai import BotCandidat3Vrai

if __name__ == "__main__":
    nb = int(sys.argv[1]) if len(sys.argv) > 1 else 600
    regles = REGLES_STANDARD
    
    print(f"=== DUEL : VRAI Candidat 3 (Minimax Trick + IA Rollout) vs MC-Enchères ({nb} donnes) ===")
    print("Même système d'annonces, comparaison pure du jeu de la carte.\n")
    
    afficher_rapide(BotCandidat3Vrai, MCEncheres, nb, regles, graine=654321)
