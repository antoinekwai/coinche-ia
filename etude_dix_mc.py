import os
import random
import multiprocessing as mp
from collections import defaultdict
from regles import REGLES_STANDARD
from moteur import distribuer, gagnant_pli
from partie import jouer_donne
from montecarlo import JoueurMonteCarloContrat
from systeme_corrige import SysCorrige
from etude_atout import resume

NB = 8000
GRAINE = 11000000


class TesteurMC(JoueurMonteCarloContrat, SysCorrige):
    option = "dix"
    etat = None

    def jouer_carte(self, main, jouables, pli, contrat, joueur, regles):
        a, e = contrat["atout"], self.etat
        if not e["fait"] and pli and gagnant_pli(pli, a)[0] == (joueur + 2) % 4:
            dix = [c for c in jouables if c[0] == "10" and c[1] != a]
            autres = [c for c in jouables if c not in dix]
            if len(dix) == 1 and autres:
                e["fait"] = True
                x = dix[0][1]
                vues = {c for _, c in self.historique}
                if ("A", x) in main:
                    statut = "j'ai l'As"
                elif ("A", x) in vues:
                    statut = "10 maître"
                else:
                    statut = "As dehors"
                camp = "attaque" if contrat["joueur"] % 2 == joueur % 2 else "défense"
                pos = "4e" if len(pli) == 3 else "3e"
                e["equipe"] = joueur % 2
                e["groupes"] = [camp, f"{camp} / {pos}", f"{camp} / {statut}"]
                jouables = dix if self.option == "dix" else autres
        return super().jouer_carte(main, jouables, pli, contrat, joueur, regles)


def une_donne(numero):
    ecarts = {}
    for option in ("dix", "autre"):
        random.seed(numero)                  # même hasard pour les deux versions
        mains = distribuer()
        etat = {"fait": False}
        joueurs = [TesteurMC() for _ in range(4)]
        for j in joueurs:
            j.option, j.etat = option, etat
        r = jouer_donne(numero % 4, joueurs, REGLES_STANDARD, mains=mains)
        if r is None or not etat["fait"]:
            return None
        eq = etat["equipe"]
        ecarts[option] = r["scores"][eq] - r["scores"][1 - eq]
    return etat["groupes"], ecarts["dix"] - ecarts["autre"]


if __name__ == "__main__":
    with mp.get_context("fork").Pool(os.cpu_count()) as pool:
        cas = [c for c in pool.imap_unordered(une_donne, range(GRAINE, GRAINE + NB), chunksize=20)
               if c is not None]
    groupes = defaultdict(list)
    for gs, d in cas:
        for g in gs:
            groupes[g].append(d)
    print(f"{len(cas)} situations sur {NB} donnes\n")
    print("Situation (Monte Carlo)   |   Cas | 10 − autre (pts)")
    for k in sorted(groupes):
        n, m, marge = resume(groupes[k])
        print(f"{k:25} | {n:5} | {m:+6.1f} ± {marge:4.1f}")
