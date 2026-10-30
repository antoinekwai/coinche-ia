import time
from regles import REGLES_STANDARD
from joueurs import JoueurAleatoire, JoueurRegles
from montecarlo import JoueurMonteCarlo
from partie import jouer_donne, jouer_partie


def match(classe_a, classe_b, nb_parties, regles, progression=False):
    """Fait jouer l'équipe A contre l'équipe B. Renvoie le % de victoires de A.
    On alterne les places pour que ce soit équitable."""
    victoires_a = 0
    for i in range(nb_parties):
        if i % 2 == 0:
            joueurs = [classe_a(), classe_b(), classe_a(), classe_b()]
            equipe_a = 0
        else:
            joueurs = [classe_b(), classe_a(), classe_b(), classe_a()]
            equipe_a = 1
        gagnant, _, _ = jouer_partie(joueurs, regles)
        if gagnant == equipe_a:
            victoires_a += 1
        if progression and (i + 1) % 10 == 0:
            print(f"    {i + 1}/{nb_parties} parties jouées "
                  f"({100 * victoires_a / (i + 1):.1f} % pour {classe_a.nom})")
    return 100 * victoires_a / nb_parties


def stats_donnes(classe_a, classe_b, nb_donnes, regles):
    """Statistiques détaillées sur les contrats (équipe 0 = A, équipe 1 = B)."""
    joueurs = [classe_a(), classe_b(), classe_a(), classe_b()]
    pris, reussis, marques = [0, 0], [0, 0], [0, 0]

    for i in range(nb_donnes):
        res = jouer_donne(i % 4, joueurs, regles)
        if res is None:
            continue
        eq = res["contrat"]["joueur"] % 2
        pris[eq] += 1
        if res["reussi"]:
            reussis[eq] += 1
        marques[0] += res["scores"][0]
        marques[1] += res["scores"][1]

    for eq, classe in [(0, classe_a), (1, classe_b)]:
        taux = 100 * reussis[eq] / pris[eq] if pris[eq] else 0
        print(f"  {classe.nom:10} : {pris[eq]:5} contrats pris, {taux:5.1f} % réussis, "
              f"{marques[eq] / nb_donnes:6.1f} points marqués par donne")


if __name__ == "__main__":
    regles = REGLES_STANDARD

    # 1. Une donne détaillée pour voir jouer le joueur Monte Carlo
    print("=== Exemple : MonteCarlo (J0, J2) contre Règles (J1, J3) ===")
    joueurs = [JoueurMonteCarlo(), JoueurRegles(), JoueurMonteCarlo(), JoueurRegles()]
    resultat = None
    while resultat is None:
        resultat = jouer_donne(0, joueurs, regles, afficher=True)

    # 2. Le tournoi (Monte Carlo est plus lent : on joue moins de parties)
    nb = 100
    print(f"=== Tournoi MonteCarlo contre Règles sur {nb} parties ===")
    debut = time.time()
    pct = match(JoueurMonteCarlo, JoueurRegles, nb, regles, progression=True)
    print(f"  MonteCarlo gagne {pct:.1f} % des parties "
          f"({time.time() - debut:.0f} secondes)\n")

    # 3. Statistiques sur les contrats
    print("=== Statistiques sur 500 donnes ===")
    stats_donnes(JoueurMonteCarlo, JoueurRegles, 500, regles)
