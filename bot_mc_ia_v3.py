"""
bot_mc_ia_v3.py
Bot-MC-IA identique à l'original, mais avec le détective « Système v2 » (detective_v3.py).
"""
import bot_mc_ia
from bot_mc_ia import BotMCIA
from detective_v3 import imaginer_v3


class BotMCIAv3(BotMCIA):
    nom = "Bot-MC-IA v3"

    def jouer_carte(self, main, jouables, pli, contrat, joueur, regles):
        # On remplace temporairement l'ancien détective par le nouveau,
        # puis on remet l'ancien en place (même en cas d'erreur).
        ancien = bot_mc_ia.imaginer_donnes_contraintes
        bot_mc_ia.imaginer_donnes_contraintes = imaginer_v3
        try:
            return super().jouer_carte(main, jouables, pli, contrat, joueur, regles)
        finally:
            bot_mc_ia.imaginer_donnes_contraintes = ancien
