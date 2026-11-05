"""
bot_mc_ia_v5.py
CHAMPION OFFICIEL DU PROJET (Issu des benchmarks comparatifs de nov. 2026).
Architecture hybride à deux étages :
1. Plis 1 à 3 : JoueurIA (réseau de neurones pur + arbitrage canonique As-10).
   -> Instantané, zéro bruit d'échantillonnage, respecte les entames d'école.
2. Plis 4 à 8 : Monte-Carlo 40 simulations avec Détective v3 (rejeu des enchères).
   -> Haute résolution sur les 5 derniers plis, calcul précis des fins de coups.
Performance mesurée : +26.4 pts de marque vs ancien v3 (+14.1 vs v3_std),
temps moyen : 1.27 s / partie.
"""
from bot_mc_ia import BotMCIA
from ia_joueur import JoueurIA
from detective_v3 import imaginer_v3
import bot_mc_ia


class BotMCIAv5(BotMCIA):
    nom = "Bot-MC-IA v5 (Hybride 40s)"

    def __init__(self, nb_simulations=40):
        super().__init__()
        self.nb_simulations = nb_simulations
        self.ia = JoueurIA()

    def jouer_carte(self, main, jouables, pli, contrat, joueur, regles):
        if len(jouables) == 1:
            return jouables[0]

        # Étage 1 : Plis 1, 2 et 3 (moins de 12 cartes jouées au total)
        # Prise de décision par le réseau de neurones pur (rapide et sans bruit MC)
        if len(self.historique) < 12:
            self.ia.historique = list(self.historique)
            self.ia.encheres = list(self.encheres) if self.encheres else []
            return self.ia.jouer_carte(main, jouables, pli, contrat, joueur, regles)

        # Étage 2 : Plis 4 à 8
        # Monte-Carlo 40 simulations avec détective v3 (rejeu des enchères)
        ancien_detective = bot_mc_ia.imaginer_donnes_contraintes
        bot_mc_ia.imaginer_donnes_contraintes = imaginer_v3
        try:
            return super().jouer_carte(main, jouables, pli, contrat, joueur, regles)
        finally:
            bot_mc_ia.imaginer_donnes_contraintes = ancien_detective
