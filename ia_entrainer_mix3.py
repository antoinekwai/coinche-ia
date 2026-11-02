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

def entrainer_avec_mix3():
    dev = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"Chargement des 3 sources de données sur {dev}...")
    debut = time.time()

    # 1. Source Générale (40 blocs, ~70% du mix)
    fichiers_gen = sorted(glob.glob("imitation_encheres/bloc_*.npz"))
    S_g, D_g, C_g, V_g = charger_blocs(fichiers_gen)
    V_g_lisse = lisser_equivalences(S_g, D_g, C_g, V_g)
    V_g_cible = centrer(D_g, V_g_lisse)

    # 2. Source Attaque au Valet (20k donnes, ~15% du mix)
    z_att = np.load("ciblage_entame_20k.npz")
    S_att, D_att, C_att, V_att = z_att["S"], z_att["D"], z_att["C"].astype(np.int64), z_att["V"]

    # 3. Source Défense Coinchée (12k donnes, ~15% du mix)
    z_def = np.load("ciblage_defense_12k.npz")
    S_def, D_def, C_def, V_def = z_def["S"], z_def["D"], z_def["C"].astype(np.int64), z_def["V"]

    print(f"  • Source 1 - Jeu Général   : {len(V_g_cible)} cartes ({len(S_g)} décisions)")
    print(f"  • Source 2 - Attaque Valet : {len(V_att)} cartes ({len(S_att)} décisions)")
    print(f"  • Source 3 - Défense 120+  : {len(V_def)} cartes ({len(S_def)} décisions)")

    # Transfert mémoire GPU
    S_g_t, D_g_t, C_g_t, V_g_t = (torch.from_numpy(a).to(dev) for a in (S_g, D_g, C_g, V_g_cible))
    S_att_t, D_att_t, C_att_t, V_att_t = (torch.from_numpy(a).to(dev) for a in (S_att, D_att, C_att, V_att))
    S_def_t, D_def_t, C_def_t, V_def_t = (torch.from_numpy(a).to(dev) for a in (S_def, D_def, C_def, V_def))

    # Chargement du réseau actuel
    reseau = creer_reseau_carte()
    if os.path.exists(FICHIER):
        reseau.load_state_dict(torch.load(FICHIER, map_location="cpu"))
        print(f"Réseau existant chargé depuis {FICHIER}")
    reseau.to(dev)

    # Tailles des sous-lots par tirage (Total = 2048)
    lot_att = int(LOT * 0.15)            # ~307 exemples Attaque
    lot_def = int(LOT * 0.15)            # ~307 exemples Défense
    lot_g = LOT - lot_att - lot_def      # ~1434 exemples Généraux
    pas_par_epoque = len(V_g_cible) // lot_g

    opt = torch.optim.Adam(reseau.parameters(), lr=2e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=EPOQUES * pas_par_epoque)
    perte_fn = nn.MSELoss()

    print(f"\nDébut de l'entraînement mixé (70% / 15% / 15%) sur {EPOQUES} époques...")
    for epoque in range(1, EPOQUES + 1):
        reseau.train()
        total_perte = 0.0
        
        for _ in range(pas_par_epoque):
            idx_g = torch.randint(0, len(V_g_t), (lot_g,), device=dev)
            idx_att = torch.randint(0, len(V_att_t), (lot_att,), device=dev)
            idx_def = torch.randint(0, len(V_def_t), (lot_def,), device=dev)

            x_g = torch.cat([S_g_t[D_g_t[idx_g]].float(), nn.functional.one_hot(C_g_t[idx_g], 32).float()], 1)
            x_att = torch.cat([S_att_t[D_att_t[idx_att]].float(), nn.functional.one_hot(C_att_t[idx_att], 32).float()], 1)
            x_def = torch.cat([S_def_t[D_def_t[idx_def]].float(), nn.functional.one_hot(C_def_t[idx_def], 32).float()], 1)

            x = torch.cat([x_g, x_att, x_def], dim=0)
            y = torch.cat([V_g_t[idx_g], V_att_t[idx_att], V_def_t[idx_def]], dim=0)

            perte = perte_fn(reseau(x).squeeze(1), y)
            opt.zero_grad()
            perte.backward()
            opt.step()
            sched.step()
            total_perte += perte.item()

        print(f"Époque {epoque}/{EPOQUES} — Erreur : {total_perte / pas_par_epoque:.4f} ({(time.time()-debut)/60:.1f} min)")

    # Sauvegarde finale
    torch.save(reseau.cpu().state_dict(), FICHIER)
    print(f"\nRéseau mis à jour avec succès dans {FICHIER} en {(time.time()-debut)/60:.1f} min !")

if __name__ == "__main__":
    entrainer_avec_mix3()
