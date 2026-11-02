import time
import numpy as np
import torch
from regles import REGLES_STANDARD
from moteur import cartes_jouables, gagnant_pli, points
from montecarlo import manques, belote_imaginee, contrat_reussi, bilan_passe
from test_mc_encheres import MCEncheres
from systeme_v2 import SysV2
from solveur_exact import SolveurExact
from ia_joueur import charger, FICHIER
from ia_encodage import encoder_situation, encoder_carte

class BotMinimax(MCEncheres, SysV2):
    """
    Super Joueur : Monte Carlo Enchères résolu par Minimax Double Dummy.
    Simule la riposte adverse parfaite cartes ouvertes.
    """
    nom = "Bot-Minimax"
    nb_donnes_minimax = 8  # 8 donnes résolues exactement par coup

    def evaluer_carte_double_dummy(self, mains_virtuelles, pli_actuel, atout, contrat, joueur, carte, regles):
        """Résout la donne exacte après avoir posé `carte` face au jeu parfait."""
        m = [list(main_p) for main_p in mains_virtuelles]
        m[joueur].remove(carte)
        pli = list(pli_actuel) + [(joueur, carte)]
        
        # 1. Si le pli actuel est incomplet, le faire terminer de façon exacte
        solveur = SolveurExact(atout, regles)
        
        # Score obtenu avec Minimax complet jusqu'à la fin de la donne (Pli 8)
        # minimax() renvoie les points nets de Sud/Nord (0/2) - (1/3)
        score_net_02 = solveur.minimax(m, pli, (joueur - len(pli_actuel)) % 4, -999, 999)
        
        equipe = joueur % 2
        # Score pour notre équipe
        score_equipe = score_net_02 if equipe == 0 else -score_net_02
        return score_equipe

    def jouer_carte(self, main, jouables, pli, contrat, joueur, regles):
        if len(jouables) == 1:
            return jouables[0]

        atout = contrat["atout"]
        manque = manques(self.historique, atout, regles)

        # 1. Tirage de donnes cohérentes avec les enchères
        mains_echantillons = []
        for _ in range(30):
            m = self.imaginer(main, joueur, manque, atout)
            mains_echantillons.append(m)
            if len(mains_echantillons) == self.nb_donnes_minimax:
                break

        # 2. Présélection rapide au Pli 1 et 2 si trop de cartes pour garder la fluidité
        cartes_a_tester = jouables
        if len(self.historique) < 8 and len(jouables) > 3:
            # Le réseau pré-sélectionne les 3 meilleures cartes pour le solveur
            s = encoder_situation(main, pli, self.historique, contrat, joueur, regles, self.encheres)
            vec_cartes = np.stack([encoder_carte(c, atout) for c in jouables])
            x_in = np.concatenate([np.repeat(s[None, :], len(jouables), axis=0), vec_cartes], axis=1)
            with torch.no_grad():
                notes = charger(FICHIER)(torch.from_numpy(x_in)).squeeze(1).numpy()
            top_indices = np.argsort(notes)[-3:]
            cartes_a_tester = [jouables[i] for i in top_indices]

        # 3. Résolution exacte Double Dummy
        scores_moyens = {c: 0.0 for c in cartes_a_tester}
        
        for c in cartes_a_tester:
            total_net = 0.0
            for m in mains_echantillons:
                total_net += self.evaluer_carte_double_dummy(m, pli, atout, contrat, joueur, c, regles)
            scores_moyens[c] = total_net / len(mains_echantillons)

        return max(cartes_a_tester, key=scores_moyens.get)
