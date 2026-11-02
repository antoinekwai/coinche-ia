from collections import Counter
from regles import REGLES_STANDARD
from partie import jouer_donne
from systeme_corrige import SysCorrige
from dispute import JoueurDispute
from rapide import afficher_rapide


class DisputeCompteur(JoueurDispute):
    """Même joueur, mais il note chacune de ses décisions (pour les statistiques)."""
    decisions = Counter()

    def decision_disputee(self, main, joueur, contrat, regles, a, valeur):
        d = super().decision_disputee(main, joueur, contrat, regles, a, valeur)
        nom = "marge (repli)" if d is None else (d if isinstance(d, str) else "monter")
        DisputeCompteur.decisions[nom] += 1
        return d


def statistiques(nb, regles):
    """Ce que décide le joueur 'Disputé' quand les adversaires parlent."""
    joueurs = [DisputeCompteur(), SysCorrige(), DisputeCompteur(), SysCorrige()]
    for i in range(nb):
        jouer_donne(i % 4, joueurs, regles)
    total = sum(DisputeCompteur.decisions.values())
    print(f"  {total} décisions disputées sur {nb} donnes :")
    for nom, n in DisputeCompteur.decisions.most_common():
        print(f"    {nom:14} : {n:5} ({100 * n / total:.0f} %)")
    print()


if __name__ == "__main__":
    regles = REGLES_STANDARD

    print("=== 1. Que décide la simulation ? (300 donnes) ===")
    statistiques(300, regles)

    print("=== 2. Duel : enchères disputées par simulation contre système corrigé ===")
    afficher_rapide(JoueurDispute, SysCorrige, 3000, regles)
