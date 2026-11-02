import random
import numpy as np
import torch
from regles import REGLES_STANDARD
from moteur import cartes_jouables, gagnant_pli, points
from montecarlo import manques, belote_imaginee, contrat_reussi, bilan_passe
from test_mc_encheres import MCEncheres
from systeme_v2 import SysV2
from ia_joueur import JoueurIA, charger, FICHIER
from ia_encodage import encoder_situation, encoder_carte

class BotCandidat3(MCEncheres, SysV2):
    """
    Candidat 3 : Monte Carlo Récursif avec Élagage par IA (Policy Pruning).
    L'adversaire calcule activement en choisissant parmi ses 2 meilleurs coups IA.
    """
    nom = "Bot-Candidat3"
    nb_simulations = 15
    top_k_adversaire = 2   # L'adversaire explore uniquement ses 2 meilleures cartes selon le réseau

    def selectionner_top_coups_ia(self, main_p, jouables, pli, hist, contrat, p, atout, k_top=2):
        """Utilise le réseau de neurones pour ne retenir que les K meilleures cartes candidates."""
        if len(jouables) <= k_top:
            return jouables
        reseau = charger(FICHIER)
        s = encoder_situation(main_p, pli, hist, contrat, p, REGLES_STANDARD, self.encheres)
        vec_c = np.stack([encoder_carte(c, atout) for c in jouables])
        x_in = np.concatenate([np.repeat(s[None, :], len(jouables), axis=0), vec_c], axis=1)
        with torch.no_grad():
            notes = reseau(torch.from_numpy(x_in)).squeeze(1).numpy()
        # Indices des K meilleures notes
        top_idx = np.argsort(notes)[-k_top:]
        return [jouables[i] for i in top_idx]

    def simuler_avec_riposte(self, mains_virtuelles, pli_actuel, atout, contrat, joueur, carte, regles):
        """Simule la fin de donne où chaque camp explore intelligemment."""
        m = [list(main_p) for main_p in mains_virtuelles]
        m[joueur].remove(carte)
        pli = list(pli_actuel) + [(joueur, carte)]
        hist = list(self.historique) + [(joueur, carte)]
        
        pts_faits, plis_faits = bilan_passe(self.historique, atout)
        pts_eq = list(pts_faits)
        plis_eq = list(plis_faits)
        
        prochain = (joueur + 1) % 4
        
        while len(hist) < 32:
            while len(pli) < 4:
                j = prochain
                jouables = cartes_jouables(m[j], pli, atout, j, regles)
                
                if len(jouables) == 1:
                    c_choisie = jouables[0]
                else:
                    # L'adversaire ou le partenaire filtre ses 2 meilleurs coups via l'IA
                    candidats = self.selectionner_top_coups_ia(
                        m[j], jouables, pli, hist, contrat, j, atout, k_top=self.top_k_adversaire
                    )
                    # Choix tactique rapide parmi ces 2 coups (carte la plus forte si maître, ou la plus basse)
                    c_choisie = candidats[-1] # La carte avec la meilleure note du réseau

                m[j].remove(c_choisie)
                pli.append((j, c_choisie))
                hist.append((j, c_choisie))
                prochain = (j + 1) % 4

            # Bilan du pli
            gagnant, _ = gagnant_pli(pli, atout)
            pts_pli = sum(points(c, atout) for _, c in pli)
            if len(hist) == 32:
                pts_pli += regles["dix_de_der"]

            eq_gagnant = gagnant % 2
            pts_eq[eq_gagnant] += pts_pli
            plis_eq[eq_gagnant] += 1
            pli = []
            prochain = gagnant

        return pts_eq, plis_eq

    def jouer_carte(self, main, jouables, pli, contrat, joueur, regles):
        if len(jouables) == 1:
            return jouables[0]

        atout = contrat["atout"]
        eq, attaque = joueur % 2, contrat["joueur"] % 2
        manque = manques(self.historique, atout, regles)

        # 1. Échantillonnage de donnes cohérentes
        mains_echantillons = []
        for _ in range(35):
            m = self.imaginer(main, joueur, manque, atout)
            mains_echantillons.append(m)
            if len(mains_echantillons) == self.nb_simulations:
                break

        # 2. Évaluation de chaque coup contre la riposte adverse élaguée
        scores_cartes = {c: 0.0 for c in jouables}
        
        for m_sim in mains_echantillons:
            bel = belote_imaginee(m_sim, self.historique, atout)
            for c in jouables:
                pts_tot, plis_tot = self.simuler_avec_riposte(m_sim, pli, atout, contrat, joueur, c, regles)
                reussi = contrat_reussi(contrat, pts_tot[attaque], plis_tot[attaque], bel == attaque, regles)
                gagne = reussi if eq == attaque else not reussi
                score_coup = (1000.0 if gagne else -1000.0) + (pts_tot[eq] - pts_tot[1 - eq])
                scores_cartes[c] += score_coup

        return max(jouables, key=scores_cartes.get)
