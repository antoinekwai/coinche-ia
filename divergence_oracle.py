"""
divergence_oracle.py
Mesure statistique rigoureuse :
Sur les donnes d'attaque où l'Oracle réussit et le v3 chute :
1. À quel pli se produit la PREMIÈRE divergence entre le coup de l'Oracle et celui du v3 ?
2. Quel est le coût en points de cette divergence (évalué par solveur exact) ?
"""
import json
import random
import numpy as np
import torch
from regles import REGLES_STANDARD
from moteur import distribuer, cartes_jouables, gagnant_pli, points, COULEURS
from solveur_exact import SolveurExact
from ia_joueur import JoueurIA
from bot_mc_ia_v3 import BotMCIAv3
from test_mc_encheres import MCEncheres

FICHIER = "resultats_v4.jsonl"
NB_DONNES = 60

# 1. Sélectionner les donnes d'attaque où Oracle gagne et v3 chute
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

print(f"=== ANALYSE DE LA PREMIÈRE DIVERGENCE SUR {len(candidats)} DONNES D'ATTAQUE ===")
print("Pour chaque donne : pli du premier désaccord, carte Oracle vs carte v3, coût en points.")
print("-" * 75)

stats_premier_pli = {p: 0 for p in range(1, 9)}
couts_par_pli = {p: [] for p in range(1, 9)}

for idx, d in enumerate(candidats, 1):
    graine = d["graine"]
    
    # Extraction propre des enchères
    encheres_propres = []
    atout = "♠"
    valeur = d["valeur"]
    dernier_c = None
    for item in d["encheres"]:
        j = item[0]
        act = item[1]
        if isinstance(act, list):
            act = tuple(act)
            if len(act) == 2 and act[1] in COULEURS:
                atout = act[1]
                valeur = act[0]
                dernier_c = (j, act[0], act[1])
        encheres_propres.append((j, act))

    # Premier déclarant de la couleur
    camp = 0  # Attaque
    declarant = 0
    for j_e, act_e in encheres_propres:
        if isinstance(act_e, tuple) and act_e[1] == atout and (j_e % 2 == camp):
            declarant = j_e
            break

    contrat = {
        "valeur": valeur,
        "atout": atout,
        "joueur": declarant,
        "coinche": 1 if any(dec == "coinche" for _, dec in encheres_propres) else 0,
        "capot": False
    }

    donneur = graine % 4
    premier = (donneur + 1) % 4

    # Reconstituer la donne
    random.seed(graine)
    mains_depart = distribuer()

    # Jouer pli par pli en comparant le coup du v3 et celui de l'Oracle
    mains_communes = [list(m) for m in mains_depart]
    hist = []
    bot_v3 = BotMCIAv3()
    solveur = SolveurExact(atout, REGLES_STANDARD)
    adv = MCEncheres()
    ia_pli1 = JoueurIA()

    divergence_trouvee = False

    for pli_num in range(1, 9):
        pli = []
        for k in range(4):
            j = (premier + k) % 4
            jouables = cartes_jouables(mains_communes[j], pli, atout, j, REGLES_STANDARD)

            if len(jouables) == 1:
                c_choisie = jouables[0]
            elif j % 2 != camp:
                # Adversaire
                adv.historique = list(hist)
                adv.encheres = list(encheres_propres)
                c_choisie = adv.jouer_carte(mains_communes[j], jouables, pli, contrat, j, REGLES_STANDARD)
            else:
                # Camp d'attaque (joueur 0 ou partenaire joueur 2)
                # 1. Coup du v3
                random.seed(graine * 10 + 7 + len(hist))
                np.random.seed((graine * 10 + 7 + len(hist)) % 2**32)
                torch.manual_seed(graine * 10 + 7 + len(hist))

                bot_v3.historique = list(hist)
                bot_v3.encheres = list(encheres_propres)
                c_v3 = bot_v3.jouer_carte(mains_communes[j], jouables, pli, contrat, j, REGLES_STANDARD)

                # 2. Coup optimal de l'Oracle (solveur minimax cartes ouvertes)
                best_val = -9999
                c_oracle = None
                for cand in jouables:
                    m_test = [list(m) for m in mains_communes]
                    m_test[j].remove(cand)
                    pli_test = list(pli) + [(j, cand)]
                    solveur.transposition.clear()
                    net = solveur.minimax(m_test, pli_test, premier, -1000, 1000)
                    # Si c'est l'équipe 0, minimax maximise net ; si équipe 1, minimise
                    val = net if j % 2 == 0 else -net
                    if val > best_val:
                        best_val = val
                        c_oracle = cand

                # Évaluer la valeur du coup du v3 avec le solveur
                m_v3_test = [list(m) for m in mains_communes]
                m_v3_test[j].remove(c_v3)
                pli_v3_test = list(pli) + [(j, c_v3)]
                solveur.transposition.clear()
                val_v3 = solveur.minimax(m_v3_test, pli_v3_test, premier, -1000, 1000)
                if j % 2 != 0:
                    val_v3 = -val_v3

                cout = (best_val - val_v3) // 2  # conversion score net -> points réels

                if not divergence_trouvee and c_v3 != c_oracle and cout > 0:
                    stats_premier_pli[pli_num] += 1
                    couts_par_pli[pli_num].append(cout)
                    divergence_trouvee = True
                    print(f"[{idx:2d}/{NB_DONNES}] Graine {graine} ({valeur} {atout}) : ⚡ 1re divergence au Pli {pli_num} (J{j}) | v3={c_v3[0]}{c_v3[1]} vs Oracle={c_oracle[0]}{c_oracle[1]} | Coût = -{cout} pts", flush=True)

                c_choisie = c_v3  # On continue la partie avec le coup réel du v3

            mains_communes[j].remove(c_choisie)
            pli.append((j, c_choisie))
            hist.append((j, c_choisie))

        g = gagnant_pli(pli, atout)[0]
        premier = g

    if not divergence_trouvee:
        stats_premier_pli[8] += 1
        couts_par_pli[8].append(0)

print("\n" + "=" * 75)
print(f"RÉPARTITION DU PREMIER DÉCROCHAGE (SUR {NB_DONNES} DONNES D'ATTAQUE) :")
print("=" * 75)
total_div = sum(stats_premier_pli.values())
for p in range(1, 9):
    nb = stats_premier_pli[p]
    pct = 100 * nb / max(1, total_div)
    cout_m = np.mean(couts_par_pli[p]) if couts_par_pli[p] else 0.0
    barre = "█" * int(pct / 3)
    print(f"  Pli {p} : {nb:2d} donnes ({pct:5.1f} %) | Coût moyen : -{cout_m:4.1f} pts  {barre}")
