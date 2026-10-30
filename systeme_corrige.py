from collections import Counter
from regles import REGLES_STANDARD
from systeme import nb_atouts, nb_as, plis_surs
from joueurs import estimer
from experience_coinche import SysCoinche, variante
from joueur_reseau import joueur_reseau
from mains_types import MAINS_TYPES, generer_main, ATOUT
from rapide import afficher_rapide


def niveau_corrige(main, a):
    n, nas = nb_atouts(main, a), nb_as(main, a)
    valet, neuf = ("V", a) in main, ("9", a) in main
    as_atout = ("A", a) in main
    belote = ("R", a) in main and ("D", a) in main

    if n >= 4 and plis_surs(main, a) == len(main):
        return 250
        # Mains très fortes (tableau des mains fortes)
    cotes = {c for (r, c) in main if c != a}
    if valet and neuf and n >= 5 and (nas >= 2 or (n >= 6 and nas >= 1) or len(cotes) == 1):
        return 140

    if estimer(main, a) >= 130:
        return 130
    # Règle 5 : V et 9 avec 4-5 atouts et un as
    if valet and neuf and n >= 5 and nas >= 1:
        return 120
    if valet and neuf and n >= 4 and nas >= 1:
        return 110
    if valet and neuf and n >= 5:                      # 5 atouts V 9, sans as
        return 110

    # 100
    if valet and as_atout and belote:                  # V A R D
        return 100
    if valet and neuf and n >= 4:
        return 100
    # 90
    if as_atout and belote and n >= 5:                 # A R D + 2 petits
        return 90
    if valet and neuf and n >= 3 and nas >= 1:
        return 90
    if valet and n >= 3 and nas >= 2:                  # Règle 4
        return 90
    # 80
    if valet and neuf and n >= 3:                      # V 9 troisièmes, sans as
        return 80

    if valet and n >= 3 and (nas >= 1 or as_atout or belote):   # Règle 3
        return 80
    if valet and n >= 4:                               # Règle 2
        return 80
    if neuf and (n >= 4 or (n >= 3 and nas >= 2)):     # Règle 1
        return 80
    return 0


class SysCorrige(SysCoinche):
    """Votre système complet, avec les ouvertures corrigées."""
    nom = "Corrigé"

    def niveau(self, main, a):
        return niveau_corrige(main, a)


if __name__ == "__main__":
    print("=== Vérification : ouverture la plus fréquente par main type ===")
    for nom, spec in MAINS_TYPES:
        c = Counter(niveau_corrige(generer_main(spec), ATOUT) for _ in range(200))
        niv, _ = c.most_common(1)[0]
        print(f"  {nom:34} -> {'passe' if niv == 0 else niv}")
    print()

    regles = REGLES_STANDARD
    ref = variante(4)        # votre système actuel
    reseau = joueur_reseau(0.8)

    print("=== Système corrigé contre votre système ===")
    afficher_rapide(SysCorrige, ref, 5000, regles)

    print("=== Rappel : réseau contre votre système ===")
    afficher_rapide(reseau, ref, 5000, regles)

    print("=== Duel direct : réseau contre système corrigé ===")
    afficher_rapide(reseau, SysCorrige, 5000, regles)
