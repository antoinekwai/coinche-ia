"""
test_detective2.py
Mesure des détectives par CRITÈRES (atouts, longueurs, As, honneurs) et calibration.
UTILISATION : python3 test_detective2.py
"""
import random
import time
import os
import multiprocessing as mp
import numpy as np
import torch
from regles import REGLES_STANDARD
from moteur import distribuer, cartes_jouables, gagnant_pli, COULEURS
from partie import phase_annonces
from ia_joueur import JoueurIA
from generateur_contraintes import imaginer_donnes_contraintes
from detective_v2 import coherente, imaginer_filtre
from detective_v3 import tirage_naif, imaginer_v3

NB_DONNES = 100        # donnes réelles testées
NB_IMAGINEES = 20      # donnes imaginées par question
MOMENTS = [0, 2, 4]    # nombre de plis joués quand on interroge
PREMIERE_GRAINE = 2_000_000


def hasard_filtre(m, j, h, e, a, r):
    imag = None
    for _ in range(200):
        imag = tirage_naif(m, j, h)
        if coherente(imag, h, a, r):
            return imag
    return imag


GENERATEURS = {
    "Hasard filtré":  hasard_filtre,
    "Détective AVEC": lambda m, j, h, e, a, r: imaginer_donnes_contraintes(m, j, h, e, a, r),
    "AVEC + filtre":  lambda m, j, h, e, a, r: imaginer_filtre(m, j, h, e, a, r),
    "Système v2":     lambda m, j, h, e, a, r: imaginer_v3(m, j, h, e, a, r),
}
CLES = ["n", "imp", "at", "lon", "as", "cles", "proba", "brier"]


def profil(main, atout):
    """Les critères qui comptent : longueur de chaque couleur et nombre d'As hors atout."""
    lon = {c: sum(1 for x in main if x[1] == c) for c in COULEURS}
    nas = sum(1 for r, c in main if r == "A" and c != atout)
    return lon, nas


def mesurer(gen, mains, j, hist, encheres, atout, regles):
    autres = [(j + k) % 4 for k in (1, 2, 3)]
    jouees = {c for _, c in hist}
    cartes_cles = [(r, atout) for r in ("V", "9", "A")
                   if (r, atout) not in mains[j] and (r, atout) not in jouees]
    vrais = {p: profil(mains[p], atout) for p in autres}
    s = dict.fromkeys(CLES, 0.0)
    compte = {(c, p): 0 for c in cartes_cles for p in autres}

    for _ in range(NB_IMAGINEES):
        imag = gen(mains[j], j, hist, encheres, atout, regles)
        s["n"] += 1
        s["imp"] += 0 if coherente(imag, hist, atout, regles) else 1
        for p in autres:
            lon, nas = profil(imag[p], atout)
            vlon, vnas = vrais[p]
            s["at"] += abs(lon[atout] - vlon[atout]) / 3
            s["lon"] += np.mean([abs(lon[c] - vlon[c]) for c in COULEURS if c != atout]) / 3
            s["as"] += abs(nas - vnas) / 3
            for c in cartes_cles:
                if c in imag[p]:
                    compte[(c, p)] += 1

    for c in cartes_cles:
        s["cles"] += 1
        for p in autres:
            f = compte[(c, p)] / NB_IMAGINEES      # proba donnée par le détective
            y = 1.0 if c in mains[p] else 0.0      # réalité
            s["brier"] += (f - y) ** 2 / 3
            if y:
                s["proba"] += f
    return s


def tester_une_donne(graine):
    try:
        regles = REGLES_STANDARD
        random.seed(graine)
        mains = distribuer()
        donneur = graine % 4
        joueurs = [JoueurIA() for _ in range(4)]
        contrat = phase_annonces(mains, donneur, joueurs, regles, afficher=False)
        if contrat is None:
            return None
        encheres = list(joueurs[(donneur + 1) % 4].encheres)
        atout = contrat["atout"]

        ia = JoueurIA()
        mains = [list(m) for m in mains]
        hist, premier, res = [], (donneur + 1) % 4, {}
        for num_pli in range(8):
            if num_pli in MOMENTS:
                for nom, gen in GENERATEURS.items():
                    res[(nom, num_pli)] = mesurer(gen, mains, premier, hist, encheres, atout, regles)
            pli = []
            for i in range(4):
                j = (premier + i) % 4
                jouables = cartes_jouables(mains[j], pli, atout, j, regles)
                ia.historique, ia.encheres = list(hist), list(encheres)
                c = ia.jouer_carte(mains[j], jouables, pli, contrat, j, regles)
                mains[j].remove(c)
                pli.append((j, c))
                hist.append((j, c))
            premier = gagnant_pli(pli, atout)[0]
        return res
    except Exception as e:
        return {"erreur": f"graine {graine} : {e!r}"}


def init_worker():
    torch.set_num_threads(1)


if __name__ == "__main__":
    total = {(nom, m): dict.fromkeys(CLES, 0.0) for nom in GENERATEURS for m in MOMENTS}
    debut, faites, erreurs = time.time(), 0, 0
    graines = range(PREMIERE_GRAINE, PREMIERE_GRAINE + NB_DONNES * 3)
    with mp.get_context("fork").Pool(os.cpu_count(), initializer=init_worker) as pool:
        for res in pool.imap_unordered(tester_une_donne, graines):
            if res is None:
                continue
            if "erreur" in res:
                erreurs += 1
                print("  ⚠️", res["erreur"], flush=True)
                if erreurs >= 10:
                    print("⛔ Trop d'erreurs, arrêt.")
                    break
                continue
            for k, s in res.items():
                for c in CLES:
                    total[k][c] += s[c]
            faites += 1
            if faites % 10 == 0:
                print(f"  {faites}/{NB_DONNES} donnes ({(time.time() - debut) / 60:.1f} min)", flush=True)
            if faites >= NB_DONNES:
                break

    print("\n" + "=" * 92)
    print(f"DÉTECTIVES MESURÉS PAR CRITÈRES  ({faites} donnes, {NB_IMAGINEES} imaginées par question)")
    print("=" * 92)
    for m in MOMENTS:
        print(f"\n--- Après {m} pli(s) joué(s) ---")
        print(f"{'Générateur':<15} | {'% impos.':>8} | {'Écart atouts':>12} | {'Écart longueurs':>15} | "
              f"{'Écart As':>8} | {'Proba vraie':>11} | {'Brier':>6}")
        print("-" * 92)
        for nom in GENERATEURS:
            s = total[(nom, m)]
            n, k = max(1, s["n"]), max(1, s["cles"])
            print(f"{nom:<15} | {100 * s['imp'] / n:7.1f}% | {s['at'] / n:12.2f} | {s['lon'] / n:15.2f} | "
                  f"{s['as'] / n:8.2f} | {100 * s['proba'] / k:10.1f}% | {s['brier'] / k:6.3f}")
    print("\nCOMMENT LIRE :")
    print(" - Écarts : erreur moyenne par joueur (0 = parfait). Le 7 et le 8 sont équivalents.")
    print(" - Proba vraie : chance moyenne donnée au BON joueur pour V, 9, As d'atout (hasard = 33 %).")
    print(" - Brier : honnêteté du détective (plus bas = mieux ; hasard = 0,222).")
    print(f"\nTerminé en {(time.time() - debut) / 60:.1f} minutes.")
