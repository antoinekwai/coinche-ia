import os
import random
import multiprocessing as mp
from collections import defaultdict
from regles import REGLES_STANDARD
from moteur import distribuer
from partie import jouer_donne
from ia_joueur import JoueurIA
from experience_coinche import force_coinche

NB = 300000
GRAINE = 17000000
NIVEAUX = ["80-90", "100-110", "120-130", "140+"]
TYPES = ["ouverture seule", "ouverture + réponse", "disputées"]


class SansCoinche(JoueurIA):
    nom = "IA-sans-coinche"
    seuil = 99                     # ne coinche jamais


def niveau(v):
    return "80-90" if v <= 90 else "100-110" if v <= 110 else "120-130" if v <= 130 else "140+"


def une_donne(numero):
    random.seed(numero)
    mains = distribuer()
    joueurs = [SansCoinche() for _ in range(4)]
    r = jouer_donne(numero % 4, joueurs, REGLES_STANDARD, mains=mains)
    if r is None or r["contrat"]["capot"]:
        return []
    c = r["contrat"]
    att = c["joueur"] % 2
    annonces = [(j, d) for j, d in joueurs[0].encheres if isinstance(d, tuple)]
    adv = any(j % 2 != att for j, _ in annonces)
    nb_att = sum(1 for j, _ in annonces if j % 2 == att)
    type_e = "disputées" if adv else ("ouverture + réponse" if nb_att >= 2 else "ouverture seule")
    res = []
    for p in range(4):
        if p % 2 == att:
            continue
        f = min(force_coinche(mains[p], c), 6)
        nas = sum(1 for x in mains[p] if x[0] == "A" and x[1] != c["atout"])
        part_parle = any(j == (p + 2) % 4 for j, _ in annonces)
        res.append((f, min(nas, 2), niveau(c["valeur"]), type_e, part_parle, not r["reussi"]))
    return res


def grille(titre, cas, cle_col, colonnes, filtre=lambda x: True):
    t = defaultdict(list)
    for x in cas:
        if filtre(x):
            t[(x[0], cle_col(x))].append(x[5])
    print(f"\n{titre}")
    print("Force  | " + " | ".join(f"{c:>19}" for c in colonnes))
    for f in range(7):
        cellules = []
        for col in colonnes:
            l = t[(f, col)]
            cellules.append(f"{100 * sum(l) / len(l):5.0f} % ({len(l):6})" if len(l) >= 200 else f"{'—':>19}")
        print(f"{f if f < 6 else '6+':>6} | " + " | ".join(cellules))


if __name__ == "__main__":
    with mp.get_context("fork").Pool(os.cpu_count()) as pool:
        cas = [x for lot in pool.imap_unordered(une_donne, range(GRAINE, GRAINE + NB), chunksize=200)
               for x in lot]
    print(f"{len(cas)} situations de défense. Cases : probabilité de chute (nombre de cas).")
    print("Règle actuelle : coincher si force >= 4 (80-90), 3 (100-110), 2 (120-130), 1 (140+)")

    grille("1. Selon le niveau du contrat", cas, lambda x: x[2], NIVEAUX)
    grille("2. Selon les enchères (contrats 80 à 110)", cas, lambda x: x[3], TYPES,
           lambda x: x[2] in ("80-90", "100-110"))
    grille("3. Enchères disputées : mon partenaire a-t-il annoncé ? (80 à 130)", cas,
           lambda x: "partenaire a parlé" if x[4] else "partenaire muet",
           ["partenaire a parlé", "partenaire muet"],
           lambda x: x[3] == "disputées" and x[2] != "140+")
    grille("4. As à côté (contrats 80 à 110)", cas,
           lambda x: ["0 as", "1 as", "2 as ou plus"][x[1]], ["0 as", "1 as", "2 as ou plus"],
           lambda x: x[2] in ("80-90", "100-110"))
