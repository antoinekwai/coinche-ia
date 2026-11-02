import time
import random
import os
import multiprocessing as mp
import numpy as np
import torch
from regles import REGLES_STANDARD
from moteur import distribuer, cartes_jouables, gagnant_pli, points, equipe_belote, decompte
from partie import phase_annonces
from systeme_v2 import SysV2
from test_mc_encheres import MCEncheres
from ia_joueur import JoueurIA, charger, FICHIER
from ia_encodage import encoder_situation, encoder_carte
from joueurs import JoueurRegles
from solveur_exact import SolveurExact
from bot_mc_ia import BotMCIA
from bot_coop import BotCoop

NB_DONNES_NUIT = 400

class OracleJoueur:
    """Solveur omniscient cartes ouvertes (Double Dummy) : Attaque ou Défense."""
    def __init__(self, est_attaque):
        self.est_attaque = est_attaque

    def jouer_carte(self, mains_reelles, jouables, pli, contrat, joueur, historique, regles):
        if len(jouables) == 1:
            return jouables[0]

        atout = contrat["atout"]
        equipe = joueur % 2

        # Plis 1 et 2 : choix guidé par le réseau pour la vitesse
        if len(historique) < 8 and len(jouables) > 3:
            s = encoder_situation(mains_reelles[joueur], pli, historique, contrat, joueur, regles, [])
            vec_c = np.stack([encoder_carte(c, atout) for c in jouables])
            x_in = np.concatenate([np.repeat(s[None, :], len(jouables), axis=0), vec_c], axis=1)
            with torch.no_grad():
                notes = charger(FICHIER)(torch.from_numpy(x_in)).squeeze(1).numpy()
            return jouables[int(notes.argmax())]

        premier_du_pli = (joueur - len(pli)) % 4
        solveur = SolveurExact(atout, regles)

        meilleure_carte = jouables[0]
        meilleur_score = -9999

        for c in jouables:
            m_copie = [list(m) for m in mains_reelles]
            m_copie[joueur].remove(c)
            pli_v = list(pli) + [(joueur, c)]

            score_net_02 = solveur.minimax(m_copie, pli_v, premier_du_pli, -999, 999)
            score_mon_camp = score_net_02 if equipe == 0 else -score_net_02

            if score_mon_camp > meilleur_score:
                meilleur_score = score_mon_camp
                meilleure_carte = c

        return meilleure_carte

def simuler_une_table(mains_depart, contrat, donneur, regles, type_moteur, camp_teste):
    """
    camp_teste : 0 si Sud/Nord est le camp testé, 1 si Est/Ouest est testé.
    L'adversaire est TOUJOURS MC-Enchères.
    """
    atout = contrat["atout"]
    premier = (donneur + 1) % 4
    mains = [list(m) for m in mains_depart]

    # Bots
    bot_ref_adversaire = MCEncheres()
    oracle = OracleJoueur(est_attaque=(camp_teste == contrat["joueur"] % 2))
    bots = {
        "mcia": BotMCIA(),
        "mc_encheres": MCEncheres(),
        "coop": BotCoop(),
        "ia": JoueurIA(),
        "regles": JoueurRegles()
    }

    historique = []
    pts_eq = [0, 0]
    plis_eq = [0, 0]

    for num in range(1, 9):
        pli = []
        for i in range(4):
            j = (premier + i) % 4
            jouables = cartes_jouables(mains[j], pli, atout, j, regles)

            if j % 2 == camp_teste:
                # Camp testé
                if type_moteur == "oracle":
                    c = oracle.jouer_carte(mains, jouables, pli, contrat, j, historique, regles)
                else:
                    b = bots[type_moteur]
                    b.historique = list(historique)
                    b.encheres = []
                    c = b.jouer_carte(mains[j], jouables, pli, contrat, j, regles)
            else:
                # Adversaire de référence : TOUJOURS MC-Enchères
                bot_ref_adversaire.historique = list(historique)
                bot_ref_adversaire.encheres = []
                c = bot_ref_adversaire.jouer_carte(mains[j], jouables, pli, contrat, j, regles)

            mains[j].remove(c)
            pli.append((j, c))
            historique.append((j, c))

        gagnant, _ = gagnant_pli(pli, atout)
        eq = gagnant % 2
        pts = sum(points(c, atout) for _, c in pli)
        if num == 8: pts += regles["dix_de_der"]
        pts_eq[eq] += pts
        plis_eq[eq] += 1
        premier = gagnant

    belote = equipe_belote(mains_depart, atout)
    marque, reussi = decompte(contrat, pts_eq, plis_eq, belote, regles)
    
    # Pour le camp testé : points faits et si le résultat lui est favorable
    # (Attaque : réussi ; Défense : chuté)
    pts_faits = pts_eq[camp_teste]
    est_attaque = (camp_teste == contrat["joueur"] % 2)
    succes = reussi if est_attaque else (not reussi)
    
    return pts_faits, succes

