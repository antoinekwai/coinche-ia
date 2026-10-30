import os
import random
import multiprocessing as mp
from collections import defaultdict
from regles import REGLES_STANDARD
from moteur import distribuer
from partie import jouer_donne
from ia_joueur import JoueurIA

NB = 40000
GRAINE = 7000000


class Testeur(JoueurIA):
    option = "libre"     # "atout", "autre" ou "libre"
    etat = None          # informations partagées pendant la donne

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
                e["pli"] = len(self.historique) // 4 + 1
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
    random.seed(numero)
    mains = distribuer()
    ecarts, etats = {}, {}
    for option in ("atout", "autre", "libre"):
        etat = {"fait": False}
        joueurs = [Testeur() for _ in range(4)]
        for j in joueurs:
            j.option, j.etat = option, etat
        r = jouer_donne(numero % 4, joueurs, REGLES_STANDARD, mains=mains)
        if r is None or not etat["fait"]:
            return None
        eq = r["contrat"]["joueur"] % 2
        ecarts[option] = r["scores"][eq] - r["scores"][1 - eq]
        etats[option] = etat
    contrat = r["contrat"]
    infos = dict(etats["libre"])
    infos["valet_preneur"] = ("V", contrat["atout"]) in mains[contrat["joueur"]]
    return infos, ecarts["atout"] - ecarts["autre"]


def resume(diffs):
    n = len(diffs)
    m = sum(diffs) / n
    sd = (sum((x - m) ** 2 for x in diffs) / max(n - 1, 1)) ** 0.5
    return n, m, 1.96 * sd / n ** 0.5


if __name__ == "__main__":
    with mp.get_context("fork").Pool(os.cpu_count()) as pool:
        cas = [c for c in pool.imap_unordered(une_donne, range(GRAINE, GRAINE + NB), chunksize=50)
               if c is not None]
    print(f"Situation rencontrée dans {len(cas)} donnes sur {NB}\n")

    groupes = defaultdict(list)
    for infos, ecart in cas:
        n_at = infos["nb_atouts"]
        cles = ["Toutes situations",
                "Au 1er pli" if infos["pli"] == 1 else "Plus tard dans la donne",
                f"{n_at} atout(s) en main" if n_at < 3 else "3 atouts ou plus en main",
                "Valet chez le preneur" if infos["valet_preneur"] else "Valet chez un adversaire"]
        for k in cles:
            groupes[k].append((ecart, infos["joue_atout"]))

    print("Situation                      |   Cas | Atout − Autre (pts) | L'IA libre joue atout")
    for k, liste in groupes.items():
        n, m, marge = resume([e for e, _ in liste])
        part = 100 * sum(j for _, j in liste) / n
        print(f"{k:30} | {n:5} | {m:+7.1f} ± {marge:4.1f}      | {part:5.0f} %")
