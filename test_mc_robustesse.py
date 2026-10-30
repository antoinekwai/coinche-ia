from regles import REGLES_STANDARD
from rapide import afficher_rapide
from montecarlo import JoueurMonteCarloContrat
from experience_coinche import variante
from test_mc_encheres import MCEncheres


class MCAncien(JoueurMonteCarloContrat, variante(4)):
    nom = "MC (système d'origine)"


class MCEncheresAncien(MCAncien):
    """Annonce avec le système d'origine, mais lit les enchères selon le système corrigé."""
    nom = "MC-enchères (lecture erronée)"
    essais = 50
    imaginer = MCEncheres.imaginer


if __name__ == "__main__":
    print("=== Robustesse : adversaires qui n'annoncent pas comme prévu ===")
    afficher_rapide(MCEncheresAncien, MCAncien, 3000, REGLES_STANDARD, graine=600000)
