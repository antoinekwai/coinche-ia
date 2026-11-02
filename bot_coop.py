import random
import numpy as np
import torch
from regles import REGLES_STANDARD
from moteur import cartes_jouables, gagnant_pli, points
from montecarlo import manques, belote_imaginee, contrat_reussi, bilan_passe
from systeme_v2 import SysV2
from bot_mc_ia import BotMCIA
from ia_joueur import charger, FICHIER
from ia_encodage import encoder_situation, encoder_carte

def analyser_signal_defausse(carte, main, atout):
    """Identifie si une carte défaussée constitue un appel conventionnel."""
    r, coul = carte
    if coul == atout:
        return None
    # 1. As défaussé avec le 10 en main -> Appel franc au 10
    if r == "A" and ("10", coul) in main:
        return ("appel_10", coul)
    # 2. Petite carte défaussée avec l'As en main -> Appel à l'As
    if r in ("7", "8", "9", "D", "R") and ("A", coul) in main:
        return ("appel_as", coul)
    # 3. 10 défaussé sans l'As -> Rejet
    if r == "10" and ("A", coul) not in main:
        return ("rejet", coul)
    return None

class BotCoop(BotMCIA):
    """
    Champion d'élite avec communication bidirectionnelle complète :
    1. Signaux par défausse (As = 10 derrière, petite = As, 10 = rejet).
    2. Convention de singlette en défense à l'entame avec retour pour la coupe.
    """
    nom = "Bot-Coop"
    nb_simulations = 20

    def identifier_singlette_entame(self, main, atout):
        """Retourne la couleur de singlette hors-atout si elle existe (différente d'un As)."""
        cotes = [c for c in ["♠", "♥", "♦", "♣"] if c != atout]
        for c in cotes:
            cartes_coul = [x for x in main if x[1] == c]
            if len(cartes_coul) == 1 and cartes_coul[0][0] != "A":
                return c
        return None

    def imaginer_avec_signaux(self, main, joueur, manque, atout, contrat):
        """Tirage bayésien intégrant les défausses ET l'entame de singlette en défense."""
        partenaire = (joueur + 2) % 4
        defense = (joueur % 2 != contrat["joueur"] % 2)
        
        # 1. Lire les signaux de défausse du partenaire (CONDITIONNÉS AUX ENCHÈRES)
        appels_partenaire = []
        
        # Le partenaire a-t-il promis du jeu / des As aux enchères ?
        annonces_partenaire = [d for j, d in self.encheres if j == partenaire and isinstance(d, tuple)]
        partenaire_a_promis_du_jeu = len(annonces_partenaire) > 0

        for i, (j, (r, c)) in enumerate(self.historique):
            if j == partenaire and i % 4 != 0:
                pli_deb = i - (i % 4)
                couleur_demandee = self.historique[pli_deb][1][1]
                if c != couleur_demandee and c != atout:
                    # Cas A : As défaussé -> promet le 10 (inconditionnel)
                    if r == "A":
                        appels_partenaire.append(("10", c))
                    # Cas B : Petite carte -> n'est un appel d'As QUE SI le partenaire a parlé aux enchères !
                    elif r in ("7", "8", "9") and partenaire_a_promis_du_jeu:
                        appels_partenaire.append(("A", c))


        # 2. Détecter si le partenaire a entamé le Pli 1 en défense (singlette potentielle)
        couleur_singlette_partenaire = None
        if defense and len(self.historique) >= 4:
            premier_joueur, (prem_r, prem_c) = self.historique[0]
            if premier_joueur == partenaire and prem_c != atout and prem_r != "A":
                couleur_singlette_partenaire = prem_c

        # 3. Tirage initial compatible avec les enchères
        m = self.imaginer(main, joueur, manque, atout)

        # 4. Ajustement bayésien des défausses (placer la carte maîtresse chez le partenaire à 85%)
        adversaires = [(joueur + 1) % 4, (joueur + 3) % 4]
        for carte_cible in appels_partenaire:
            if random.random() < 0.85:
                jouees = {c for _, c in self.historique}
                if carte_cible not in jouees and carte_cible not in main and carte_cible not in m[partenaire]:
                    for adv in adversaires:
                        if carte_cible in m[adv]:
                            echanges = [c for c in m[partenaire] if c[1] not in manque[adv] and c != carte_cible]
                            if echanges:
                                c_ech = random.choice(echanges)
                                m[adv].remove(carte_cible)
                                m[partenaire].remove(c_ech)
                                m[adv].append(c_ech)
                                m[partenaire].append(carte_cible)
                            break

        # 5. Ajustement bayésien de la singlette : s'assurer que le partenaire n'a plus de cette couleur (80%)
        if couleur_singlette_partenaire and random.random() < 0.80:
            cartes_en_trop = [c for c in m[partenaire] if c[1] == couleur_singlette_partenaire]
            for c_trop in cartes_en_trop:
                for adv in adversaires:
                    echanges_adv = [c for c in m[adv] if c[1] != couleur_singlette_partenaire and c[1] not in manque[partenaire]]
                    if echanges_adv:
                        c_ech = random.choice(echanges_adv)
                        m[partenaire].remove(c_trop)
                        m[adv].remove(c_ech)
                        m[partenaire].append(c_ech)
                        m[adv].append(c_trop)
                        break

        return m

    def simuler_avec_cooperation(self, mains_virtuelles, pli_actuel, atout, contrat, joueur, carte, signal_emis, singlette_emise, regles):
        """Déroule la donne en modélisant la réaction coopérative du partenaire."""
        reseau = charger(FICHIER)
        m = [list(main_p) for main_p in mains_virtuelles]
        m[joueur].remove(carte)
        pli = list(pli_actuel) + [(joueur, carte)]
        hist = list(self.historique) + [(joueur, carte)]
        
        pts_faits, plis_faits = bilan_passe(self.historique, atout)
        pts_eq = list(pts_faits)
        plis_eq = list(plis_faits)
        
        partenaire = (joueur + 2) % 4
        prochain = (joueur + 1) % 4
        couleur_appelee = signal_emis[1] if signal_emis else singlette_emise

        while len(hist) < 32:
            while len(pli) < 4:
                j = prochain
                jouables = cartes_jouables(m[j], pli, atout, j, regles)
                
                # Réaction coopérative du partenaire : s'il prend la main à l'entame d'un pli
                if not pli and j == partenaire and couleur_appelee:
                    retour = [c for c in jouables if c[1] == couleur_appelee]
                    if retour:
                        c_choisie = retour[0]
                        couleur_appelee = None # Appel consommé
                    else:
                        c_choisie = jouables[0]
                elif len(jouables) == 1:
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
        defense = (eq != attaque)
        manque = manques(self.historique, atout, regles)

        # 1. Échantillonnage bayésien (avec défausses et singlettes)
        mains_echantillons = []
        for _ in range(35):
            m = self.imaginer_avec_signaux(main, joueur, manque, atout, contrat)
            mains_echantillons.append(m)
            if len(mains_echantillons) == self.nb_simulations:
                break

        # 2. Détection de contexte
        couleur_demandee = pli[0][1][1] if pli else None
        est_defausse = (pli and couleur_demandee != atout and not any(c[1] == couleur_demandee for c in main))
        est_entame_defense = (not pli and defense and len(self.historique) == 0)
        coul_singlette = self.identifier_singlette_entame(main, atout) if est_entame_defense else None

        scores_cartes = {c: 0.0 for c in jouables}

        for m_sim in mains_echantillons:
            bel = belote_imaginee(m_sim, self.historique, atout)
            for c in jouables:
                signal = analyser_signal_defausse(c, main, atout) if est_defausse else None
                # Si c'est l'entame de singlette en défense, transmettre l'information de retour
                singlette_jouee = coul_singlette if (est_entame_defense and c[1] == coul_singlette) else None

                pts_tot, plis_tot = self.simuler_avec_cooperation(
                    m_sim, pli, atout, contrat, joueur, c, signal, singlette_jouee, regles
                )
                
                reussi = contrat_reussi(contrat, pts_tot[attaque], plis_tot[attaque], bel == attaque, regles)
                gagne = reussi if eq == attaque else not reussi
                score_coup = (1000.0 if gagne else -1000.0) + (pts_tot[eq] - pts_tot[1 - eq])
                scores_cartes[c] += score_coup

        return max(jouables, key=scores_cartes.get)
