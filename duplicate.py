import time
import math
from regles import REGLES_STANDARD
from moteur import distribuer
from joueurs import JoueurAleatoire, JoueurRegles
from montecarlo import JoueurMonteCarlo
from partie import jouer_donne


def ecart_table(classe_a, classe_b, mains, donneur, place_a, regles):
    """Joue une donne avec l'équipe A à la place 0 (J0, J2) ou 1 (J1, J3).
    Renvoie (points de A) - (points de B)."""
    if place_a == 0:
        joueurs = [classe_a(), classe_b(), classe_a(), classe_b()]
    else:
        joueurs = [classe_b(), classe_a(), classe_b(), classe_a()]
    res = jouer_donne(donneur, joueurs, regles, mains=mains)
    if res is None:
        return 0
    s = res["scores"]
    return s[place_a] - s[1 - place_a]


def duplicate(classe_a, classe_b, nb_donnes, regles, progression=False):
    """Renvoie (écart moyen par donne en faveur de A, marge d'erreur à 95 %)."""
    resultats = []
    for i in range(nb_donnes):
        mains = distribuer()
        donneur = i % 4
        e1 = ecart_table(classe_a, classe_b, mains, donneur, 0, regles)
        e2 = ecart_table(classe_a, classe_b, mains, donneur, 1, regles)
        resultats.append((e1 + e2) / 2)
        if progression and (i + 1) % 50 == 0:
            print(f"    {i + 1}/{nb_donnes} donnes "
                  f"(écart provisoire : {sum(resultats) / len(resultats):+.1f})")

    n = len(resultats)
    moyenne = sum(resultats) / n
    variance = sum((x - moyenne) ** 2 for x in resultats) / (n - 1)
    marge = 1.96 * math.sqrt(variance / n)
    return moyenne, marge


def afficher(classe_a, classe_b, nb_donnes, regles, progression=False):
    debut = time.time()
    moyenne, marge = duplicate(classe_a, classe_b, nb_donnes, regles, progression)
    if moyenne - marge > 0:
        verdict = f"{classe_a.nom} est meilleur"
    elif moyenne + marge < 0:
        verdict = f"{classe_b.nom} est meilleur"
    else:
        verdict = "pas de différence prouvée"
    print(f"  {classe_a.nom} contre {classe_b.nom} ({nb_donnes} donnes) : "
          f"{moyenne:+.1f} ± {marge:.1f} points par donne -> {verdict} "
          f"({time.time() - debut:.0f} s)\n")


if __name__ == "__main__":
    regles = REGLES_STANDARD

    print("=== Test de contrôle (doit donner environ 0) ===")
    afficher(JoueurRegles, JoueurRegles, 2000, regles)

    print("=== Règles contre Aléatoire ===")
    afficher(JoueurRegles, JoueurAleatoire, 2000, regles)

    print("=== MonteCarlo contre Règles ===")
    afficher(JoueurMonteCarlo, JoueurRegles, 300, regles, progression=True)
