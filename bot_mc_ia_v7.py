"""
bot_mc_ia_v7.py
CHAMPION OFFICIEL V7 :
- Réseau V2 (ia_carte_v2_champion.pt, 324 entrées).
- Plis 1 à 3 : JoueurIA_V2 (instantané en 11 ms, zéro bruit MC).
- Plis 4 à 8 : Monte-Carlo 40 simulations avec le Détective v5 guidé réparé (imaginer_v5).
- Simulateur interne à cartes fermées déroulé par le Réseau V2 d'élite avec bilan_passe !
"""
from bot_mc_ia_v6 import BotMCIAv6, FICHIER_V6_RESEAU
from detective_v5 import imaginer_v5
from montecarlo import belote_imaginee, contrat_reussi


class BotMCIAv7(BotMCIAv6):
    nom = "Bot-MC-IA v7 (Det v5 + Réseau V2 + MC 40s)"

    def jouer_carte(self, main, jouables, pli, contrat, joueur, regles):
        if len(jouables) == 1:
            return jouables[0]

        # Étage 1 : Plis 1 à 3 en IA V2 pure
        if len(self.historique) < 12:
            self.ia_v2.historique = list(self.historique)
            self.ia_v2.encheres = list(self.encheres) if self.encheres else []
            self.ia_v2.belote_declaree = self.belote_declaree
            return self.ia_v2.jouer_carte(main, jouables, pli, contrat, joueur, regles)

        # Étage 2 : Plis 4 à 8 en Monte-Carlo 40 simulations avec le VRAI Détective v5 !
        atout = contrat["atout"]
        eq, attaque = joueur % 2, contrat["joueur"] % 2

        # APPEL DIRECT ET RÉEL À imaginer_v5 :
        mains_echantillons = [
            imaginer_v5(main, joueur, self.historique, self.encheres, atout, regles)
            for _ in range(self.nb_simulations)
        ]

        scores = {c: 0.0 for c in jouables}
        for m_sim in mains_echantillons:
            bel = belote_imaginee(m_sim, self.historique, atout)
            for c in jouables:
                pts_totaux, plis_totaux = self.simuler_avec_ia_v2(m_sim, pli, atout, contrat, joueur, c, regles)
                reussi = contrat_reussi(contrat, pts_totaux[attaque], plis_totaux[attaque],
                                        bel == attaque, regles)
                gagne = reussi if eq == attaque else not reussi
                score_coup = (1000.0 if gagne else -1000.0) + (pts_totaux[eq] - pts_totaux[1 - eq])
                scores[c] += score_coup

        return max(jouables, key=scores.get)
