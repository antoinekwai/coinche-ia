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
from generateur_contraintes import imaginer_donnes_contraintes


class BotMCIA(MCEncheres, SysV2):
    """
    Candidat 2 : Monte Carlo Enchères dont les donnes virtuelles
    sont jouées par notre réseau de neurones aux 4 places.
    """
    nom = "Bot-MC-IA"
    nb_simulations = 20  # 20 donnes complètes jouées par l'IA par décision

    def simuler_avec_ia(self, mains_virtuelles, pli_actuel, atout, contrat, joueur, carte, regles):
        """Déroule la fin de la donne jusqu'au Pli 8 avec le réseau de neurones."""
        reseau = charger(FICHIER)
        m = [list(main_p) for main_p in mains_virtuelles]
        m[joueur].remove(carte)
        pli = list(pli_actuel) + [(joueur, carte)]
        hist = list(self.historique) + [(joueur, carte)]
        
        # Contexte initial
        pts_faits, plis_faits = bilan_passe(self.historique, atout)
        pts_eq = list(pts_faits)
        plis_eq = list(plis_faits)
        
        premier = (joueur - len(pli_actuel)) % 4
        prochain = (joueur + 1) % 4
        
        while len(hist) < 32:
            # Finir le pli en cours
            while len(pli) < 4:
                j = prochain
                jouables = cartes_jouables(m[j], pli, atout, j, regles)
                if len(jouables) == 1:
                    c_choisie = jouables[0]
                else:
                    s = encoder_situation(m[j], pli, hist, contrat, j, regles, self.encheres)
                    vec_c = np.stack([encoder_carte(c, atout) for c in jouables])
                    x_in = np.concatenate([np.repeat(s[None, :], len(jouables), axis=0), vec_c], axis=1)
                    with torch.no_grad():
                        notes = reseau(torch.from_numpy(x_in)).squeeze(1).numpy()
                    c_choisie = jouables[int(notes.argmax())]

                m[j].remove(c_choisie)
                pli.append((j, c_choisie))
                hist.append((j, c_choisie))
                prochain = (j + 1) % 4

            # Bilan du pli terminé
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

        # 1. Tirage de donnes sous contraintes couplées (toutes couleurs annoncées)
        mains_echantillons = []
        for _ in range(self.nb_simulations):
            m = imaginer_donnes_contraintes(main, joueur, self.historique, self.encheres, atout, regles)
            mains_echantillons.append(m)


        # 2. Évaluation de chaque carte par simulation IA
        scores_cartes = {c: 0.0 for c in jouables}
        
        for m_sim in mains_echantillons:
            bel = belote_imaginee(m_sim, self.historique, atout)
            for c in jouables:
                pts_totaux, plis_totaux = self.simuler_avec_ia(m_sim, pli, atout, contrat, joueur, c, regles)
                
                reussi = contrat_reussi(contrat, pts_totaux[attaque], plis_totaux[attaque], 
                                        bel == attaque, regles)
                gagne = reussi if eq == attaque else not reussi
                
                # Formule d'espérance : priorité absolue au contrat, points pour départager
                score_coup = (1000.0 if gagne else -1000.0) + (pts_totaux[eq] - pts_totaux[1 - eq])
                scores_cartes[c] += score_coup

        return max(jouables, key=scores_cartes.get)