def evaluer_donne_complete(graine):
    random.seed(graine)
    mains = distribuer()
    donneur = graine % 4
    regles = REGLES_STANDARD

    j_bids = [JoueurIA() for _ in range(4)]
    contrat = phase_annonces(mains, donneur, j_bids, regles, afficher=False)
    if contrat is None:
        return None

    # On teste le camp Sud/Nord (équipe 0)
    # Si contrat["joueur"] % 2 == 0 : l'équipe 0 est en ATTAQUE
    # Si contrat["joueur"] % 2 == 1 : l'équipe 0 est en DÉFENSE
    camp_teste = 0
    role = "attaque" if (contrat["joueur"] % 2 == 0) else "defense"

    moteurs = ["oracle", "mcia", "mc_encheres", "coop", "ia", "regles"]
    resultats = {"role": role, "valeur": contrat["valeur"]}

    for mot in moteurs:
        pts, ok = simuler_une_table(mains, contrat, donneur, regles, mot, camp_teste)
        resultats[f"{mot}_pts"] = pts
        resultats[f"{mot}_ok"] = ok

    return resultats

if __name__ == "__main__":
    regles = REGLES_STANDARD
    debut = time.time()
    print("=" * 80)
    print("🌙 LE GRAND BENCHMARK DE NUIT : ATTAQUE & DÉFENSE SYMÉTRIQUES")
    print("=" * 80)
    print(f"Évaluation sur {NB_DONNES_NUIT} donnes complètes...")
    print("Adversaire commun à toutes les tables : MC-Enchères (information cachée).\n")

    donnes_valides = []
    with mp.get_context("fork").Pool(os.cpu_count()) as pool:
        for k, res in enumerate(pool.imap_unordered(evaluer_donne_complete, range(1000000, 1000000 + NB_DONNES_NUIT * 2), chunksize=5)):
            if res is not None:
                donnes_valides.append(res)
                if len(donnes_valides) % 25 == 0:
                    ecoule = (time.time() - debut) / 60
                    print(f"  {len(donnes_valides):3d}/{NB_DONNES_NUIT} donnes résolues ({ecoule:.1f} min)...", flush=True)
                if len(donnes_valides) >= NB_DONNES_NUIT:
                    break

    # DÉPOUILLEMENT
    moteurs = ["oracle", "mcia", "mc_encheres", "coop", "ia", "regles"]
    noms = {
        "oracle": "1. Oracle (Plafond Absolu)",
        "mcia": "2. Bot-MC-IA (Champion Réseau)",
        "mc_encheres": "3. MC-Enchères (MCTS)",
        "coop": "4. Bot-Coop (Avec Signaux)",
        "ia": "5. Notre IA (Réseau Pur 11ms)",
        "regles": "6. Joueur À Règles (Amateur)"
    }

    donnes_att = [d for d in donnes_valides if d["role"] == "attaque"]
    donnes_def = [d for d in donnes_valides if d["role"] == "defense"]

    print("\n" + "=" * 80)
    print(f"RÉSULTATS GLOBAUX SUR {len(donnes_valides)} DONNES ({len(donnes_att)} Attaques, {len(donnes_def)} Défenses) :")
    print("=" * 80)
    print(f"{'Moteur de Jeu':<30} | {'Rend. Attaque':<14} | {'Rend. Défense':<14} | {'Rendement Global'}")
    print("-" * 80)

    # L'oracle définit le 100% en attaque et en défense
    max_pts_att = np.mean([d["oracle_pts"] for d in donnes_att])
    # En défense, l'oracle cherche à faire le MAXIMUM de points pour faire chuter
    max_pts_def = np.mean([d["oracle_pts"] for d in donnes_def])

    for mot in moteurs:
        pts_att = np.mean([d[f"{mot}_pts"] for d in donnes_att])
        pts_def = np.mean([d[f"{mot}_pts"] for d in donnes_def])
        
        rend_att = 100 * pts_att / max_pts_att
        rend_def = 100 * pts_def / max_pts_def
        rend_global = (rend_att + rend_def) / 2.0
        
        succes_att = sum(d[f"{mot}_ok"] for d in donnes_att)
        succes_def = sum(d[f"{mot}_ok"] for d in donnes_def)

        print(f"{noms[mot]:<30} | {rend_att:5.1f} % ({succes_att}/{len(donnes_att)}) | {rend_def:5.1f} % ({succes_def}/{len(donnes_def)}) | {rend_global:5.1f} %")

    print("=" * 80)
    print(f"Calcul terminé en {(time.time() - debut) / 60:.1f} minutes.")
