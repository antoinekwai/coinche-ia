import os
import random
import time
import multiprocessing as mp
import numpy as np
import torch
from regles import REGLES_STANDARD
from moteur import distribuer, COULEURS, RANGS, cartes_jouables
from test_mc_encheres import MCEncheres
from ia_encodage import encoder_situation, encoder_carte, indice, ordre_couleurs

NB_CAS = 20000
FICHIER_CIBLE_20K = "ciblage_entame_20k.npz"

def generer_une_donne_ciblee(graine):
    random.seed(graine)
    atout = random.choice(COULEURS)
    cotes = [c for c in COULEURS if c != atout]
    
    # 50% Déclarant (1.0), 50% Partenaire du déclarant (0.5)
    role_declarant = (graine % 2 == 0)
    
    # Main d'entame : Valet d'atout + 1 ou 2 As annexes
    avec_9 = random.random() < 0.5
    atouts = [("V", atout)] + ([("9", atout)] if avec_9 else [])
    nb_petits = random.choice([1, 2, 3])
    pool_petits = [r for r in ["7", "8", "10", "D", "R"] if r != "9" or not avec_9]
    atouts += [(r, atout) for r in random.sample(pool_petits, nb_petits)]

    # 1 ou 2 As hors atout
    as_cotes = [("A", c) for c in random.sample(cotes, random.choice([1, 2]))]
    reste_cartes = [(r, c) for c in cotes for r in RANGS if (r, c) not in as_cotes]
    main_0 = atouts + as_cotes + random.sample(reste_cartes, 8 - len(atouts) - len(as_cotes))
    
    paquet_reste = [(r, c) for c in COULEURS for r in RANGS if (r, c) not in main_0]
    random.shuffle(paquet_reste)
    mains = [main_0, paquet_reste[0:8], paquet_reste[8:16], paquet_reste[16:24]]

    # Contrat d'attaque
    val_contrat = 110 if len(atouts) >= 4 else 90
    preneur = 0 if role_declarant else 2
    contrat = {"valeur": val_contrat, "atout": atout, "joueur": preneur, "coinche": 0, "capot": False}
    
    if role_declarant:
        encheres = [(0, (val_contrat, atout)), (1, "passe"), (2, "passe"), (3, "passe")]
    else:
        encheres = [(2, (val_contrat, atout)), (3, "passe"), (0, "passe"), (1, "passe")]

    mc = MCEncheres()
    mc.nb_simulations = 40
    mc.historique = []
    mc.encheres = encheres
    
    jouables = list(main_0)
    valeurs = {c: 0.0 for c in jouables}
    manque = {p: set() for p in range(4)}
    ordre = ordre_couleurs(atout)

    from montecarlo import simuler, contrat_reussi, belote_imaginee
    
    for _ in range(mc.nb_simulations):
        m_sim = mc.imaginer(main_0, 0, manque, atout)
        bel = belote_imaginee(m_sim, [], atout)
        for c in jouables:
            pts, plis = simuler(m_sim, [], contrat, 0, c, 0, REGLES_STANDARD)
            reussi = contrat_reussi(contrat, pts[0], plis[0], bel == 0, REGLES_STANDARD)
            
            # --- PÉNALITÉ DE RISQUE SUR L'ENTAME ---
            # Si on joue un As hors-atout et qu'un adversaire avait une chicane (a coupé au pli 1),
            # le coût stratégique est lourdement pénalisé
            penalite = 0.0
            if c[0] == "A" and c[1] != atout:
                adv_coupe = any(m_sim[p] and not any(x[1] == c[1] for x in m_sim[p]) and any(x[1] == atout for x in m_sim[p])
                                for p in (1, 3))
                if adv_coupe:
                    penalite = -0.6  # Sanction sévère du risque de coupe immédiate
            
            score = (1.0 if reussi else -1.0) + penalite + 0.2 * (pts[0] - pts[1]) / 162.0
            valeurs[c] += score

    s = encoder_situation(main_0, [], [], contrat, 0, REGLES_STANDARD, encheres)
    
    cartes_eval = []
    for c in jouables:
        c_idx = indice(c, ordre)
        val_moy = valeurs[c] / mc.nb_simulations
        cartes_eval.append((c_idx, val_moy))

    vals = [v for _, v in cartes_eval]
    moy_decision = np.mean(vals)
    cartes_centrees = [(c_idx, v - moy_decision) for c_idx, v in cartes_eval]

    return s, cartes_centrees

def generer_20k():
    print(f"Génération de {NB_CAS} donnes ciblées avec pénalité de risque...")
    debut = time.time()
    S, D, C, V = [], [], [], []
    
    with mp.get_context("fork").Pool(os.cpu_count()) as pool:
        for k, (s, evals) in enumerate(pool.imap_unordered(generer_une_donne_ciblee, range(200000, 200000 + NB_CAS), chunksize=25)):
            d_idx = len(S)
            S.append(s.astype(np.float16))
            for c_id, val in evals:
                D.append(d_idx)
                C.append(c_id)
                V.append(val)
            if (k + 1) % 2500 == 0:
                ecoule = time.time() - debut
                vitesse = (k + 1) / ecoule
                restant = (NB_CAS - k - 1) / vitesse
                print(f"  {k + 1:5d}/{NB_CAS} donnes ({ecoule/60:.1f} min — reste ~{restant/60:.1f} min)")

    np.savez(FICHIER_CIBLE_20K, S=np.array(S), D=np.array(D, dtype=np.int32),
             C=np.array(C, dtype=np.int8), V=np.array(V, dtype=np.float32))
    print(f"\nFichier {FICHIER_CIBLE_20K} enregistré avec succès en {(time.time()-debut)/60:.1f} min !")

if __name__ == "__main__":
    generer_20k()
