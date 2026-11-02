import time
import random
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
from bot_coop import BotCoop
from bot_mc_ia import BotMCIA


NB_DONNES_BENCHMARK = 100

class AttaquantOracle:
    """Attaquant omniscient : résout la donne exacte cartes ouvertes (Double Dummy)."""
    nom = "Oracle"

    def jouer_carte(self, mains_reelles, jouables, pli, contrat, joueur, historique, regles):
        if len(jouables) == 1:
            return jouables[0]

        atout = contrat["atout"]
        equipe = joueur % 2

        # Plis 1 et 2 : choix guidé par le réseau pour la fluidité
        if len(historique) < 8 and len(jouables) > 3:
            s = encoder_situation(mains_reelles[joueur], pli, historique, contrat, joueur, regles, [])
            vec_c = np.stack([encoder_carte(c, atout) for c in jouables])
            x_in = np.concatenate([np.repeat(s[None, :], len(jouables), axis=0), vec_c], axis=1)
            with torch.no_grad():
                notes = charger(FICHIER)(torch.from_numpy(x_in)).squeeze(1).numpy()
            return jouables[int(notes.argmax())]

        # Du Pli 3 au Pli 8 : Résolution exacte cartes ouvertes
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

def jouer_manche_benchmark(mains_depart, contrat, donneur, regles, type_att):
    atout = contrat["atout"]
    premier = (donneur + 1) % 4
    mains = [list(m) for m in mains_depart]

    # Défense commune : MC-Enchères sous information cachée
    bot_def = MCEncheres()
    oracle = AttaquantOracle()
    bot_mc_att = MCEncheres()
    bot_ia_att = JoueurIA()
    bot_mcia_pur = BotMCIA()
    bot_coop_att = BotCoop()
    bot_regles_att = JoueurRegles()

    historique = []
    pts_eq = [0, 0]
    plis_eq = [0, 0]

    for num in range(1, 9):
        pli = []
        for i in range(4):
            j = (premier + i) % 4
            jouables = cartes_jouables(mains[j], pli, atout, j, regles)

            if j % 2 == 0:  # ATTAQUE (Sud/Nord)
                if type_att == "oracle":
                    c = oracle.jouer_carte(mains, jouables, pli, contrat, j, historique, regles)
                elif type_att == "mc_encheres":
                    bot_mc_att.historique = list(historique)
                    bot_mc_att.encheres = []
                    c = bot_mc_att.jouer_carte(mains[j], jouables, pli, contrat, j, regles)
                elif type_att == "ia":
                    bot_ia_att.historique = list(historique)
                    bot_ia_att.encheres = []
                    c = bot_ia_att.jouer_carte(mains[j], jouables, pli, contrat, j, regles)
                elif type_att == "coop":
                    bot_coop_att.historique = list(historique)
                    bot_coop_att.encheres = []
                    c = bot_coop_att.jouer_carte(mains[j], jouables, pli, contrat, j, regles)
                elif type_att == "regles":
                    c = bot_regles_att.jouer_carte(mains[j], jouables, pli, contrat, j, regles)
                elif type_att == "mcia":
                    bot_mcia_pur.historique = list(historique)
                    bot_mcia_pur.encheres = []
                    c = bot_mcia_pur.jouer_carte(mains[j], jouables, pli, contrat, j, regles)

            else:  # DÉFENSE (MC-Enchères, information cachée)
                bot_def.historique = list(historique)
                bot_def.encheres = []
                c = bot_def.jouer_carte(mains[j], jouables, pli, contrat, j, regles)

            mains[j].remove(c)
            pli.append((j, c))
            historique.append((j, c))

        gagnant, _ = gagnant_pli(pli, atout)
        eq = gagnant % 2
        pts = sum(points(c, atout) for _, c in pli)
        if num == 8:
            pts += regles["dix_de_der"]
        pts_eq[eq] += pts
        plis_eq[eq] += 1
        premier = gagnant

    belote = equipe_belote(mains_depart, atout)
    marque, reussi = decompte(contrat, pts_eq, plis_eq, belote, regles)
    return pts_eq[0], reussi

def lancer_benchmark_complet():
    regles = REGLES_STANDARD
    print("=" * 75)
    print("🔬 ÉCHELLE ABSOLUE DU JEU DE LA CARTE (BENCHMARK ORACLE)")
    print("=" * 75)
    print("Défense commune : MC-Enchères (information cachée).")
    print("Les 5 attaquants jouent exactement les mêmes cartes contre la même défense :\n")
    print("  1. Oracle (Plafond absolu, cartes ouvertes)")
    print("  2. MC-Enchères (MCTS sous information cachée)")
    print("  3. Notre IA (Réseau de neurones instantané)")
    print("  4. Bot-Coop (Avec signaux conditionnés aux enchères)")
    print("  5. Joueur À Règles (Heuristique amateur)\n")


    donnes_traitees = 0
    types_att = ["oracle", "mcia", "mc_encheres", "coop", "ia", "regles"]
    scores = {k: [] for k in types_att}
    reussites = {k: 0 for k in types_att}


    debut = time.time()

    for num in range(NB_DONNES_BENCHMARK * 3):
        random.seed(666000 + num)
        mains = distribuer()
        donneur = num % 4

        j_bids = [JoueurIA() for _ in range(4)]
        contrat = phase_annonces(mains, donneur, j_bids, regles, afficher=False)
        if contrat is None or contrat["joueur"] % 2 != 0:
            continue

        donnes_traitees += 1

        for type_att in types_att:
            pts, ok = jouer_manche_benchmark(mains, contrat, donneur, regles, type_att)
            scores[type_att].append(pts)
            if ok:
                reussites[type_att] += 1

        if donnes_traitees % 20 == 0:
            ecoule = time.time() - debut
            print(f"  {donnes_traitees}/{NB_DONNES_BENCHMARK} donnes traitées ({ecoule/60:.1f} min)...")
        if donnes_traitees >= NB_DONNES_BENCHMARK:
            break

    pts_max = np.mean(scores["oracle"])
    print("\n" + "=" * 75)
    print(f"CLASSEMENT ABSOLU SUR {donnes_traitees} DONNES (POTENTIEL ORACLE = 100 %) :")
    print("=" * 75)
    titre_col = "Moteur d'Attaque"
    print(f"{titre_col:<30} | {'Pts Moyens':<12} | {'Rendement':<12} | {'Contrats Réussis'}")
    print("-" * 75)

    noms_propres = {
        "oracle": "1. Oracle (Plafond Absolu)",
        "mcia": "2. Bot-MC-IA (Champion Réseau)",
        "mc_encheres": "3. MC-Enchères (MCTS)",
        "coop": "4. Bot-Coop (Avec Signaux)",
        "ia": "5. Notre IA (Réseau Pur 11ms)",
        "regles": "6. Joueur À Règles (Amateur)"
    }


    for cle in types_att:
        moy = np.mean(scores[cle])
        rendement = 100 * moy / pts_max
        tx_reussite = 100 * reussites[cle] / donnes_traitees
        nom_aff = noms_propres[cle]
        print(f"{nom_aff:<30} | {moy:5.1f} / 162   | {rendement:5.1f} %      | {reussites[cle]}/{donnes_traitees} ({tx_reussite:.1f} %)")


if __name__ == "__main__":
    lancer_benchmark_complet()
