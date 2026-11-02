from regles import REGLES_STANDARD
from moteur import distribuer
from match_mc import Systeme30, SystemeMCContrat
from experience_audace import joueur_audace
from partie import jouer_donne


def tester(seuil, nb_capots, regles, max_donnes=100000):
    class Annonce(Systeme30):
        seuil_capot = seuil
    class Jeu(SystemeMCContrat):
        seuil_capot = seuil
    adv = joueur_audace(20)
    trouves = reussis = donnes = 0

    while trouves < nb_capots and donnes < max_donnes:
        mains = distribuer()
        donnes += 1
        res = jouer_donne(0, [Annonce(), adv(), Annonce(), adv()], regles, mains=mains)
        if res is None or not res["contrat"]["capot"] or res["contrat"]["joueur"] % 2 != 0:
            continue
        trouves += 1
        r = jouer_donne(0, [Jeu(), adv(), Jeu(), adv()], regles, mains=mains)
        reussis += r["reussi"]

    if trouves == 0:
        print(f"  Seuil {seuil} : aucun capot annoncé en {donnes} donnes\n")
        return
    p = reussis / trouves
    print(f"  Seuil {seuil} : {reussis}/{trouves} réussis ({100 * p:.0f} %), "
          f"1 capot toutes les {donnes // trouves} donnes, "
          f"gain moyen par capot : {250 * (2 * p - 1):+.0f}\n")


if __name__ == "__main__":
    for seuil in [8, 9, 10]:
        tester(seuil, 40, REGLES_STANDARD)
