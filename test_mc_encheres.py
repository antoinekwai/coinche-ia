from regles import REGLES_STANDARD
from rapide import afficher_rapide
from montecarlo import imaginer_mains
from dispute import coherent
from ia_evaluer import CorrigeMC


class MC10(CorrigeMC):
    nom = "MC10"

    def __init__(self):
        super().__init__(10)


class MCEncheres(CorrigeMC):
    """Monte Carlo qui n'imagine que des mains compatibles avec les enchères."""
    nom = "MC-enchères"
    essais = 50

    def imaginer(self, main, joueur, manque, atout):
        autres = [p for p in range(4) if p != joueur]
        jouees = {p: [c for j, c in self.historique if j == p] for p in autres}
        mains = None
        for _ in range(self.essais):
            mains = imaginer_mains(main, joueur, self.historique, manque)
            # main de départ de chaque joueur = cartes imaginées + cartes déjà jouées
            if all(coherent(mains[p] + jouees[p], p, self.encheres) for p in autres):
                return mains
        return mains          # rien de cohérent trouvé : on garde le dernier tirage


if __name__ == "__main__":
    regles = REGLES_STANDARD
    print("=== 1. Coût de 10 donnes imaginées au lieu de 20 ===")
    afficher_rapide(MC10, CorrigeMC, 3000, regles, graine=600000)
    print("=== 2. Monte Carlo qui tient compte des enchères ===")
    afficher_rapide(MCEncheres, CorrigeMC, 3000, regles, graine=600000)
