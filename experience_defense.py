from regles import REGLES_STANDARD
from montecarlo import JoueurMonteCarloContrat
from systeme_corrige import SysCorrige
from rapide import afficher_rapide


def var(nom, reponse=False, belote=0, marge=30, plafond=130):
    class J(SysCorrige):
        pass
    J.nom, J.ouvreur_compte_reponse, J.bonus_belote = nom, reponse, belote
    J.marge, J.plafond = marge, plafond
    return J


def mc(classe):
    return type(classe.nom + "-MC", (JoueurMonteCarloContrat, classe), {"nom": classe.nom + "-MC"})


if __name__ == "__main__":
    regles = REGLES_STANDARD
    base = SysCorrige
    nb = 15000

    print("=== 1. Niveau de l'équipe ===")
    afficher_rapide(var("Réponse", reponse=True), base, nb, regles)
    afficher_rapide(var("Réponse-marge20", reponse=True, marge=20), base, nb, regles)

    print("=== 2. Belote ===")
    afficher_rapide(var("Belote10", belote=10), base, nb, regles)
    afficher_rapide(var("Belote20", belote=20), base, nb, regles)

    print("=== 3. Combinaison et plafond ===")
    afficher_rapide(var("Rép+Bel20", reponse=True, belote=20), base, nb, regles)
    for p in (140, 150, 160):
        afficher_rapide(var(f"Rép+Bel20-plaf{p}", reponse=True, belote=20, plafond=p),
                        base, nb, regles)
