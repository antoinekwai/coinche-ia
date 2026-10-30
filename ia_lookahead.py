import random
import numpy as np
import torch
from regles import REGLES_STANDARD
from moteur import cartes_jouables, gagnant_pli, points
from montecarlo import manques, imaginer_mains
from dispute import coherent
from systeme_v2 import SysV2
from ia_joueur import JoueurIA, charger, FICHIER
from ia_encodage import encoder_situation, encoder_carte

class JoueurLookahead(SysV2, JoueurIA):
    """IA guidée par anticipation tactique à 1 pli (Lookahead)."""
    nom = "IA-Lookahead"
    nb_echantillons = 10   # 10 donnes crédibles imaginées par coup

    def tirer_mains_plausibles(self, main, joueur, atout, regles):
        """Tire des répartitions compatibles avec les coupes et les enchères."""
        autres = [p for p in range(4) if p != joueur]
        jouees = {p: [c for j, c in self.historique if j == p] for p in autres}
        manque = manques(self.historique, atout, regles)
        echantillons = []
        
        for _ in range(40):
            m = imaginer_mains(main, joueur, self.historique, manque)
            # Vérification de cohérence avec les enchères
            if all(coherent(m[p] + jouees[p], p, self.encheres) for p in autres):
                echantillons.append(m)
                if len(echantillons) == self.nb_echantillons:
                    break
        
        # Secours si les enchères sont trop strictes
        while len(echantillons) < self.nb_echantillons:
            echantillons.append(imaginer_mains(main, joueur, self.historique, manque))
        return echantillons

    def simuler_fin_pli(self, mains_virtuelles, pli_actuel, atout, contrat, joueur, carte, regles):
        """Déroule la fin du pli en cours et évalue la position d'arrivée."""
        reseau = charger(self.fichier)
        m = [list(main_p) for main_p in mains_virtuelles]
        m[joueur].remove(carte)
        pli = list(pli_actuel) + [(joueur, carte)]
        hist = list(self.historique) + [(joueur, carte)]
        
        prochain = (joueur + 1) % 4
        while len(pli) < 4:
            jouables = cartes_jouables(m[prochain], pli, atout, prochain, regles)
            if len(jouables) == 1:
                c_suivante = jouables[0]
            else:
                s_suivante = encoder_situation(m[prochain], pli, hist, contrat, prochain, regles, self.encheres)
                vec_cartes = np.stack([encoder_carte(c, atout) for c in jouables])
                x_in = np.concatenate([np.repeat(s_suivante[None, :], len(jouables), axis=0), vec_cartes], axis=1)
                with torch.no_grad():
                    scores = reseau(torch.from_numpy(x_in)).squeeze(1).numpy()
                c_suivante = jouables[int(scores.argmax())]

            m[prochain].remove(c_suivante)
            pli.append((prochain, c_suivante))
            hist.append((prochain, c_suivante))
            prochain = (prochain + 1) % 4

        # Bilan du pli terminé
        gagnant, c_gagnante = gagnant_pli(pli, atout)
        pts_pli = sum(points(c, atout) for _, c in pli)
        if len(hist) == 32: # Dernier pli
            pts_pli += regles["dix_de_der"]

        equipe = joueur % 2
        gain_pli = (pts_pli if gagnant % 2 == equipe else -pts_pli) / 162.0

        # Évaluation de l'avenir si la donne continue
        gain_futur = 0.0
        if len(hist) < 32:
            jouables_futur = cartes_jouables(m[gagnant], [], atout, gagnant, regles)
            s_futur = encoder_situation(m[gagnant], [], hist, contrat, gagnant, regles, self.encheres)
            vec_c_futur = np.stack([encoder_carte(c, atout) for c in jouables_futur])
            x_futur = np.concatenate([np.repeat(s_futur[None, :], len(jouables_futur), axis=0), vec_c_futur], axis=1)
            with torch.no_grad():
                val_futur = reseau(torch.from_numpy(x_futur)).squeeze(1).numpy()
            
            # La valeur d'avenir du point de vue de notre équipe
            meilleure_val = float(val_futur.max())
            gain_futur = meilleure_val if gagnant % 2 == equipe else -meilleure_val

        return gain_pli + gain_futur

    def jouer_carte(self, main, jouables, pli, contrat, joueur, regles):
        if len(jouables) == 1:
            return jouables[0]

        atout = contrat["atout"]
        mains_echantillons = self.tirer_mains_plausibles(main, joueur, atout, regles)

        scores_moyens = {c: 0.0 for c in jouables}
        for c in jouables:
            total = 0.0
            for m in mains_echantillons:
                total += self.simuler_fin_pli(m, pli, atout, contrat, joueur, c, regles)
            scores_moyens[c] = total / len(mains_echantillons)

        return max(jouables, key=scores_moyens.get)
