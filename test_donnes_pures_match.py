import sys
from regles import REGLES_STANDARD
from rapide import afficher_rapide
from test_mc_encheres import MCEncheres
from bot_mc_ia import BotMCIA

if __name__ == "__main__":
    nb = int(sys.argv[1]) if len(sys.argv) > 1 else 600
    regles = REGLES_STANDARD
    print(f"=== DUEL : Bot-MC-IA avec ÉCHANTILLONNAGE PUR vs MC-Enchères classique ({nb} donnes) ===")
    afficher_rapide(BotMCIA, MCEncheres, nb, regles, graine=112233)
