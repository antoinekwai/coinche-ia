from regles import REGLES_STANDARD
from ia_joueur import JoueurIA
from rapide import afficher_rapide


def ia_var(nom, marge=30, seuil=4):
    class J(JoueurIA):
        pass
    J.nom, J.marge, J.seuil = nom, marge, seuil
    return J


if __name__ == "__main__":
    regles = REGLES_STANDARD
    ref = ia_var("IA-réf")          # marge 30, coinche seuil 4
    nb = 15000

    print("=== 1. Marge dans les enchères disputées (contre marge 30) ===")
    for m in (10, 20, 40, 50):
        afficher_rapide(ia_var(f"IA-marge{m}", marge=m), ref, nb, regles)

    print("=== 2. Seuil de coinche (contre seuil 4) ===")
    for s in (3, 5):
        afficher_rapide(ia_var(f"IA-coinche{s}", seuil=s), ref, nb, regles)
