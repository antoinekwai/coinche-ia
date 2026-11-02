import os
import random
import time
import multiprocessing as mp
import numpy as np
import torch
import torch.nn as nn
from regles import REGLES_STANDARD
from moteur import distribuer, COULEURS, RANGS, cartes_jouables
from test_mc_encheres import MCEncheres
from ia_joueur import charger, FICHIER, creer_reseau_carte
from ia_encodage import encoder_situation, encoder_carte, indice, ordre_couleurs

NB_CAS = 2000
DOSSIER_CIBLE = "ciblage_entame.npz"

def generer_donne_ciblee(graine):
    random.seed(graine)
    atout = random.choice(COULEURS)
    cotes = [c for c in COULEURS if c != atout]
    
    # Construction d'une main d'entame critique : Valet d'atout + 1 ou 2 As annexes
    # 50% avec le 9, 50% sans le 9
    avec_9 = random.random() < 0.5
    atouts = [("V", atout)] + ([("9", atout)] if avec_9 else [])
    nb_petits = random.choice([1, 2, 3])
    pool_petits = [r for r in ["7", "8", "10", "D", "R"] if r != "9" or not avec_9]
    atouts += [(r, atout) for r in random.sample(pool_petits, nb_petits)]

    # Au moins 1 As hors atout
    as_cotes = [("A", c) for c in random.sample(cotes, random.choice([1, 2]))]
    
    reste_cartes = [(r, c) for c in cotes for r in RANGS if (r, c) not in as_cotes]
    main_0 = atouts + as_cotes + random.sample(reste_cartes, 8 - len(atouts) - len(as_cotes))
    
    # Distribuer les 24 cartes restantes aux 3 autres joueurs
    paquet_reste = [(r, c) for c in COULEURS for r in RANGS if (r, c) not in main_0]
    random.shuffle(paquet_reste)
    mains = [main_0, paquet_reste[0:8], paquet_reste[8:16], paquet_reste[16:24]]

    # Contrat d'attaque par le joueur 0
    val_contrat = 110 if len(atouts) >= 4 else 90
    contrat = {"valeur": val_contrat, "atout": atout, "joueur": 0, "coinche": 0, "capot": False}
    encheres = [(0, (val_contrat, atout)), (1, "passe"), (2, "passe"), (3, "passe")]

    # Évaluation par Monte Carlo 100 simulations
    mc = MCEncheres()
    mc.nb_simulations = 100
    mc.historique = []
    mc.encheres = encheres
    
    jouables = list(main_0)
    
    # Évaluation de chaque carte
    valeurs = {}
    eq = 0
    manque = {p: set() for p in range(4)}
    ordre = ordre_couleurs(atout)

    for _ in range(mc.nb_simulations):
        m_sim = mc.imaginer(main_0, 0, manque, atout)
        from montecarlo import simuler, contrat_reussi, belote_imaginee
        bel = belote_imaginee(m_sim, [], atout)
        for c in jouables:
            pts, plis = simuler(m_sim, [], contrat, 0, c, 0, REGLES_STANDARD)
            reussi = contrat_reussi(contrat, pts[0], plis[0], bel == 0, REGLES_STANDARD)
            score = (1.0 if reussi else -1.0) + 0.2 * (pts[0] - pts[1]) / 162.0
            valeurs[c] = valeurs.get(c, 0.0) + score

    s = encoder_situation(main_0, [], [], contrat, 0, REGLES_STANDARD, encheres)
    
    # Enregistrement des cibles lissées/centrées
    cartes_eval = []
    for c in jouables:
        c_idx = indice(c, ordre)
        val_moy = valeurs[c] / mc.nb_simulations
        cartes_eval.append((c_idx, val_moy))

    # Centrage sur cette décision
    vals = [v for _, v in cartes_eval]
    moy_decision = np.mean(vals)
    cartes_centrees = [(c_idx, v - moy_decision) for c_idx, v in cartes_eval]

    return s, cartes_centrees

def lancer_generation():
    print(f"Génération de {NB_CAS} donnes ciblées avec Monte Carlo 100 simulations...")
    debut = time.time()
    S, D, C, V = [], [], [], []
    
    with mp.get_context("fork").Pool(os.cpu_count()) as pool:
        for k, (s, evals) in enumerate(pool.imap_unordered(generer_donne_ciblee, range(100000, 100000 + NB_CAS), chunksize=20)):
            d_idx = len(S)
            S.append(s.astype(np.float16))
            for c_id, val in evals:
                D.append(d_idx)
                C.append(c_id)
                V.append(val)
            if (k + 1) % 250 == 0:
                print(f"  {k + 1}/{NB_CAS} donnes générées ({(time.time() - debut) / 60:.1f} min)")

    np.savez(DOSSIER_CIBLE, S=np.array(S), D=np.array(D, dtype=np.int32),
             C=np.array(C, dtype=np.int8), V=np.array(V, dtype=np.float32))
    print(f"Données enregistrées dans {DOSSIER_CIBLE} ({len(V)} cartes évaluées).")

def ajuster_reseau():
    print("\nAjustement des poids du réseau de neurones...")
    z = np.load(DOSSIER_CIBLE)
    S, D, C, V = z["S"], z["D"], z["C"].astype(np.int64), z["V"]
    
    dev = "mps" if torch.backends.mps.is_available() else "cpu"
    S_t = torch.from_numpy(S).to(dev)
    D_t = torch.from_numpy(D).to(dev)
    C_t = torch.from_numpy(C).to(dev)
    V_t = torch.from_numpy(V).to(dev)
    
    reseau = creer_reseau_carte()
    reseau.load_state_dict(torch.load(FICHIER, map_location="cpu"))
    reseau.to(dev)
    reseau.train()

    # Vitesse d'apprentissage très douce pour ne pas détruire les acquis du réseau
    opt = torch.optim.Adam(reseau.parameters(), lr=1e-4)
    perte_fn = nn.MSELoss()
    
    LOT = 512
    PAS = len(V) // LOT
    
    for epoque in range(1, 11):
        total = 0.0
        for _ in range(PAS):
            idx = torch.randint(0, len(V_t), (LOT,), device=dev)
            x = torch.cat([S_t[D_t[idx]].float(), nn.functional.one_hot(C_t[idx], 32).float()], 1)
            perte = perte_fn(reseau(x).squeeze(1), V_t[idx])
            opt.zero_grad()
            perte.backward()
            opt.step()
            total += perte.item()
        print(f"  Époque {epoque}/10 — Erreur : {total / PAS:.4f}")

    # Sauvegarde du nouveau modèle
    torch.save(reseau.cpu().state_dict(), FICHIER)
    print(f"\nModèle mis à jour avec succès dans {FICHIER} !")

if __name__ == "__main__":
    # Sauvegarde de sécurité
    if os.path.exists(FICHIER) and not os.path.exists("ia_carte_avant_ciblage.pt"):
        import shutil
        shutil.copy(FICHIER, "ia_carte_avant_ciblage.pt")
        print("Sauvegarde de sécurité créée dans ia_carte_avant_ciblage.pt")

    lancer_generation()
    ajuster_reseau()
