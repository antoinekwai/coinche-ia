import csv
import os
import random
import time
import multiprocessing as mp
from moteur import COULEURS, RANGS, equipe_belote
from regles import REGLES_STANDARD
from montecarlo import JoueurMonteCarlo
from partie import jouer_manche
from mains_types import MAINS_TYPES, generer_main, ATOUT

NB = 2000          # donnes par main et par position
PALIERS = [80, 90, 100, 110, 120, 130, 140, 150, 160]
POSITIONS = ["1er (entame)", "2e", "3e", "4e"]


def une_donne(tache):
    """Le preneur (J0) a une main du type demandé, les autres sont au hasard."""
    i, pos, numero = tache
    regles = REGLES_STANDARD
    random.seed(numero)
    main = generer_main(MAINS_TYPES[i][1])
    reste = [(r, c) for c in COULEURS for r in RANGS if (r, c) not in main]
    random.shuffle(reste)
    mains = [main, reste[0:8], reste[8:16], reste[16:24]]

    contrat = {"valeur": 80, "atout": ATOUT, "joueur": 0, "coinche": 0, "capot": False}
    belote = equipe_belote(mains, ATOUT)
    premier = (4 - pos) % 4                    # pos = rang du preneur au 1er pli
    joueurs = [JoueurMonteCarlo() for _ in range(4)]
    pts, plis = jouer_manche(mains, contrat, premier, joueurs, regles)

    total = pts[0]
    if belote == 0 and regles["belote_pour_contrat"]:
        total += regles["points_belote"]
    return i, pos, total, plis[0] == 8


def stats(liste):
    n = len(liste)
    moyenne = sum(t for t, _ in liste) / n
    probas = [sum(t >= v for t, _ in liste) / n for v in PALIERS]
    capot = sum(c for _, c in liste) / n
    gains = [(v * (2 * p - 1), str(v)) for v, p in zip(PALIERS, probas)]
    gains.append((250 * (2 * capot - 1), "capot"))
    g, nom = max(gains)
    return moyenne, probas, capot, (nom if g > 0 else "passe")


if __name__ == "__main__":
    taches = [(i, p, 100000 * (4 * i + p) + n)
              for i in range(len(MAINS_TYPES)) for p in range(4) for n in range(NB)]
    res = {(i, p): [] for i in range(len(MAINS_TYPES)) for p in range(4)}
    debut = time.time()

    with mp.get_context("fork").Pool(os.cpu_count()) as pool:
        for k, (i, p, total, capot) in enumerate(pool.imap_unordered(une_donne, taches, chunksize=20)):
            res[(i, p)].append((total, capot))
            if (k + 1) % 5000 == 0:
                ecoule = time.time() - debut
                restant = ecoule / (k + 1) * (len(taches) - k - 1)
                print(f"  {k + 1}/{len(taches)} donnes ({ecoule / 60:.0f} min, "
                      f"encore environ {restant / 60:.0f} min)")

    entete = ["Main", "Position", "Points moyens"] + [f"P{v}" for v in PALIERS] + ["Capot", "Conseil"]
    with open("tableau_mains.csv", "w", newline="", encoding="utf-8-sig") as f:
        ecrivain = csv.writer(f, delimiter=";")
        ecrivain.writerow(entete)
        for i, (nom, _) in enumerate(MAINS_TYPES):
            print(f"\n{nom}")
            print("  Position     | Pts |  80  90 100 110 120 130 140 150 160 | Capot | Conseil")
            lignes = [(POSITIONS[p], res[(i, p)]) for p in range(4)]
            lignes.append(("Toutes", sum((res[(i, p)] for p in range(4)), [])))
            for nom_pos, liste in lignes:
                moy, probas, capot, conseil = stats(liste)
                print(f"  {nom_pos:12} | {moy:3.0f} | "
                      + " ".join(f"{100 * q:3.0f}" for q in probas)
                      + f" | {100 * capot:4.0f}% | {conseil}")
                ecrivain.writerow([nom, nom_pos, round(moy)]
                                  + [round(100 * q) for q in probas]
                                  + [round(100 * capot), conseil])

    print(f"\nTableau enregistré dans tableau_mains.csv ({(time.time() - debut) / 60:.0f} min)")
