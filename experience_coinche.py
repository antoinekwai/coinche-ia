from regles import REGLES_STANDARD
from systeme import JoueurSysteme, nb_atouts
from match_mc import Systeme30
from partie import jouer_donne
from rapide import afficher_rapide


def force_coinche(main, contrat):
    """Force défensive dans l'atout adverse."""
    a = contrat["atout"]
    n = nb_atouts(main, a)
    force = 0
    if ("V", a) in main:
        force += 2
    if ("9", a) in main and n >= 3:
        force += 1
    force += max(0, n - 2)                      # beaucoup d'atouts
    if ("R", a) in main or ("D", a) in main:
        force += 1                              # pas de belote chez l'adversaire
    return force


class SysCoinche(JoueurSysteme):
    """Vos annonces + votre coinche (jeu de la carte à règles)."""
    nom = "SysCoinche"
    marge = 30
    seuil = 4      # force exigée contre un 80 (1 de moins tous les 20 points)

    def veut_coincher(self, main, contrat):
        exige = max(1, self.seuil - (contrat["valeur"] - 80) // 20)
        return force_coinche(main, contrat) >= exige

    def surcoincher(self, main, joueur, contrat, regles):
        return False


def variante(seuil=4, marge=30):
    class J(SysCoinche):
        pass
    J.seuil, J.marge, J.nom = seuil, marge, f"Seuil{seuil}-Marge{marge}"
    return J


def stats_coinche(classe, nb, regles):
    joueurs = [classe() for _ in range(4)]
    contrats = coinches = chutes = 0
    for i in range(nb):
        res = jouer_donne(i % 4, joueurs, regles)
        if res is None:
            continue
        contrats += 1
        if res["contrat"]["coinche"]:
            coinches += 1
            chutes += not res["reussi"]
    print(f"  {classe.nom} : {100 * coinches / contrats:.1f} % des contrats coinchés, "
          f"dont {100 * chutes / max(coinches, 1):.0f} % chutent\n")


if __name__ == "__main__":
    regles = REGLES_STANDARD
    nb = 5000

    print("=== 1. Fréquence et efficacité de votre coinche ===")
    stats_coinche(variante(4), 20000, regles)

    print("=== 2. Votre coinche contre l'ancienne ===")
    afficher_rapide(variante(4), Systeme30, nb, regles)

    print("=== 3. Quel seuil ? (contre seuil 4) ===")
    for s in [3, 5, 6]:
        afficher_rapide(variante(s), variante(4), nb, regles)

    print("=== 4. Face à un vrai coincheur, quelle marge ? (contre marge 30) ===")
    for m in [10, 20, 40]:
        afficher_rapide(variante(4, m), variante(4, 30), nb, regles)
