import os
import random
import multiprocessing as mp
from collections import defaultdict
from regles import REGLES_STANDARD
from moteur import distribuer, gagnant_pli
from partie import jouer_donne
from ia_joueur import JoueurIA
from etude_atout import resume

NB = 200000
GRAINE = 10000000


class Testeur(JoueurIA):
    option = "libre"     # "dix", "autre" ou "libre"
    etat = None

    def jouer_carte(self, main, jouables, pli, contrat, joueur, regles):
        a, e = contrat["atout"], self.etat
        cible = False
        if not e["fait"] and pli and gagnant_pli(pli, a)[0] == (joueur + 2) % 4:
            dix = [c for c in jouables if c[0] == "10" and c[1] != a]
            autres = [c for c in jouables if c not in dix]
            if len(dix) == 1 and autres:
                cible = True
                e["fait"] = True
                x = dix[0][1]
                vues = {c for _, c in self.historique}
                if ("A", x) in main:
                    statut = "j'ai l'As"
                elif ("A", x) in vues:
                    statut = "As tombé (10 maître)"
                else:
                    statut = "As dehors"
                plis_faits = (len(self.historique) - len(pli)) // 4
                v = contrat["valeur"]
                e["equipe"] = joueur % 2
                e["dix"] = dix[0]
                e["infos"] = {
                    "1. Camp": "attaque" if contrat["joueur"] % 2 == joueur % 2 else "défense",
                    "2. Contrat": "80-90" if v <= 90 else ("100-110" if v <= 110 else "120 et plus"),
                    "3. Position": "4e (dernier)" if len(pli) == 3 else "3e (un adversaire après)",
                    "4. Type": "je fournis" if x == pli[0][1][1] else "je défausse",
                    "5. As de la couleur": statut,
                    "6. Moment": "plis 1-3" if plis_faits < 3 else ("plis 4-6" if plis_faits < 6 else "plis 7-8"),
                }
                if self.option == "dix":
                    jouables = dix
                elif self.option == "autre":
                    jouables = autres
        carte = super().jouer_carte(main, jouables, pli, contrat, joueur, regles)
        if cible:
            e["charge"] = carte == e["dix"]
        return carte


def une_donne(numero):
    random.seed(numero)
    mains = distribuer()
    res = {}
    for option in ("dix", "autre", "libre"):
        etat = {"fait": False}
        joueurs = [Testeur() for _ in range(4)]
        for j in joueurs:
            j.option, j.etat = option, etat
        r = jouer_donne(numero % 4, joueurs, REGLES_STANDARD, mains=mains)
        if r is None or not etat["fait"]:
            return None
        eq = etat["equipe"]
        res[option] = (r["scores"][eq] - r["scores"][1 - eq], etat)

    infos = dict(res["libre"][1]["infos"])
    camp = infos["1. Camp"]
    infos["7. Camp × position"] = f"{camp} / {infos['3. Position']}"
    infos["8. Camp × As"] = f"{camp} / {infos['5. As de la couleur']}"
    return infos, res["dix"][0] - res["autre"][0], res["libre"][1]["charge"]


if __name__ == "__main__":
    with mp.get_context("fork").Pool(os.cpu_count()) as pool:
        cas = [c for c in pool.imap_unordered(une_donne, range(GRAINE, GRAINE + NB), chunksize=200)
               if c is not None]
    n, m, marge = resume([d for _, d, _ in cas])
    part = 100 * sum(ch for _, _, ch in cas) / n
    print(f"{n} situations sur {NB} donnes : 10 − autre = {m:+.1f} ± {marge:.1f} "
          f"(l'IA libre charge {part:.0f} %)")

    groupes = defaultdict(list)
    for infos, d, ch in cas:
        for facteur, valeur in infos.items():
            groupes[(facteur, valeur)].append((d, ch))

    courant = None
    for (facteur, valeur) in sorted(groupes):
        if facteur != courant:
            print(f"\n{facteur}")
            courant = facteur
        liste = groupes[(facteur, valeur)]
        n, m, marge = resume([d for d, _ in liste])
        part = 100 * sum(ch for _, ch in liste) / n
        print(f"   {valeur:36} | {n:6} cas | 10 − autre : {m:+6.1f} ± {marge:4.1f} | IA charge {part:3.0f} %")
