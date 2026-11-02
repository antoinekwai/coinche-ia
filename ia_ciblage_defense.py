import os
import random
import time
import multiprocessing as mp
import numpy as np
from regles import REGLES_STANDARD
from moteur import COULEURS, RANGS, cartes_jouables
from test_mc_encheres import MCEncheres
from mains_types import MAINS_TYPES, generer_main
from experience_coinche import force_coinche
from ia_encodage import encoder_situation, encoder_carte, indice, ordre_couleurs

NB_CAS = 12000
FICHIER_CIBLE_DEF = "ciblage_defense_12k.npz"

# Indices des mains fortes (120+) dans MAINS_TYPES
MAINS_FORTES_SPECS = [
    spec for nom, spec in MAINS_TYPES 
    if any(k in nom for k in ["140", "120", "110", "A 10 x", "3 petits + 2 as", "4 petits + 1 as"])
]

def generer_donne_defense_coinche(graine):
    random.seed(graine)
    atout = random.choice(COULEURS)
    
    # 1. Main de l'attaquant (Preneur en Est ou Ouest)
    # L'attaquant est joueur 1 (Ouest), l'humain/bot défenseur est joueur 0 (Sud)
    spec_att = random.choice(MAINS_FORTES_SPECS)
    main_preneur = generer_main(spec_att)
    
    # 2. Distribuer les 24 cartes restantes jusqu'à ce que la défense ait de quoi coincher
    paquet_reste = [(r, c) for c in COULEURS for r in RANGS if (r, c) not in main_preneur]
    
    val_contrat = random.choice([120, 130, 140])
    contrat = {"valeur": val_contrat, "atout": atout, "joueur": 1, "coinche": 1, "capot": False}
    encheres = [(1, (val_contrat, atout)), (2, "passe"), (3, "passe"), (0, "coinche")]

    # On cherche une main de défense crédible (force >= 2)
    for _ in range(30):
        random.shuffle(paquet_reste)
        main_def = paquet_reste[0:8]
        if force_coinche(main_def, contrat) >= 2:
            break

    mains = [main_def, main_preneur, paquet_reste[8:16], paquet_reste[16:24]]

    # 3. Évaluation par Monte Carlo Enchères des coups du défenseur
    mc = MCEncheres()
    mc.nb_simulations = 40
    mc.historique = []
    mc.encheres = encheres
    
    # On évalue le premier pli où la défense a la main (Pli 1, Sud entame)
    jouables = cartes_jouables(main_def, [], atout, 0, REGLES_STANDARD)
    manque = {p: set() for p in range(4)}
    valeurs = {c: 0.0 for c in jouables}
    
    from montecarlo import simuler, contrat_reussi, belote_imaginee
    
    for _ in range(mc.nb_simulations):
        m_sim = mc.imaginer(main_def, 0, manque, atout)
        bel = belote_imaginee(m_sim, [], atout)
        for c in jouables:
            pts, plis = simuler(m_sim, [], contrat, 0, c, 0, REGLES_STANDARD)
            # L'attaquant est en 1. Pour la défense (0 et 2), le succès = faire chuter 1
            reussi = contrat_reussi(contrat, pts[1], plis[1], bel == 1, REGLES_STANDARD)
            gagne_defense = not reussi
            # Gros enjeu sur la coinche (+2.0 si chute, -2.0 si l'adversaire fait son contrat coinché)
            score = (2.0 if gagne_defense else -2.0) + 0.2 * (pts[0] - pts[1]) / 162.0
            valeurs[c] += score

    s = encoder_situation(main_def, [], [], contrat, 0, REGLES_STANDARD, encheres)
    ordre = ordre_couleurs(atout)
    
    cartes_eval = []
    for c in jouables:
        c_idx = indice(c, ordre)
        val_moy = valeurs[c] / mc.nb_simulations
        cartes_eval.append((c_idx, val_moy))

    vals = [v for _, v in cartes_eval]
    moy_decision = np.mean(vals)
    cartes_centrees = [(c_idx, v - moy_decision) for c_idx, v in cartes_eval]

    return s, cartes_centrees

def generer_defense_12k():
    print(f"Génération de {NB_CAS} donnes ciblées sur la DÉFENSE DE CONTRATS COINCHÉS (120-140)...")
    debut = time.time()
    S, D, C, V = [], [], [], []
    
    with mp.get_context("fork").Pool(os.cpu_count()) as pool:
        for k, (s, evals) in enumerate(pool.imap_unordered(generer_donne_defense_coinche, range(500000, 500000 + NB_CAS), chunksize=25)):
            d_idx = len(S)
            S.append(s.astype(np.float16))
            for c_id, val in evals:
                D.append(d_idx)
                C.append(c_id)
                V.append(val)
            if (k + 1) % 2000 == 0:
                ecoule = time.time() - debut
                vitesse = (k + 1) / ecoule
                restant = (NB_CAS - k - 1) / vitesse
                print(f"  {k + 1:5d}/{NB_CAS} donnes ({ecoule/60:.1f} min — reste ~{restant/60:.1f} min)")

    np.savez(FICHIER_CIBLE_DEF, S=np.array(S), D=np.array(D, dtype=np.int32),
             C=np.array(C, dtype=np.int8), V=np.array(V, dtype=np.float32))
    print(f"\nFichier {FICHIER_CIBLE_DEF} enregistré avec succès en {(time.time()-debut)/60:.1f} min !")

if __name__ == "__main__":
    generer_defense_12k()
