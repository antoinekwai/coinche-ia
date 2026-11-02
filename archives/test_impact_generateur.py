import sys
from regles import REGLES_STANDARD
from rapide import afficher_rapide
from bot_mc_ia import BotMCIA
from montecarlo import manques

class BotAncienGenerateur(BotMCIA):
    nom = "MC-IA (Ancien Générateur)"

    def jouer_carte(self, main, jouables, pli, contrat, joueur, regles):
        if len(jouables) == 1:
            return jouables[0]

        atout = contrat["atout"]
        eq, attaque = joueur % 2, contrat["joueur"] % 2
        manque = manques(self.historique, atout, regles)

        # Ancien tirage par rejet aléatoire
        mains_echantillons = []
        for _ in range(40):
            m = self.imaginer(main, joueur, manque, atout)
            mains_echantillons.append(m)
            if len(mains_echantillons) == self.nb_simulations:
                break

        scores_cartes = {c: 0.0 for c in jouables}
        for m_sim in mains_echantillons:
            from montecarlo import belote_imaginee, contrat_reussi
            bel = belote_imaginee(m_sim, self.historique, atout)
            for c in jouables:
                pts_totaux, plis_totaux = self.simuler_avec_ia(m_sim, pli, atout, contrat, joueur, c, regles)
                reussi = contrat_reussi(contrat, pts_totaux[attaque], plis_totaux[attaque], bel == attaque, regles)
                gagne = reussi if eq == attaque else not reussi
                score_coup = (1000.0 if gagne else -1000.0) + (pts_totaux[eq] - pts_totaux[1 - eq])
                scores_cartes[c] += score_coup

        return max(jouables, key=scores_cartes.get)

if __name__ == "__main__":
    nb = int(sys.argv[1]) if len(sys.argv) > 1 else 800
    regles = REGLES_STANDARD
    
    print("=" * 70)
    print(f"=== DUEL : Nouveau Générateur (Contraintes) vs Ancien ({nb} donnes) ===")
    print("Même moteur d'IA, seule la qualité des donnes imaginées diffère.")
    print("=" * 70 + "\n")
    
    afficher_rapide(BotMCIA, BotAncienGenerateur, nb, regles, graine=999111)
