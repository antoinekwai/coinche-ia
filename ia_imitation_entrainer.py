import glob
import os
import shutil
import time
import numpy as np
import torch
import torch.nn as nn
import sys
from ia_joueur import creer_reseau_carte, FICHIER

EPOQUES = 8
LOT = 2048
SAUVEGARDE = "ia_carte_autoapprentissage.pt"


def charger_blocs(fichiers):
    S, D, C, V = [], [], [], []
    decalage = 0
    for f in fichiers:
        z = np.load(f)
        S.append(z["S"])
        D.append(z["D"] + decalage)
        C.append(z["C"])
        V.append(z["V"])
        decalage += len(z["S"])
    return (np.concatenate(S), np.concatenate(D),
            np.concatenate(C).astype(np.int64), np.concatenate(V))

def lisser_equivalences(S, D, C, V):
    """
    Lisse les cibles des cartes strictement équivalentes dans chaque décision :
    - 7 et 8 hors atout (cartes neutres à 0 point)
    - Séquences maîtresses consécutives en main (ex: V et 9 d'atout, As et 10)
    """
    V_lisse = np.array(V, copy=True)
    
    # Pour chaque décision unique d
    nb_decisions = len(S)
    debut_d = np.r_[0, np.where(D[1:] != D[:-1])[0] + 1, len(D)]
    
    for k in range(len(debut_d) - 1):
        idx_debut = debut_d[k]
        idx_fin = debut_d[k+1]
        
        cartes_pli = C[idx_debut:idx_fin]
        valeurs_pli = V_lisse[idx_debut:idx_fin]
        
        if len(cartes_pli) <= 1:
            continue
            
        sit = S[k] # situation encodée
        
        # 1. Lissage des petites cartes neutres (7 et 8 hors atout)
        # Indice 0 à 7 = Atout, 8 à 31 = Hors atout.
        # Dans chaque couleur hors atout, 7 et 8 ont les rangs relatifs 0 et 1.
        groupes = {}
        for local_i, c_id in enumerate(cartes_pli):
            coul = c_id // 8
            rang = c_id % 8
            # Détection des petites cartes neutres (7 et 8 hors atout)
            if coul > 0 and rang in (0, 1):
                groupes.setdefault(('petite', coul), []).append(local_i)
            # Détection V et 9 d'atout (rangs 0 et 1 à l'atout)
            elif coul == 0 and rang in (0, 1) and sit[0] > 0 and sit[1] > 0:
                groupes.setdefault(('v9_atout',), []).append(local_i)

        for _, indices in groupes.items():
            if len(indices) > 1:
                moy = np.mean([valeurs_pli[i] for i in indices])
                for i in indices:
                    V_lisse[idx_debut + i] = moy

    return V_lisse

def centrer(D, V):
    somme = np.bincount(D, weights=V)
    nb = np.bincount(D)
    return (V - (somme / nb)[D]).astype(np.float32)


def premiers_par_groupe(D, cle):
    """Pour chaque décision, l'indice de la carte qui a la plus grande valeur de `cle`."""
    ordre = np.lexsort((-cle, D))
    Ds = D[ordre]
    return ordre[np.r_[True, Ds[1:] != Ds[:-1]]]


def predire(reseau, S_t, D_t, C_t, dev):
    preds = []
    with torch.no_grad():
        for i in range(0, len(D_t), 65536):
            d, c = D_t[i:i + 65536], C_t[i:i + 65536]
            x = torch.cat([S_t[d].float(), nn.functional.one_hot(c, 32).float()], 1)
            preds.append(reseau(x).squeeze(1).cpu())
    return torch.cat(preds).numpy()


if __name__ == "__main__":
    dossier = sys.argv[1] if len(sys.argv) > 1 else "imitation"
    fichiers = sorted(glob.glob(f"{dossier}/bloc_*.npz"))

    if len(fichiers) < 2:
        raise SystemExit("Il faut au moins 2 blocs (1 pour apprendre, 1 pour vérifier).")
    dev = "mps" if torch.backends.mps.is_available() else "cpu"

    S, D, C, V = charger_blocs(fichiers[:-1])
    Sv, Dv, Cv, Vv = charger_blocs(fichiers[-1:])
    print(f"Entraînement : {len(V)} cartes évaluées ({len(S)} décisions), "
          f"vérification : {len(Vv)} cartes ({len(Sv)} décisions), calcul sur {dev}\n")

    print("Application du lissage des cartes équivalentes...")
    V_lisse = lisser_equivalences(S, D, C, V)
    V_cible = centrer(D, V_lisse)

    S_t, D_t, C_t, V_t = (torch.from_numpy(a).to(dev) for a in (S, D, C, V_cible))

    Sv_t, Dv_t, Cv_t = (torch.from_numpy(a).to(dev) for a in (Sv, Dv, Cv))
    meilleur_mc = premiers_par_groupe(Dv, Vv)

    reseau = creer_reseau_carte()
    if os.path.exists(FICHIER):
        reseau.load_state_dict(torch.load(FICHIER, map_location="cpu"))
        if not os.path.exists(SAUVEGARDE):
            shutil.copy(FICHIER, SAUVEGARDE)
            print(f"Réseau de la nuit sauvegardé dans {SAUVEGARDE}")
    reseau.to(dev)

    pas_par_epoque = len(V) // LOT
    opt = torch.optim.Adam(reseau.parameters(), lr=1e-3)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=EPOQUES * pas_par_epoque)
    meilleur_regret = None
    debut = time.time()

    for epoque in range(1, EPOQUES + 1):
        reseau.train()
        total = 0.0
        for _ in range(pas_par_epoque):
            idx = torch.randint(0, len(V_t), (LOT,), device=dev)
            x = torch.cat([S_t[D_t[idx]].float(),
                           nn.functional.one_hot(C_t[idx], 32).float()], 1)
            perte = nn.functional.mse_loss(reseau(x).squeeze(1), V_t[idx])
            opt.zero_grad()
            perte.backward()
            opt.step()
            sched.step()
            total += perte.item()

        reseau.eval()
        pred = predire(reseau, Sv_t, Dv_t, Cv_t, dev)
        choix_ia = premiers_par_groupe(Dv, pred)
        accord = np.mean(choix_ia == meilleur_mc)
        regret = np.mean(Vv[meilleur_mc] - Vv[choix_ia])
        erreur_v = np.mean((pred - centrer(Dv, Vv)) ** 2)
        print(f"Époque {epoque} : erreur {total / pas_par_epoque:.4f} (vérif. {erreur_v:.4f}), "
              f"accord {100 * accord:.1f} %, regret {regret:.4f} "
              f"({(time.time() - debut) / 60:.0f} min)")

        if meilleur_regret is None or regret < meilleur_regret:
            meilleur_regret = regret
            torch.save({k: v.cpu() for k, v in reseau.state_dict().items()}, FICHIER)

    print(f"\nMeilleur réseau enregistré dans {FICHIER} (regret {meilleur_regret:.4f})")
