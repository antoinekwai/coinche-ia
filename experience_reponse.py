from regles import REGLES_STANDARD
from systeme import nb_atouts, nb_as, increment_reponse
from systeme_v2 import SysV2, V2MC
from montecarlo import JoueurMonteCarloContrat
from verif_encheres_ia import avec_ia
from rapide import afficher_rapide


def reponse_variante(mode):
    def reponse(self, main, ouverture, a):
        inc = increment_reponse(main, ouverture, a)
        if ouverture != 80:
            return inc
        n, nas = nb_atouts(main, a), nb_as(main, a)
        if n > (1 if mode == "court" else 0):
            return inc
        tetes = inc - 10 * nas                    # ce que rapportent le V et le 9
        return tetes if mode == "zero" else tetes + 10 * (nas // 2)
    return reponse


def sys_var(nom, mode):
    return type(nom, (SysV2,), {"nom": nom, "reponse": reponse_variante(mode)})


def mc_var(nom, mode):
    return type(nom, (JoueurMonteCarloContrat, SysV2),
                {"nom": nom, "reponse": reponse_variante(mode)})


MODES = [("Zéro", "zero"), ("Deux-as", "deux_as"), ("Court", "court")]

if __name__ == "__main__":
    regles = REGLES_STANDARD
    print("=== 1. Exploration avec l'IA (contre v2) ===")
    ref_ia = avec_ia(SysV2, "IA-v2")
    for nom, mode in MODES:
        afficher_rapide(avec_ia(sys_var(nom, mode), f"IA-{nom}"), ref_ia, 15000, regles)

    print("=== 2. Confirmation avec Monte Carlo classique (juge neutre) ===")
    for nom, mode in MODES:
        afficher_rapide(mc_var(f"{nom}-MC", mode), V2MC, 8000, regles, graine=800000)
