import os
import random
import multiprocessing as mp
from collections import defaultdict
from regles import REGLES_STANDARD
from moteur import distribuer
from partie import jouer_donne
from ia_joueur import JoueurIA
from etude_atout import resume

NB = 200000
GRAINE = 15000000


class Testeur(JoueurIA):
    option = "libre"     # "libre", "singlette" ou "retour"
    etat = None

    def jouer_carte(self, main, jouables, pli, contrat, joueur, regles):
        a, e = contrat["atout"], self.etat
        defense = contrat["joueur"] % 2 != joueur % 2

        # 1. Le défenseur qui a la main, avec une singlette et au moins un atout
        if not e["fait"] and not pli and defense and not contrat["capot"]:
            singl = [c for c in main if c[1] != a and c[0] != "A"
                     and sum(1 for x in main if x[1] == c[1]) == 1]
            nb_atouts = sum(1 for c in main if c[1] == a)
            if singl and nb_atouts:
                e.update(fait=True, meneur=joueur, couleur=singl[0][1],
                         pli_n=len(self.historique) // 4, nb_atouts=nb_atouts)
                if self.option != "libre":
                    jouables = [singl[0]]
                carte = super().jouer_carte(main, jouables, pli, contrat, joueur, regles)
                e["joue_singlette"] = carte == singl[0]
                return carte

        # 2. Le partenaire a remporté le pli de la singlette et reprend la main
        if (e["fait"] and not e.get("vu") and not pli
                and joueur == (e["meneur"] + 2) % 4
                and len(self.historique) == 4 * (e["pli_n"] + 1)):
            e["vu"] = True
            e["partenaire_gagne"] = True
            meme = [c for c in jouables if c[1] == e["couleur"]]
            if self.option == "retour" and meme:
                jouables = meme
        return super().jouer_carte(main, jouables, pli, contrat, joueur, regles)


def une_donne(numero):
    random.seed(numero)
    mains = distribuer()
    ecarts, etats = {}, {}
    for option in ("libre", "singlette", "retour"):
        etat = {"fait": False}
        joueurs = [Testeur() for _ in range(4)]
        for j in joueurs:
            j.option, j.etat = option, etat
        r = jouer_donne(numero % 4, joueurs, REGLES_STANDARD, mains=mains)
        if r is None or not etat["fait"]:
            return None
        eq = etat["meneur"] % 2
        ecarts[option] = r["scores"][eq] - r["scores"][1 - eq]
        etats[option] = etat
    e = etats["singlette"]
    infos = {
        "atouts": "1 atout" if e["nb_atouts"] == 1 else "2 atouts ou plus",
        "moment": "1er pli" if e["pli_n"] == 0 else "plus tard",
        "partenaire": e.get("partenaire_gagne", False),
        "ia_singlette": etats["libre"]["joue_singlette"],
    }
    return infos, ecarts["singlette"] - ecarts["libre"], ecarts["retour"] - ecarts["singlette"]


if __name__ == "__main__":
    with mp.get_context("fork").Pool(os.cpu_count()) as pool:
        cas = [c for c in pool.imap_unordered(une_donne, range(GRAINE, GRAINE + NB), chunksize=200)
               if c is not None]
    part = 100 * sum(i["ia_singlette"] for i, _, _ in cas) / len(cas)
    print(f"{len(cas)} situations sur {NB} donnes (l'IA libre entame sa singlette {part:.0f} %)\n")

    groupes = defaultdict(lambda: ([], []))
    for infos, d_entame, d_retour in cas:
        for cle in ("Toutes", infos["atouts"], infos["moment"]):
            groupes[cle][0].append(d_entame)
            if infos["partenaire"]:
                groupes[cle][1].append(d_retour)

    print("Situation        | Entamer la singlette (B − A) | Retour du partenaire (C − B, s'il a pris)")
    for cle, (ent, ret) in groupes.items():
        n1, m1, e1 = resume(ent)
        n2, m2, e2 = resume(ret) if len(ret) > 1 else (0, 0, 0)
        print(f"{cle:16} | {n1:6} cas : {m1:+5.1f} ± {e1:3.1f}    | {n2:6} cas : {m2:+5.1f} ± {e2:3.1f}")
