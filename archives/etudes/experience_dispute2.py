from regles import REGLES_STANDARD
from systeme_corrige import SysCorrige
from dispute import JoueurDispute
from experience_dispute import statistiques
from rapide import afficher_rapide


class DisputeNaif(JoueurDispute):
    """Ancienne version : ne prévoit pas la coinche adverse."""
    nom = "Disputé-naïf"
    prevoir_coinche = False


if __name__ == "__main__":
    regles = REGLES_STANDARD
    nb = 15000

    print("=== 1. Que décide la nouvelle version ? (300 donnes) ===")
    statistiques(300, regles)

    print("=== 2. Ancienne version contre système corrigé ===")
    afficher_rapide(DisputeNaif, SysCorrige, nb, regles)

    print("=== 3. Nouvelle version contre système corrigé ===")
    afficher_rapide(JoueurDispute, SysCorrige, nb, regles)

    print("=== 4. Duel direct : nouvelle contre ancienne ===")
    afficher_rapide(JoueurDispute, DisputeNaif, nb, regles)
