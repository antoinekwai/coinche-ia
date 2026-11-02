import os
import random
import multiprocessing as mp
from collections import defaultdict
from regles import REGLES_STANDARD
from moteur import distribuer, COULEURS
from partie import jouer_donne
from ia_joueur import JoueurIA
from etude_atout import resume

NB = 500000
GRAINE = 8000000


class Testeur(JoueurIA):
    option = "atout"
    etat = None
    mains_init = None

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
                e["main"] = list(main)
                e["pli"] = len(self.historique) // 4 + 1
                jouees = {c for _, c in self.historique}
                adv = [(joueur + 1) % 4, (joueur + 3) % 4]
                e["atouts_adv"] = sum(1 for p in adv for c in self.mains_init[p]
                                      if c[1] == a and c not in jouees)
                jouables = atouts if self.option == "atout" else autres
        carte = super().jouer_carte(main, jouables, pli, contrat, joueur, regles)
        if cible:
            e["carte"] = carte
        return carte


def une_donne(numero):
    random.seed(numero)
    mains = distribuer()
    res = {}
    for option in ("atout", "autre"):
        etat = {"fait": False}
        joueurs = [Testeur() for _ in range(4)]
        for j in joueurs:
            j.option, j.etat, j.mains_init = option, etat, mains
        r = jouer_donne(numero % 4, joueurs, REGLES_STANDARD, mains=mains)
        if r is None or not etat["fait"]:
            return None
        a = r["contrat"]["atout"]
        if option == "atout" and len([c for c in etat["main"] if c[1] == a]) != 1:
            return None                       # on ne garde que les cas à un seul atout
        eq = r["contrat"]["joueur"] % 2
        res[option] = (r["scores"][eq] - r["scores"][1 - eq], etat)

    a, valeur = r["contrat"]["atout"], r["contrat"]["valeur"]
    e = res["atout"][1]
    main = e["main"]
    rang = [c for c in main if c[1] == a][0][0]
    alt = res["autre"][1]["carte"][0]
    nb_as = sum(1 for c in main if c[0] == "A" and c[1] != a)
    coupe = any(not any(c[1] == x for c in main) for x in COULEURS if x != a)

    infos = {
        "1. Valeur de mon atout": {"9": "9", "A": "As", "10": "10", "R": "Roi ou Dame",
                                   "D": "Roi ou Dame"}.get(rang, "7 ou 8"),
        "2. Coupe franche": "oui" if coupe else "non",
        "3. As à côté": "0" if nb_as == 0 else ("1" if nb_as == 1 else "2 ou plus"),
        "4. Contrat": "80-90" if valeur <= 90 else ("100-110" if valeur <= 110 else "120 et plus"),
        "5. Moment": "1er pli" if e["pli"] == 1 else "plus tard",
        "6. Carte jouée à la place": {"A": "un as", "10": "un 10"}.get(alt, "une autre carte"),
        "7. Atouts adverses (caché)": "0-1" if e["atouts_adv"] <= 1 else
                                      ("2" if e["atouts_adv"] == 2 else "3 ou plus"),
    }
    moment = infos["5. Moment"]
    gros = "9 ou As" if rang in ("9", "A") else ("10" if rang == "10" else "petit (7, 8, R, D)")
    infos["8. Moment × atout"] = f"{moment} / {gros}"
    infos["9. Moment × coupe franche"] = f"{moment} / coupe {infos['2. Coupe franche']}"
    infos["10. Moment × atouts adverses"] = f"{moment} / {infos['7. Atouts adverses (caché)']} adv."

    return infos, res["atout"][0] - res["autre"][0]


if __name__ == "__main__":
    with mp.get_context("fork").Pool(os.cpu_count()) as pool:
        cas = [c for c in pool.imap_unordered(une_donne, range(GRAINE, GRAINE + NB), chunksize=200)
               if c is not None]
    n, m, marge = resume([d for _, d in cas])
    print(f"{n} situations à un seul atout sur {NB} donnes : atout − autre = {m:+.1f} ± {marge:.1f}\n")

    groupes = defaultdict(list)
    for infos, d in cas:
        for facteur, valeur in infos.items():
            groupes[(facteur, valeur)].append(d)

    courant = None
    for (facteur, valeur) in sorted(groupes):
        if facteur != courant:
            print(f"\n{facteur}")
            courant = facteur
        n, m, marge = resume(groupes[(facteur, valeur)])
        print(f"   {valeur:30} | {n:6} cas | atout − autre : {m:+6.1f} ± {marge:4.1f}")
