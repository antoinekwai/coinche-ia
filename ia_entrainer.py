import os
import sys
import time
import random
import shutil
import multiprocessing as mp
import numpy as np
import torch
import torch.nn as nn
from regles import REGLES_STANDARD
from partie import jouer_donne
from systeme_corrige import SysCorrige
from ia_joueur import JoueurIA, creer_reseau_carte, FICHIER
from ia_encodage import TAILLE_SITUATION, TAILLE_CARTE
from rapide import afficher_rapide

DONNES_PAR_TACHE = 250
TACHES = 8                 # 2000 donnes par itération
TAILLE_MEMOIRE = 500000    # décisions gardées en mémoire
PAS = 300                  # pas d'apprentissage par itération
LOT = 512
EVAL_TOUTES = 250           # itérations entre deux évaluations
BONUS = 0.2                # poids de l'écart de points (pour départager)


def generer(tache):
    """Un cœur joue des donnes IA contre IA et renvoie les décisions notées."""
    graine, epsilon, bonus = tache
    random.seed(graine)
    exemples = []
    for _ in range(DONNES_PAR_TACHE):
        memoire = []
        joueurs = [JoueurIA() for _ in range(4)]
        for j in joueurs:
            j.memoire, j.epsilon = memoire, epsilon
        res = jouer_donne(random.randrange(4), joueurs, REGLES_STANDARD)
        if res is None:
            continue
        attaque = res["contrat"]["joueur"] % 2
        pts = res["points"]
        for joueur, x in memoire:
            e = joueur % 2
            gagne = res["reussi"] if e == attaque else not res["reussi"]
            cible = (1.0 if gagne else -1.0) + bonus * (pts[e] - pts[1 - e]) / 162
            exemples.append((x, cible))
    return exemples


def sauver(reseau):
    tmp = FICHIER + ".tmp"
    torch.save(reseau.state_dict(), tmp)
    os.replace(tmp, FICHIER)        # remplacement d'un coup : les cœurs ne lisent jamais un fichier à moitié écrit


if __name__ == "__main__":
    heures = float(sys.argv[1]) if len(sys.argv) > 1 else 8
    reseau = creer_reseau_carte()
    if os.path.exists(FICHIER):
        reseau.load_state_dict(torch.load(FICHIER))
        print("Reprise à partir de ia_carte.pt")
    sauver(reseau)
    opt = torch.optim.Adam(reseau.parameters(), lr=3e-4)

    X = np.zeros((TAILLE_MEMOIRE, TAILLE_SITUATION + TAILLE_CARTE), dtype=np.float32)
    Y = np.zeros(TAILLE_MEMOIRE, dtype=np.float32)
    n = pos = iteration = 0
    debut = time.time()
    pool = mp.get_context("fork").Pool(os.cpu_count())
    erreurs_recentes = []

    while time.time() - debut < heures * 3600:
        iteration += 1
        epsilon = max(0.05, 0.2 - 0.15 * iteration / 1000)
        bonus = max(BONUS, 1.0 - 0.8 * iteration / 3000)   # points d'abord, contrat ensuite
        taches = [(int(debut) + 1000 * iteration + k, epsilon, bonus) for k in range(TACHES)]

        nouveaux = 0
        for lot in pool.imap_unordered(generer, taches):
            for x, y in lot:
                X[pos], Y[pos] = x, y
                pos = (pos + 1) % TAILLE_MEMOIRE
                n = min(n + 1, TAILLE_MEMOIRE)
                nouveaux += 1

        reseau.train()
        total = 0.0
        for _ in range(PAS):
            idx = np.random.randint(0, n, LOT)
            perte = nn.functional.mse_loss(reseau(torch.from_numpy(X[idx])).squeeze(1),
                                           torch.from_numpy(Y[idx]))
            opt.zero_grad()
            perte.backward()
            opt.step()
            total += perte.item()
        reseau.eval()
        sauver(reseau)
        erreurs_recentes.append(total / PAS)
        if iteration % 50 == 0:
            print(f"Itération {iteration} : erreur moyenne {np.mean(erreurs_recentes):.3f}, "
                  f"epsilon {epsilon:.2f}, bonus {bonus:.2f} ({(time.time() - debut) / 60:.0f} min)")
            erreurs_recentes = []


        if iteration % EVAL_TOUTES == 0:
            print(f"--- Évaluation après {iteration} itérations ---")
            afficher_rapide(JoueurIA, SysCorrige, 2000, REGLES_STANDARD)
            shutil.copy(FICHIER, f"ia_carte_iter{iteration}.pt")

    pool.close()
    print("Entraînement terminé.")
