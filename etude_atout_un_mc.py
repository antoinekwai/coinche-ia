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

NB = 150000
GRAINE = 9000000


class Abandon(Exception):
    pass


class TesteurMC(JoueurMonteCarloContrat, SysCorrige):
    option = "atout"
    etat = None

    def jouer_carte(self, main, jouables, pli, contrat, joueur, regles):
        a, e = contrat["atout"], self.etat
        if (not e["fait"] and not pli and not contrat["capot"]
                and joueur == (contrat["joueur"] + 2) % 4):
            atouts = [c for c in jouables if c[1] == a]
            autres = [c for c in jouables if c[1] != a]
            valet_connu = ("V", a) in main or any(c == ("V", a) for _, c in self.historique)
            if atouts and autres and not valet_connu:
                e["fait"] = True
                mes_atouts = [c for c in main if c[1] == a]
                if len(mes_atouts) != 1:
                    raise Abandon                    # on ne garde que les cas à un seul atout
                rang = mes_atouts[0][0]
                moment = "1er pli" if not self.historique else "plus tard"
                gros = "9 ou As" if rang in ("9", "A") else ("10" if rang == "10" else "petit (7, 8, R, D)")
                e["groupe"] = f"{moment} / {gros}"
                jouables = atouts if self.option == "atout" else autres
        return super().jouer_carte(main, jouables, pli, contrat, joueur, regles)


def une_donne(numero):
    ecarts = {}
    for option in ("atout", "autre"):
        random.seed(numero)                          # même hasard pour les deux versions
        mains = distribuer()
        etat = {"fait": False}
        joueurs = [TesteurMC() for _ in range(4)]
        for j in joueurs:
            j.option, j.etat = option, etat
        try:
            r = jouer_donne(numero % 4, joueurs, REGLES_STANDARD, mains=mains)
        except Abandon:
            return None
        if r is None or not etat["fait"]:
            return None
        eq = r["contrat"]["joueur"] % 2
        ecarts[option] = r["scores"][eq] - r["scores"][1 - eq]
    return etat["groupe"], ecarts["atout"] - ecarts["autre"]


if __name__ == "__main__":
    cas = []
    with mp.get_context("fork").Pool(os.cpu_count()) as pool:
        for k, c in enumerate(pool.imap_unordered(une_donne, range(GRAINE, GRAINE + NB), chunksize=20)):
            if c is not None:
                cas.append(c)
            if (k + 1) % 25000 == 0:
                print(f"  {k + 1}/{NB} donnes, {len(cas)} situations", flush=True)

    groupes = defaultdict(list)
    for g, d in cas:
        groupes["Toutes (un seul atout)"].append(d)
        groupes[g].append(d)
    print("\nSituation (Monte Carlo)          |   Cas | Atout − Autre (pts)")
    for k in sorted(groupes):
        n, m, marge = resume(groupes[k])
        print(f"{k:32} | {n:5} | {m:+7.1f} ± {marge:4.1f}")
