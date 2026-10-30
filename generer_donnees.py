import os
import random
import time
import multiprocessing as mp
import numpy as np
from moteur import distribuer, COULEURS, RANGS, equipe_belote
from regles import REGLES_STANDARD
from joueurs import JoueurRegles
from partie import jouer_manche


def encoder(main, atout):
    """32 cases (0 ou 1) : l'atout d'abord, puis les 3 autres couleurs triées."""
    def bits(couleur):
        return [1.0 if (r, couleur) in main else 0.0 for r in RANGS]
    cotes = sorted((bits(c) for c in COULEURS if c != atout), reverse=True)
    return bits(atout) + cotes[0] + cotes[1] + cotes[2]


def une_donne(numero):
    """Joue une donne 4 fois (un atout à chaque fois). Renvoie 4 lignes de données."""
    regles = REGLES_STANDARD
    random.seed(numero)
    mains = distribuer()
    donneur = random.randrange(4)
    premier = (donneur + 1) % 4
    on_entame = 1.0 if premier % 2 == 0 else 0.0
    joueurs = [JoueurRegles() for _ in range(4)]

    lignes = []
    for atout in COULEURS:
        contrat = {"valeur": 80, "atout": atout, "joueur": 0, "coinche": 0, "capot": False}
        copie = [m[:] for m in mains]
        belote = equipe_belote(copie, atout)
        pts, plis = jouer_manche(copie, contrat, premier, joueurs, regles)
        total = pts[0] + (regles["points_belote"] if belote == 0 else 0)
        capot = 1.0 if plis[0] == 8 else 0.0
        lignes.append(encoder(mains[0], atout) + [on_entame, total, capot])
    return np.array(lignes, dtype=np.float32)


if __name__ == "__main__":
    nb = 200000
    debut = time.time()
    morceaux = []

    with mp.get_context("fork").Pool(os.cpu_count()) as pool:
        for i, lignes in enumerate(pool.imap(une_donne, range(nb), chunksize=200)):
            morceaux.append(lignes)
            if (i + 1) % 20000 == 0:
                print(f"  {i + 1}/{nb} donnes ({time.time() - debut:.0f} s)")

    tableau = np.concatenate(morceaux)
    np.save("donnees.npy", tableau)
    print(f"\n{len(tableau)} exemples enregistrés dans donnees.npy\n")

    # Vérification : points moyens selon le nombre d'atouts en main
    nb_atouts = tableau[:, 0:8].sum(axis=1)
    points = tableau[:, 33]
    print("Atouts | Exemples | Points moyens | Atteint 80 | Atteint 100 | Capot")
    for n in range(9):
        m = nb_atouts == n
        if m.sum() == 0:
            continue
        print(f"{n:6} | {m.sum():8} | {points[m].mean():13.1f} | "
              f"{100 * (points[m] >= 80).mean():8.1f} % | "
              f"{100 * (points[m] >= 100).mean():9.1f} % | "
              f"{100 * tableau[m, 34].mean():4.1f} %")
