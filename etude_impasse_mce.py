import os
import random
import multiprocessing as mp
from collections import defaultdict
from regles import REGLES_STANDARD
from moteur import distribuer, gagnant_pli
from partie import jouer_donne
from ia_joueur import JoueurIA
from etude_atout import resume
from test_mc_encheres import MCEncheres


NB = 40000
GRAINE = 18000000


class Testeur(MCEncheres):
    option = "libre"      # "as", "petite" ou "libre"
    etat = None
    mains_init = None

    def jouer_carte(self, main, jouables, pli, contrat, joueur, regles):
        a, e = contrat["atout"], self.etat
        cible = False
        if not e["fait"] and pli:
            x = pli[0][1][1]
            vues = {c for _, c in self.historique}       # inclut le pli en cours
            if (x != a and ("A", x) in jouables
                    and ("10", x) not in main and ("10", x) not in vues
                    and gagnant_pli(pli + [(joueur, ("A", x))], a)[0] == joueur):
                petites = [c for c in jouables if c[1] == x and c[0] != "A"]
                if petites:
                    cible = True
                    e["fait"] = True
                    e["equipe"] = joueur % 2
                    detenteur = next(p for p in range(4) if ("10", x) in self.mains_init[p])
                    place = {(joueur + 1) % 4: "joueur suivant", (joueur + 2) % 4: "partenaire",
                             (joueur + 3) % 4: "joueur précédent"}[detenteur]
                    longueur = sum(1 for c in main if c[1] == x)
                    plis_faits = (len(self.historique) - len(pli)) // 4
                    camp = "attaque" if contrat["joueur"] % 2 == joueur % 2 else "défense"
                    e["infos"] = {
                        "1. Camp": camp,
                        "2. Position": f"{len(pli) + 1}e",
                        "3. Entame par": "partenaire" if pli[0][0] == (joueur + 2) % 4 else "adversaire",
                        "4. Longueur": "As + 1" if longueur == 2 else "As + 2 ou plus",
                        "5. Moment": "plis 1-3" if plis_faits < 3 else "plis 4-8",
                        "6. 10 chez (caché)": place,
                        "7. Camp × position": f"{camp} / {len(pli) + 1}e",
                        "8. Maître du pli": "partenaire" if gagnant_pli(pli, a)[0] == (joueur + 2) % 4 else "adversaire",
                        "9. Maître × position": ("partenaire" if gagnant_pli(pli, a)[0] == (joueur + 2) % 4 else "adversaire") + f" / {len(pli) + 1}e",
                        "10. Maître adverse × 10 chez": (place if gagnant_pli(pli, a)[0] != (joueur + 2) % 4 else "partenaire maître"),

                    }
                    if self.option == "as":
                        jouables = [("A", x)]
                    elif self.option == "petite":
                        jouables = petites
        carte = super().jouer_carte(main, jouables, pli, contrat, joueur, regles)
        if cible:
            e["joue_as"] = carte[0] == "A"
        return carte


def une_donne(numero):
    res = {}
    for option in ("as", "petite"):
        random.seed(numero)                   # même hasard pour les deux versions
        mains = distribuer()
        etat = {"fait": False}
        joueurs = [Testeur() for _ in range(4)]
        for j in joueurs:
            j.option, j.etat, j.mains_init = option, etat, mains
        r = jouer_donne(numero % 4, joueurs, REGLES_STANDARD, mains=mains)
        if r is None or not etat["fait"]:
            return None
        eq = etat["equipe"]
        res[option] = (r["scores"][eq] - r["scores"][1 - eq], etat)
    e = res["as"][1]
    return e["infos"], res["as"][0] - res["petite"][0], False



if __name__ == "__main__":
    with mp.get_context("fork").Pool(os.cpu_count()) as pool:
        cas = [c for c in pool.imap_unordered(une_donne, range(GRAINE, GRAINE + NB), chunksize=200)
               if c is not None]
    n, m, marge = resume([d for _, d, _ in cas])
    part = 100 * sum(j for _, _, j in cas) / n
    print(f"{n} situations sur {NB} donnes : As − petite = {m:+.1f} ± {marge:.1f} "
          f"(l'IA libre joue l'As {part:.0f} %)")

    groupes = defaultdict(list)
    for infos, d, j in cas:
        for facteur, valeur in infos.items():
            groupes[(facteur, valeur)].append((d, j))

    courant = None
    for (facteur, valeur) in sorted(groupes):
        if facteur != courant:
            print(f"\n{facteur}")
            courant = facteur
        liste = groupes[(facteur, valeur)]
        n, m, marge = resume([d for d, _ in liste])
        part = 100 * sum(j for _, j in liste) / n
        print(f"   {valeur:30} | {n:6} cas | As − petite : {m:+6.1f} ± {marge:4.1f} | IA joue l'As {part:3.0f} %")
