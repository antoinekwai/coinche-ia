import random
import numpy as np
import torch
from regles import REGLES_STANDARD
from moteur import cartes_jouables, gagnant_pli, points
from montecarlo import manques, belote_imaginee, contrat_reussi, bilan_passe
from test_mc_encheres import MCEncheres
from systeme_v2 import SysV2
from ia_joueur import JoueurIA, charger, FICHIER, cartes_sont_equivalentes_rapide
from ia_encodage import encoder_situation, encoder_carte

DELTA_SCORE_ADVERSAIRE = 0.12  # L'adversaire n'explore une 2e carte que si elle est à moins de 0.12 de sa meilleure

class BotCandidat3Vrai(MCEncheres, SysV2):
    """
    VRAI Candidat 3 : Monte Carlo 20 donnes avec Arborescence Minimax Réelle
    sur l'adversaire (élagage des équivalences + filtre delta-score).
    """
    nom = "Bot-Candidat3-Vrai"
    nb_simulations = 20

    def filtrer_ripostes_adverses(self, main_p, jouables, pli, hist, contrat, p, atout):
        """Filtre les cartes équivalentes et ne retient que les ripostes crédibles (delta-score)."""
        if len(jouables) <= 1:
            return jouables

        # 1. Éliminer les cartes strictement équivalentes en main
        candidats_uniques = []
        for c in jouables:
            if not any(cartes_sont_equivalentes_rapide(c, unique, main_p, pli, atout, hist) for unique in candidats_uniques):
                candidats_uniques.append(c)

        if len(candidats_uniques) <= 1:
            return candidats_uniques

        # 2. Évaluation rapide des cartes uniques par le réseau
        reseau = charger(FICHIER)
        s = encoder_situation(main_p, pli, hist, contrat, p, REGLES_STANDARD, self.encheres)
        vec_c = np.stack([encoder_carte(c, atout) for c in candidats_uniques])
        x_in = np.concatenate([np.repeat(s[None, :], len(candidats_uniques), axis=0), vec_c], axis=1)
        with torch.no_grad():
            notes = reseau(torch.from_numpy(x_in)).squeeze(1).numpy()

        meilleure_note = float(notes.max())
        
        # 3. Ne retenir que les cartes très proches de la meilleure (delta-score)
        ripostes = []
        for c, n in zip(candidats_uniques, notes):
            if (meilleure_note - n) <= DELTA_SCORE_ADVERSAIRE:
                ripostes.append(c)
        
        # Sécurité : maximum 2 branches pour garantir la vitesse
        if len(ripostes) > 2:
            ordre_idx = np.argsort(notes)[-2:]
            ripostes = [candidats_uniques[i] for i in ordre_idx]

        return ripostes

    def derouler_suite_ia(self, m, atout, contrat, premier, hist, pts_eq, plis_eq, regles):
        """Déroule les plis restants en ligne droite avec l'IA (ultra-rapide)."""
        reseau = charger(FICHIER)
        prochain = premier
        pli = []

        while len(hist) < 32:
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

            gagnant, _ = gagnant_pli(pli, atout)
            pts = sum(points(c, atout) for _, c in pli)
            if len(hist) == 32:
                pts += regles["dix_de_der"]

            eq = gagnant % 2
            pts_eq[eq] += pts
            plis_eq[eq] += 1
            pli = []
            prochain = gagnant

        return pts_eq, plis_eq

    def evaluer_arbre_pli(self, m, pli, hist, pts_eq, plis_eq, atout, contrat, prochain, joueur_bot, regles):
        """Arborescence Minimax sur le pli en cours : l'adversaire cherche le pire pour le bot."""
        equipe_bot = joueur_bot % 2
        attaque = contrat["joueur"] % 2

        # Pli terminé : dérouler la suite de la donne
        if len(pli) == 4:
            gagnant, _ = gagnant_pli(pli, atout)
            pts = sum(points(c, atout) for _, c in pli)
            if len(hist) == 32:
                pts += regles["dix_de_der"]

            pts_copie = list(pts_eq)
            plis_copie = list(plis_eq)
            pts_copie[gagnant % 2] += pts
            plis_copie[gagnant % 2] += 1

            # Finir les plis restants avec l'IA
            m_copie = [list(main_p) for main_p in m]
            pts_fin, plis_fin = self.derouler_suite_ia(
                m_copie, atout, contrat, gagnant, list(hist), pts_copie, plis_copie, regles
            )

            # Évaluation du résultat du point de vue de l'équipe du bot
            reussi = contrat_reussi(contrat, pts_fin[attaque], plis_fin[attaque], False, regles)
            gagne_bot = reussi if (equipe_bot == attaque) else not reussi
            return (1000.0 if gagne_bot else -1000.0) + (pts_fin[equipe_bot] - pts_fin[1 - equipe_bot])

        # Joueur suivant sur le pli
        j = prochain
        jouables = cartes_jouables(m[j], pli, atout, j, regles)
        est_partenaire = (j % 2 == equipe_bot)

        if est_partenaire:
            # Le partenaire calcule aussi : il teste ses ripostes crédibles et choisit le MEILLEUR coup pour l'équipe (MAX)
            candidats = self.filtrer_ripostes_adverses(m[j], jouables, pli, hist, contrat, j, atout)
            
            meilleur_score_pour_bot = -999999.0
            for c_part in candidats:
                m_suiv = [list(p) for p in m]
                m_suiv[j].remove(c_part)
                pli_suiv = list(pli) + [(j, c_part)]
                hist_suiv = list(hist) + [(j, c_part)]
                
                score_branche = self.evaluer_arbre_pli(
                    m_suiv, pli_suiv, hist_suiv, pts_eq, plis_eq, atout, contrat, (j + 1) % 4, joueur_bot, regles
                )
                if score_branche > meilleur_score_pour_bot:
                    meilleur_score_pour_bot = score_branche

            return meilleur_score_pour_bot
        else:
            # C'est un ADVERSAIRE : Minimax réel sur ses 1 ou 2 ripostes crédibles
            ripostes = self.filtrer_ripostes_adverses(m[j], jouables, pli, hist, contrat, j, atout)
            
            pire_score_pour_bot = 999999.0
            for c_adv in ripostes:
                m_suiv = [list(p) for p in m]
                m_suiv[j].remove(c_adv)
                pli_suiv = list(pli) + [(j, c_adv)]
                hist_suiv = list(hist) + [(j, c_adv)]
                
                score_branche = self.evaluer_arbre_pli(
                    m_suiv, pli_suiv, hist_suiv, pts_eq, plis_eq, atout, contrat, (j + 1) % 4, joueur_bot, regles
                )
                # L'adversaire choisit la carte qui MINIMISE les chances du bot !
                if score_branche < pire_score_pour_bot:
                    pire_score_pour_bot = score_branche

            return pire_score_pour_bot

    def jouer_carte(self, main, jouables, pli, contrat, joueur, regles):
        if len(jouables) == 1:
            return jouables[0]

        atout = contrat["atout"]
        manque = manques(self.historique, atout, regles)
        pts_faits, plis_faits = bilan_passe(self.historique, atout)

        # 1. 20 donnes cohérentes compatibles avec les enchères
        mains_echantillons = []
        for _ in range(40):
            m = self.imaginer(main, joueur, manque, atout)
            mains_echantillons.append(m)
            if len(mains_echantillons) == self.nb_simulations:
                break

        # 2. Évaluation de chaque carte du bot face à l'arbre de riposte adverse
        scores_cartes = {c: 0.0 for c in jouables}

        for c in jouables:
            total_c = 0.0
            for m_sim in mains_echantillons:
                m_depart = [list(p) for p in m_sim]
                m_depart[joueur].remove(c)
                pli_init = list(pli) + [(joueur, c)]
                hist_init = list(self.historique) + [(joueur, c)]
                
                score_arbre = self.evaluer_arbre_pli(
                    m_depart, pli_init, hist_init, list(pts_faits), list(plis_faits), 
                    atout, contrat, (joueur + 1) % 4, joueur, regles
                )
                total_c += score_arbre
            scores_cartes[c] = total_c / len(mains_echantillons)

        return max(jouables, key=scores_cartes.get)
