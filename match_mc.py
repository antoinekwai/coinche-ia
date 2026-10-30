from regles import REGLES_STANDARD
from moteur import distribuer
from systeme import JoueurSysteme
from montecarlo import JoueurMonteCarlo
from experience_audace import joueur_audace
from duplicate import afficher
from partie import jouer_donne


class Systeme30(JoueurSysteme):
    """Vos annonces (marge 30, plafond 130), jeu de la carte à règles."""
    nom = "Sys30"
    marge = 30


class SystemeMC(JoueurMonteCarlo, JoueurSysteme):
    """Vos annonces (marge 30, plafond 130), jeu de la carte Monte Carlo (objectif points)."""
    nom = "SysMC-points"
    marge = 30
    objectif = "points"


class SystemeMCContrat(SystemeMC):
    """Idem, mais Monte Carlo cherche à gagner le contrat."""
    nom = "SysMC-contrat"
    objectif = "contrat"


def comparer_capots(nb_capots, regles):
    """Cherche des donnes où votre système annonce capot, puis les fait jouer
    par les 3 joueurs (mêmes cartes, mêmes annonces). Compte les capots réussis."""
    adv = joueur_audace(20)
    classes = [Systeme30, SystemeMC, SystemeMCContrat]
    reussis = {c.nom: 0 for c in classes}
    trouves = 0
    while trouves < nb_capots:
        mains = distribuer()
        res = jouer_donne(0, [Systeme30(), adv(), Systeme30(), adv()], regles, mains=mains)
        if res is None or not res["contrat"]["capot"] or res["contrat"]["joueur"] % 2 != 0:
            continue
        trouves += 1
        for c in classes:
            r = jouer_donne(0, [c(), adv(), c(), adv()], regles, mains=mains)
            reussis[c.nom] += r["reussi"]
    for nom, n in reussis.items():
        print(f"  {nom:14} : {n}/{nb_capots} capots réussis ({100 * n / nb_capots:.0f} %)")
    print()


if __name__ == "__main__":
    regles = REGLES_STANDARD
    adv = joueur_audace(20)

    print("=== 1. Référence : vos annonces + jeu à règles ===")
    afficher(Systeme30, adv, 5000, regles)

    print("=== 2. Vos annonces + Monte Carlo (objectif points) ===")
    afficher(SystemeMC, adv, 500, regles, progression=True)

    print("=== 3. Vos annonces + Monte Carlo (objectif contrat) ===")
    afficher(SystemeMCContrat, adv, 500, regles, progression=True)

    print("=== 4. Duel direct : objectif contrat contre objectif points ===")
    afficher(SystemeMCContrat, SystemeMC, 300, regles, progression=True)

    print("=== 5. Qui joue le mieux les capots ? (50 capots annoncés) ===")
    comparer_capots(50, regles)
