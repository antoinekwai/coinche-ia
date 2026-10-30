import math
import os
import random
import time
import multiprocessing as mp
from moteur import distribuer
from duplicate import ecart_table

_CONFIG = None   # (classe_a, classe_b, regles), transmis aux cœurs de calcul


def _une_donne(numero):
    classe_a, classe_b, regles = _CONFIG
    random.seed(numero)                 # même numéro = même donne
    mains = distribuer()
    donneur = numero % 4
    e1 = ecart_table(classe_a, classe_b, mains, donneur, 0, regles)
    e2 = ecart_table(classe_a, classe_b, mains, donneur, 1, regles)
    return (e1 + e2) / 2


def afficher_rapide(classe_a, classe_b, nb_donnes, regles, graine=0):
    global _CONFIG
    _CONFIG = (classe_a, classe_b, regles)
    debut = time.time()
    resultats = []

    with mp.get_context("fork").Pool(os.cpu_count()) as pool:
        for r in pool.imap(_une_donne, range(graine, graine + nb_donnes), chunksize=5):
            resultats.append(r)
            if len(resultats) % 5000 == 0:
                print(f"    {len(resultats)}/{nb_donnes} donnes "
                      f"(écart provisoire : {sum(resultats) / len(resultats):+.1f})")

    n = len(resultats)
    moyenne = sum(resultats) / n
    variance = sum((x - moyenne) ** 2 for x in resultats) / (n - 1)
    marge = 1.96 * math.sqrt(variance / n)
    if moyenne - marge > 0:
        verdict = f"{classe_a.nom} est meilleur"
    elif moyenne + marge < 0:
        verdict = f"{classe_b.nom} est meilleur"
    else:
        verdict = "pas de différence prouvée"
    print(f"  {classe_a.nom} contre {classe_b.nom} ({n} donnes) : "
          f"{moyenne:+.1f} ± {marge:.1f} points par donne -> {verdict} "
          f"({time.time() - debut:.0f} s, {os.cpu_count()} cœurs)\n")


if __name__ == "__main__":
    from regles import REGLES_STANDARD
    from joueurs import JoueurRegles
    from montecarlo import JoueurMonteCarlo
    from match_mc import SystemeMCContrat
    from experience_signaux import variante

    regles = REGLES_STANDARD

    print("=== Contrôle de vitesse (avant : 19 s sur un seul cœur) ===")
    afficher_rapide(JoueurMonteCarlo, JoueurRegles, 300, regles)

    print("=== Apport de la lecture des signaux (confiance 0.8 contre 0) ===")
    afficher_rapide(variante(0.8), variante(0), 3000, regles)

    print("=== Bilan global : signaux contre sans signaux ===")
    afficher_rapide(variante(0.8), SystemeMCContrat, 3000, regles)
