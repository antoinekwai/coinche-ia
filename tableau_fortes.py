import csv
import os
import random
import time
import multiprocessing as mp
from moteur import COULEURS, RANGS, equipe_belote
from regles import REGLES_STANDARD
from montecarlo import JoueurMonteCarlo, JoueurMonteCarloContrat
from partie import jouer_manche
from mains_types import MAINS_TYPES, generer_main, ATOUT

NB = 3000                                             # donnes par main
PALIERS = [80, 90, 100, 110, 120, 130, 140, 150, 160]
INDICES = [4, 9] + list(range(27, 48))                # mains 5 et 10 (comparaison) + mains 28 à 34


def une_donne(tache):
    """Même donne jouée deux fois : pour les points, puis en visant le capot."""
    i, numero = tache
    regles = REGLES_STANDARD
    random.seed(numero)
    main = generer_main(MAINS_TYPES[i][1])
    reste = [(r, c) for c in COULEURS for r in RANGS if (r, c) not in main]
    random.shuffle(reste)
    mains = [main, reste[0:8], reste[8:16], reste[16:24]]
    premier = random.randrange(4)                     # position au hasard ("Toutes")

    belote = equipe_belote(mains, ATOUT)
    bonus = regles["points_belote"] if belote == 0 and regles["belote_pour_contrat"] else 0

    # 1. Pour les points
    contrat = {"valeur": 80, "atout": ATOUT, "joueur": 0, "coinche": 0, "capot": False}
    joueurs = [JoueurMonteCarlo() for _ in range(4)]
    pts, _ = jouer_manche([m[:] for m in mains], contrat, premier, joueurs, regles)

    # 2. En visant le capot (la défense cherche à faire un pli)
    contrat_capot = dict(contrat, valeur=regles["valeur_capot"], capot=True)
    joueurs = [JoueurMonteCarloContrat() for _ in range(4)]
    _, plis = jouer_manche([m[:] for m in mains], contrat_capot, premier, joueurs, regles)

    return i, pts[0] + bonus, plis[0] == 8


if __name__ == "__main__":
    taches = [(i, 1000000 + 100000 * i + n) for i in INDICES for n in range(NB)]
    res = {i: [] for i in INDICES}
    debut = time.time()

    with mp.get_context("fork").Pool(os.cpu_count()) as pool:
        for k, (i, total, capot) in enumerate(pool.imap_unordered(une_donne, taches, chunksize=20)):
            res[i].append((total, capot))
            if (k + 1) % 2000 == 0:
                ecoule = time.time() - debut
                restant = ecoule / (k + 1) * (len(taches) - k - 1)
                print(f"  {k + 1}/{len(taches)} donnes ({ecoule / 60:.0f} min, "
                      f"encore environ {restant / 60:.0f} min)")

    print("\nMain                               | Pts |  80  90 100 110 120 130 140 150 160 | Capot | 80 % | Gain")
    with open("tableau_mains3.csv", "w", newline="", encoding="utf-8-sig") as f:
        ecrivain = csv.writer(f, delimiter=";")
        ecrivain.writerow(["Main", "Points moyens"] + [f"P{v}" for v in PALIERS]
                          + ["Capot visé", "Annonce 80 %", "Annonce gain"])
        for i in INDICES:
            liste = res[i]
            n = len(liste)
            moy = sum(t for t, _ in liste) / n
            probas = [sum(t >= v for t, _ in liste) / n for v in PALIERS]
            capot = sum(c for _, c in liste) / n

            # Annonce "80 %" : le plus haut niveau réussi au moins 80 % du temps
            a80 = "capot" if capot >= 0.8 else next(
                (str(v) for v, p in reversed(list(zip(PALIERS, probas))) if p >= 0.8), "passe")
            # Annonce "gain" : meilleur gain moyen V × (2p − 1)
            gains = [(v * (2 * p - 1), str(v)) for v, p in zip(PALIERS, probas)]
            gains.append((250 * (2 * capot - 1), "capot"))
            g, a_gain = max(gains)
            a_gain = a_gain if g > 0 else "passe"

            nom = MAINS_TYPES[i][0]
            print(f"{nom:34} | {moy:3.0f} | " + " ".join(f"{100 * q:3.0f}" for q in probas)
                  + f" | {100 * capot:4.0f}% | {a80:>5} | {a_gain}")
            ecrivain.writerow([nom, round(moy)] + [round(100 * q) for q in probas]
                              + [round(100 * capot), a80, a_gain])

    print(f"\nTableau enregistré dans tableau_mains3.csv ({(time.time() - debut) / 60:.0f} min)")
