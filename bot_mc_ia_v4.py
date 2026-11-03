"""
bot_mc_ia_v4.py
Bot-MC-IA avec le détective v4 (detective_v4.py) : détective v3 + lecture par le
réseau de l'entame et de la 1re défausse de chaque joueur.
Le v3 (bot_mc_ia_v3.py) n'est PAS modifié.
"""
from functools import partial

import bot_mc_ia
from bot_mc_ia import BotMCIA
import detective_v4
from detective_v4 import imaginer_v4


class BotMCIAv4(BotMCIA):
    nom = "Bot-MC-IA v4 (T=0,1)"
    temperature = 0.1

    def jouer_carte(self, main, jouables, pli, contrat, joueur, regles):
        # Remplacement temporaire du détective. partial ajoute le contrat
        # (absent de l'appel de BotMCIA) et la température.
        ancien = bot_mc_ia.imaginer_donnes_contraintes
        bot_mc_ia.imaginer_donnes_contraintes = partial(
            imaginer_v4, contrat=contrat, temperature=self.temperature)
        try:
            return super().jouer_carte(main, jouables, pli, contrat, joueur, regles)
        finally:
            bot_mc_ia.imaginer_donnes_contraintes = ancien
            detective_v4.ECARTS.clear()   # évite que la liste de diagnostic grossisse


class BotMCIAv4T03(BotMCIAv4):
    nom = "Bot-MC-IA v4 (T=0,03)"
    temperature = 0.03
