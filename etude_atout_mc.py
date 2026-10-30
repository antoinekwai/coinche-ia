import os
import random
import multiprocessing as mp
from collections import defaultdict
from regles import REGLES_STANDARD
from moteur import distribuer
from partie import jouer_donne
from montecarlo import JoueurMonteCarloContrat
from systeme_corrige import SysCorrige
from etude_atout import resume

NB = 20000
GRAINE = 7000000


class TesteurMC(JoueurMonteCarloContrat, SysCorrige):
    option = "libre"
    etat = None

    def jouer_carte(self, main, jouables, pli, contrat, joueur, regles):
        a, e = contrat["atout"], self.etat
        cible = False
        if (not e["fait"] and not pli and not contrat["capot"]
                and joueur == (contrat["joueur"] + 2) % 4):
            atouts = [c for c in jouables if c[1] == a]
            autres = [c for c in jouables if c[1] != a]
            valet_connu = ("V", a) in main or any(c == ("V", a) for _, c in self.historique)
            if atouts and autres and not valet_connu:
                cible = True
                e["fait"] = True
                e["nb_atouts"] = len([c for c in main if c[1] == a])
                if self.option == "atout":
                    jouables = atouts
                elif self.option == "autre":
                    jouables = autres
        carte = super().jouer_carte(main, jouables, pli, contrat, joueur, regles)
        if cible:
            e["joue_atout"] = carte[1] == a
        return carte


def une_donne(numero):
    ecarts, etats = {}, {}
    for option in ("atout", "autre"):
        random.seed(numero)                 # même hasard pour les deux versions
        mains = distribuer()
        etat = {"fait": False}
        joueurs = [TesteurMC() for _ in range(4)]
        for j in joueurs:
            j.option, j.etat = option, etat
        r = jouer_donne(numero % 4, joueurs, REGLES_STANDARD, mains=mains)
        if r is None or not etat["fait"]:
            return None
        eq = r["contrat"]["joueur"] % 2
        ecarts[option] = r["scores"][eq] - r["scores"][1 - eq]
        etats[option] = etat
    return etats["atout"]["nb_atouts"], ecarts["atout"] - ecarts["autre"]


if __name__ == "__main__":
    with mp.get_context("fork").Pool(os.cpu_count()) as pool:
        cas = [c for c in pool.imap_unordered(une_donne, range(GRAINE, GRAINE + NB), chunksize=20)
               if c is not None]
    print(f"Situation rencontrée dans {len(cas)} donnes sur {NB}\n")
    groupes = defaultdict(list)
    for n_at, ecart in cas:
        groupes["Toutes situations"].append(ecart)
        groupes[f"{n_at} atout(s) en main" if n_at < 3 else "3 atouts ou plus en main"].append(ecart)
    print("Situation (Monte Carlo)        |   Cas | Atout − Autre (pts)")
    for k, liste in groupes.items():
        n, m, marge = resume(liste)
        print(f"{k:30} | {n:5} | {m:+7.1f} ± {marge:4.1f}")
