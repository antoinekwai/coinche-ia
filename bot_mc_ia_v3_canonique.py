"""
bot_mc_ia_v3_canonique.py
BotMCIAv3 avec arbitrage déterministe sur cartes équivalentes :
- Si la carte choisie par Monte-Carlo fait partie d'une séquence maîtresse en main,
  et qu'une autre carte de la même séquence a un score quasi-identique (bruit MC <= 2.0 pts) :
  * Si le pli va à notre camp (ou défausse garantie en attaque) -> jouer la plus HAUTE (convention As-10)
  * Si le pli est perdu en défense -> jouer la plus BASSE (économiser 1 point)
Hérite de BotMCIAv3 (utilise le détective v3 par rejeu des enchères).
"""
import bot_mc_ia
from bot_mc_ia_v3 import BotMCIAv3
from detective_v3 import imaginer_v3
from ia_joueur import cartes_sont_equivalentes_rapide
from moteur import gagnant_pli


class BotMCIAv3Canonique(BotMCIAv3):
    nom = "Bot-MC-IA v3 (Canonique)"
    seuil_bruit_mc = 2.0  # écart de score en-dessous duquel deux cartes sont considérées à égalité

    def jouer_carte(self, main, jouables, pli, contrat, joueur, regles):
        if len(jouables) == 1:
            return jouables[0]

        ancien = bot_mc_ia.imaginer_donnes_contraintes
        bot_mc_ia.imaginer_donnes_contraintes = imaginer_v3
        try:
            return self._jouer_carte_canonique(main, jouables, pli, contrat, joueur, regles)
        finally:
            bot_mc_ia.imaginer_donnes_contraintes = ancien

    def _jouer_carte_canonique(self, main, jouables, pli, contrat, joueur, regles):
        atout = contrat["atout"]
        eq, attaque = joueur % 2, contrat["joueur"] % 2

        # 1. Tirage v3 standard (20 simulations)
        mains_echantillons = []
        for _ in range(self.nb_simulations):
            m = imaginer_v3(main, joueur, self.historique, self.encheres, atout, regles)
            mains_echantillons.append(m)

        # 2. Évaluation Monte-Carlo
        scores = {c: 0.0 for c in jouables}
        for m_sim in mains_echantillons:
            for c in jouables:
                pts_totaux, plis_totaux = self.simuler_avec_ia(m_sim, pli, atout, contrat, joueur, c, regles)
                from montecarlo import belote_imaginee, contrat_reussi
                bel = belote_imaginee(m_sim, self.historique, atout)
                reussi = contrat_reussi(contrat, pts_totaux[attaque], plis_totaux[attaque],
                                        bel == attaque, regles)
                gagne = reussi if eq == attaque else not reussi
                score_coup = (1000.0 if gagne else -1000.0) + (pts_totaux[eq] - pts_totaux[1 - eq])
                scores[c] += score_coup

        # Carte préférée brute
        c_top = max(jouables, key=scores.get)
        score_top = scores[c_top]

        # 3. Arbitrage déterministe sur cartes maîtresses équivalentes
        equivs = [c for c in jouables
                  if cartes_sont_equivalentes_rapide(c, c_top, main, pli, atout, self.historique)
                  and abs(scores[c] - score_top) <= self.seuil_bruit_mc * self.nb_simulations]

        if len(equivs) <= 1:
            return c_top

        # Déterminer si le pli est pour notre camp ou pour l'adversaire
        pli_pour_nous = False
        if pli:
            gagnant_actuel = gagnant_pli(pli, atout)[0]
            pli_pour_nous = (gagnant_actuel % 2 == eq)

        ordre_haut = (["V", "9", "A", "10", "R", "D", "8", "7"] if c_top[1] == atout
                      else ["A", "10", "R", "D", "V", "9", "8", "7"])

        # Si le pli est pour nous (ou en attaque) : convention -> la plus HAUTE
        # Si le pli est perdu : économie de points -> la plus BASSE
        if pli_pour_nous or (eq == attaque):
            equivs.sort(key=lambda c: ordre_haut.index(c[0]))
        else:
            equivs.sort(key=lambda c: ordre_haut.index(c[0]), reverse=True)

        return equivs[0]
