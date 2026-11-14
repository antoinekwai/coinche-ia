"""
autopsie_plis.py
Trouve le pli exact où le BotMCIAv3 commet l'erreur fatale par rapport à l'Oracle.
Sur 40 donnes d'attaque où Oracle gagne et v3 chute :
On laisse le v3 jouer jusqu'au pli K, puis le solveur parfait (minimax)
calcule si le contrat est ENCORE réalisable.
"""
import json
import random
import numpy as np
import torch
from regles import REGLES_STANDARD
from moteur import distribuer, cartes_jouables, gagnant_pli, points, equipe_belote, decompte, COULEURS
from solveur_exact import SolveurExact
from test_mc_encheres import MCEncheres
from bot_mc_ia_v3 import BotMCIAv3

FICHIER = "resultats_v4.jsonl"
NB_DONNES = 40

# Sélectionner des donnes d'attaque perdues par le v3
candidats = []
with open(FICHIER, encoding="utf-8") as f:
    for ligne in f:
        try:
            d = json.loads(ligne)
        except:
            continue
        if d.get("role") == "attaque" and d.get("oracle_ok") and not d.get("mcia_v3_ok"):
            candidats.append(d)
        if len(candidats) >= NB_DONNES:
            break

print(f"=== AUTOPSIE DU DÉCROCHAGE SUR {len(candidats)} DONNES D'ATTAQUE ===")
print("Objectif : trouver le premier pli où le contrat devient mathématiquement infaisable.")
print("-" * 72)

fatal_par_pli = {pli: 0 for pli in range(1, 9)}

for idx, d in enumerate(candidats, 1):
    graine = d["graine"]
    
    encheres_propres = []
    atout = "♠"
    valeur = d["valeur"]
    
    for item in d["encheres"]:
        j = item[0]
        act = item[1]
        if isinstance(act, list):
            act = tuple(act)
            if len(act) == 2 and act[1] in COULEURS:
                atout = act[1]
                valeur = act[0]
        encheres_propres.append((j, act))

    est_coinche = 1 if any(dec == "coinche" for _, dec in encheres_propres) else 0

    contrat = {
        "valeur": valeur,
        "atout": atout,
        "joueur": 0,
        "coinche": est_coinche,
        "capot": False
    }
    donneur = graine % 4

    # 1. Rejouer la partie complète avec le v3 pour enregistrer l'historique exact
    random.seed(graine)
    mains_init = distribuer()

    random.seed(graine * 10 + 7)
    np.random.seed((graine * 10 + 7) % (2**32))
    torch.manual_seed(graine * 10 + 7)

    mains_v3 = [list(m) for m in mains_init]
    bot = BotMCIAv3()
    adversaire = MCEncheres()
    premier = (donneur + 1) % 4
    historique_v3 = []

    while len(historique_v3) < 32:
        pli = []
        for k in range(4):
            j = (premier + k) % 4
            jouables = cartes_jouables(mains_v3[j], pli, atout, j, REGLES_STANDARD)
            if j % 2 == 0:
                bot.historique = list(historique_v3)
                bot.encheres = list(encheres_propres)
                c = bot.jouer_carte(mains_v3[j], jouables, pli, contrat, j, REGLES_STANDARD)
            else:
                adversaire.historique = list(historique_v3)
                adversaire.encheres = list(encheres_propres)
                c = adversaire.jouer_carte(mains_v3[j], jouables, pli, contrat, j, REGLES_STANDARD)
            mains_v3[j].remove(c)
            pli.append((j, c))
            historique_v3.append((j, c))
        premier = gagnant_pli(pli, atout)[0]

    # 2. Tester à la fin de chaque pli K :
    solveur = SolveurExact(atout, REGLES_STANDARD)
    bel = equipe_belote(mains_init, atout)
    bonus_belote_0 = 20 if bel == 0 else 0
    pli_decrochage = None

    for num_pli in range(1, 8):
        cartes_jouees = historique_v3[:num_pli * 4]
        mains_apres = [list(m) for m in mains_init]
        pts_deja_0 = 0

        prem = (donneur + 1) % 4
        for p_idx in range(num_pli):
            p_cartes = cartes_jouees[p_idx*4 : p_idx*4 + 4]
            g = gagnant_pli(p_cartes, atout)[0]
            pts_p = sum(points(c, atout) for _, c in p_cartes)
            if g % 2 == 0:
                pts_deja_0 += pts_p
            prem = g
            for j_c, c_c in p_cartes:
                mains_apres[j_c].remove(c_c)

        # Total des points encore en jeu dans les mains restantes (avec le dix de der)
        pts_restants_totaux = sum(points(c, atout) for m in mains_apres for c in m) + REGLES_STANDARD["dix_de_der"]
        
        # Minimax renvoie : pts_futurs_0 - pts_futurs_1
        score_net = solveur.minimax(mains_apres, [], prem, -1000, 1000)
        pts_futurs_0 = (pts_restants_totaux + score_net) // 2

        pts_max_possibles = pts_deja_0 + pts_futurs_0 + bonus_belote_0

        # Si même avec le jeu parfait restant, le contrat ne peut plus être fait :
        if pts_max_possibles < contrat["valeur"]:
            pli_decrochage = num_pli
            break

    if pli_decrochage:
        fatal_par_pli[pli_decrochage] += 1
        print(f"[{idx:2d}/{NB_DONNES}] Graine {graine} ({contrat['valeur']:3d} {atout}) : 💥 Pli fatal = Pli {pli_decrochage}", flush=True)
    else:
        fatal_par_pli[8] += 1
        print(f"[{idx:2d}/{NB_DONNES}] Graine {graine} ({contrat['valeur']:3d} {atout}) : 💥 Pli fatal = Pli 8 (départage final)", flush=True)

print("\n" + "=" * 72)
print(f"DISTRIBUTION DU PREMIER PLI FATAL (SUR {NB_DONNES} DONNES D'ATTAQUE) :")
print("=" * 72)
for p in range(1, 9):
    nb = fatal_par_pli[p]
    pct = 100 * nb / NB_DONNES
    barre = "█" * int(pct / 3)
    print(f"  Pli {p} : {nb:2d} donnes ({pct:5.1f} %)  {barre}")
