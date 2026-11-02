import random
from regles import REGLES_STANDARD
from rapide import afficher_rapide
from montecarlo import JoueurMonteCarloContrat, manques
from moteur import COULEURS, RANGS, cartes_jouables, gagnant_pli, points
from experience_coinche import variante
from systeme_v2 import SysV2, niveau_v2


class MCEncheres(JoueurMonteCarloContrat, SysV2):
    """Monte Carlo avec échantillonnage pur : ne conserve QUE des donnes conformes aux annonces."""
    nom = "MC-enchères"
    essais = 120

    def imaginer(self, main, joueur, manque, atout):
        autres = [p for p in range(4) if p != joueur]
        toutes_vues = set(main) | {c for _, c in self.historique}
        inconnues = [(r, c) for c in COULEURS for r in RANGS if (r, c) not in toutes_vues]

        def coherent_strict(m_p, p):
            for j, d in self.encheres:
                if isinstance(d, tuple) and j == p:
                    val, coul = d
                    if niveau_v2(m_p, coul) < max(80, val - 10):
                        return False
                elif d == "passe" and j == p:
                    idx = self.encheres.index((j, d))
                    if idx < 4 and max(niveau_v2(m_p, c) for c in COULEURS) >= 80:
                        return False
            return True

        valides = []
        dernier_tirage = None

        for _ in range(self.essais):
            random.shuffle(inconnues)
            m = [None] * 4
            m[joueur] = list(main)

            cur = 0
            for p in autres:
                nb_p = 8 - sum(1 for j, c in self.historique if j == p)
                m[p] = inconnues[cur:cur + nb_p]
                cur += nb_p

            dernier_tirage = m
            coupes_ok = all(all(c[1] not in manque[p] for c in m[p]) for p in autres)
            if coupes_ok and all(coherent_strict(m[p], p) for p in autres):
                valides.append(m)
                if len(valides) >= 15:
                    break

        if len(valides) >= 3:
            return random.choice(valides)

        return dernier_tirage


class MC10(MCEncheres):
    nom = "MC10"

    def __init__(self):
        super().__init__(10)


if __name__ == "__main__":
    from ia_evaluer import CorrigeMC
    regles = REGLES_STANDARD
    print("=== 1. Coût de 10 donnes imaginées au lieu de 20 ===")
    afficher_rapide(MC10, CorrigeMC, 3000, regles, graine=600000)
    print("=== 2. Monte Carlo qui tient compte des enchères ===")
    afficher_rapide(MCEncheres, CorrigeMC, 3000, regles, graine=600000)
