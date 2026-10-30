from regles import REGLES_STANDARD
from experience_coinche import force_coinche
from experience_reponse import sys_var, reponse_variante
from montecarlo import JoueurMonteCarloContrat
from systeme_v2 import SysV2
from verif_encheres_ia import avec_ia
from rapide import afficher_rapide

SysV3 = sys_var("Système-v3", "court")      # système actuel (v2 + réponse sur 80)


def coinche_variante(compte_as, compte_encheres, minimum):
    def veut_coincher(self, main, contrat):
        a = contrat["atout"]
        f = force_coinche(main, contrat)
        if compte_as:
            f += sum(1 for c in main if c[0] == "A" and c[1] != a)
        exige = (5 if compte_as else 4) - (contrat["valeur"] - 80) // 20
        if compte_encheres:
            defense = 1 - contrat["joueur"] % 2
            disputee = any(isinstance(d, tuple) and j % 2 == defense for j, d in self.encheres)
            exige += -1 if disputee else 1
        return f >= max(minimum, exige)
    return veut_coincher


VARIANTES = [("Min2", (False, False, 2)), ("Enchères", (False, True, 2)),
             ("As", (True, False, 2)), ("As+Enchères", (True, True, 2))]


def sys_coinche(nom, params, mc=False):
    bases = (JoueurMonteCarloContrat, SysV2) if mc else (SysV2,)
    return type(nom, bases, {"nom": nom, "reponse": reponse_variante("court"),
                             "veut_coincher": coinche_variante(*params)})


if __name__ == "__main__":
    regles = REGLES_STANDARD
    print("=== 1. Exploration avec l'IA (contre le système actuel) ===")
    ref_ia = avec_ia(SysV3, "IA-v3")
    for nom, p in VARIANTES:
        afficher_rapide(avec_ia(sys_coinche(nom, p), f"IA-{nom}"), ref_ia, 15000, regles)

    print("=== 2. Confirmation avec Monte Carlo classique ===")
    ref_mc = type("v3-MC", (JoueurMonteCarloContrat, SysV2),
                  {"nom": "v3-MC", "reponse": reponse_variante("court")})
    for nom, p in VARIANTES:
        afficher_rapide(sys_coinche(f"{nom}-MC", p, mc=True), ref_mc, 8000, regles, graine=900000)
