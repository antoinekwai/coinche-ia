import sys
from regles import REGLES_STANDARD
from rapide import afficher_rapide
from bot_mc_ia import BotMCIA
from bot_coop import BotCoop

if __name__ == "__main__":
    nb = int(sys.argv[1]) if len(sys.argv) > 1 else 800
    regles = REGLES_STANDARD
    
    print(f"=== DUEL : Bot-Coop (Signaux bidirectionnels) vs Bot-MC-IA ({nb} donnes) ===")
    print("Même moteur d'élite, seule la communication par les défausses diffère.\n")
    
    afficher_rapide(BotCoop, BotMCIA, nb, regles, graine=123456)
