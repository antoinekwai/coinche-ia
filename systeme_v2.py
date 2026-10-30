from regles import REGLES_STANDARD
from systeme import nb_atouts, nb_as
from systeme_corrige import niveau_corrige, SysCorrige
from montecarlo import JoueurMonteCarloContrat
from rapide import afficher_rapide



def niveau_v2(main, a):
    base = niveau_corrige(main, a)
    n, nas = nb_atouts(main, a), nb_as(main, a)
    v, neuf = ("V", a) in main, ("9", a) in main
    c = 0
    if v and neuf:
        if n == 2 and nas >= 1:
            c = {1: 80, 2: 90}.get(nas, 100)        # V 9 secs
        if n == 3 and nas >= 2:
            c = 110
        if n == 4 and nas >= 2:
            c = 120
        if n >= 6:
            c = 120
    elif v:                                          # valet sans le 9
        if n >= 5:
            c = 110 if nas >= 1 else 100
        elif n == 4:
            c = 110 if nas >= 2 else (100 if nas == 1 else 0)
        elif n == 3 and nas >= 3:
            c = 100
    elif neuf:                                       # 9 sans le valet
        if (n >= 4 and nas >= 2) or (n >= 5 and nas >= 1):
            c = 90
    return max(base, c)


class SysV2(SysCorrige):
    nom = "Corrigé-v2"

    def niveau(self, main, a):
        return niveau_v2(main, a)


class V2MC(JoueurMonteCarloContrat, SysV2):
    nom = "Corrigé-v2-MC"


if __name__ == "__main__":
    from ia_joueur import JoueurIA
    from verif_encheres_ia import avec_ia
    from ia_evaluer import CorrigeMC
    print("=== Confirmation avec Monte Carlo classique (16 000 donnes) ===")
    afficher_rapide(V2MC, CorrigeMC, 16000, REGLES_STANDARD, graine=700000)

