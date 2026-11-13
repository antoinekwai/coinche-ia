"""
bot_mc_ia_v7.py
CHAMPION OFFICIEL V7 (Novembre 2026) :
- Réseau V2 (ia_carte_v2_champion.pt, 324 entrées).
- Plis 1 à 3 : JoueurIA_V2 (instantané en 11 ms, zéro bruit MC).
- Plis 4 à 8 : Monte-Carlo 40 simulations avec le Détective v5 guidé
  (réservation souple des atouts du preneur + As pondérés + ZÉRO main fantoche).
- Simulateur interne à cartes fermées déroulé par le Réseau V2 d'élite.
"""
from bot_mc_ia_v6 import BotMCIAv6, FICHIER_V6_RESEAU
from detective_v5 import imaginer_v5
import bot_mc_ia


class BotMCIAv7(BotMCIAv6):
    nom = "Bot-MC-IA v7 (Det v5 + Réseau V2 + MC 40s)"

    def jouer_carte(self, main, jouables, pli, contrat, joueur, regles):
        if len(jouables) == 1:
            return jouables[0]

        # Étage 1 : Plis 1 à 3 en IA V2 pure
        if len(self.historique) < 12:
            self.ia_v2.historique = list(self.historique)
            self.ia_v2.encheres = list(self.encheres) if self.encheres else []
            return self.ia_v2.jouer_carte(main, jouables, pli, contrat, joueur, regles)

        # Étage 2 : Plis 4 à 8 en Monte-Carlo 40 simulations avec Détective v5 guidé !
        ancien = bot_mc_ia.imaginer_donnes_contraintes
        bot_mc_ia.imaginer_donnes_contraintes = imaginer_v5
        try:
            return super().jouer_carte(main, jouables, pli, contrat, joueur, regles)
        finally:
            bot_mc_ia.imaginer_donnes_contraintes = ancien
