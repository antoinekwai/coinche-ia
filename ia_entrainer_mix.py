import glob
import os
import time
import numpy as np
import torch
import torch.nn as nn
from ia_joueur import creer_reseau_carte, FICHIER
from ia_imitation_entrainer import charger_blocs, lisser_equivalences, centrer

EPOQUES = 6
LOT = 2048
RATIO_CIBLE = 0.20  # 20% de cas d'entame ciblés, 80% de jeu général

def entrainer_avec_mix():
    dev = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"Chargement des données sur {dev}...")
    debut = time.time()

    # 1. Chargement des 40 blocs généraux (80% du mix)
    fichiers_gen = sorted(glob.glob("imitation_encheres/bloc_*.npz"))
    S_g, D_g, C_g, V_g = charger_blocs(fichiers_gen)
    V_g_lisse = lisser_equivalences(S_g, D_g, C_g, V_g)
    V_g_cible = centrer(D_g, V_g_lisse)

    # 2. Chargement des 20 000 donnes ciblées (20% du mix)
    z_c = np.load("ciblage_entame_20k.npz")
    S_c, D_c, C_c, V_c = z_c["S"], z_c["D"], z_c["C"].astype(np.int64), z_c["V"]
    # Déjà centrées lors de la génération

    print(f"  • Données générales : {len(V_g_cible)} cartes ({len(S_g)} décisions)")
    print(f"  • Données ciblées   : {len(V_c)} cartes ({len(S_c)} décisions)")

    # Transfert mémoire
    S_g_t, D_g_t, C_g_t, V_g_t = (torch.from_numpy(a).to(dev) for a in (S_g, D_g, C_g, V_g_cible))
    S_c_t, D_c_t, C_c_t, V_c_t = (torch.from_numpy(a).to(dev) for a in (S_c, D_c, C_c, V_c))

    # Chargement du réseau actuel
    reseau = creer_reseau_carte()
    if os.path.exists(FICHIER):
        reseau.load_state_dict(torch.load(FICHIER, map_location="cpu"))
        print(f"Réseau existant chargé depuis {FICHIER}")
    reseau.to(dev)

    # Tailles des sous-lots
    lot_c = int(LOT * RATIO_CIBLE)       # ~410 exemples ciblés
    lot_g = LOT - lot_c                  # ~1638 exemples généraux
    pas_par_epoque = len(V_g_cible) // lot_g

    opt = torch.optim.Adam(reseau.parameters(), lr=3e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=EPOQUES * pas_par_epoque)
    perte_fn = nn.MSELoss()

    print(f"\nDébut de l'entraînement mixé sur {EPOQUES} époques...")
    for epoque in range(1, EPOQUES + 1):
        reseau.train()
        total_perte = 0.0
        
        for _ in range(pas_par_epoque):
            # Tirage mixte
            idx_g = torch.randint(0, len(V_g_t), (lot_g,), device=dev)
            idx_c = torch.randint(0, len(V_c_t), (lot_c,), device=dev)

            x_g = torch.cat([S_g_t[D_g_t[idx_g]].float(), nn.functional.one_hot(C_g_t[idx_g], 32).float()], 1)
            x_c = torch.cat([S_c_t[D_c_t[idx_c]].float(), nn.functional.one_hot(C_c_t[idx_c], 32).float()], 1)

            x = torch.cat([x_g, x_c], dim=0)
            y = torch.cat([V_g_t[idx_g], V_c_t[idx_c]], dim=0)

            perte = perte_fn(reseau(x).squeeze(1), y)
            opt.zero_grad()
            perte.backward()
            opt.step()
            sched.step()
            total_perte += perte.item()

        print(f"Époque {epoque}/{EPOQUES} — Erreur : {total_perte / pas_par_epoque:.4f} ({(time.time()-debut)/60:.1f} min)")

    # Sauvegarde finale
    torch.save(reseau.cpu().state_dict(), FICHIER)
    print(f"\nRéseau réajusté avec succès et enregistré dans {FICHIER} en {(time.time()-debut)/60:.1f} min !")

if __name__ == "__main__":
    entrainer_avec_mix()
