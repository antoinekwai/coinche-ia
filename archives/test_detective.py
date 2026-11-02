"""
test_detective.py
Mesure la qualité du « détective » (generateur_contraintes.py) sans jouer de benchmark.
UTILISATION : python3 test_detective.py
"""
import random
import time
from regles import REGLES_STANDARD
from moteur import distribuer, cartes_jouables, gagnant_pli, COULEURS, RANGS
from partie import phase_annonces
from ia_joueur import JoueurIA
from generateur_contraintes import imaginer_donnes_contraintes
from detective_v2 import imaginer_filtre, coherente, STATS


NB_DONNES = 1000        # donnes réelles testées
NB_IMAGINEES = 50      # donnes imaginées à chaque interrogation
MOMENTS = [0, 2, 4]    # nombre de plis déjà joués quand on interroge le détective
PREMIERE_GRAINE = 2_000_000


def donne_coherente_avec_le_jeu(imag, mains_reelles, historique, atout, regles):
    """True si la donne imaginée respecte les tailles de main ET toutes les règles
    sur les cartes déjà jouées (fournir, couper, monter, sous-couper)."""
    for p in range(4):
        if len(imag[p]) != len(mains_reelles[p]):
            return False
    mains = [list(m) for m in imag]
    for j, c in historique:
        mains[j].append(c)
    for debut in range(0, len(historique), 4):
        pli = []
        for j, c in historique[debut:debut + 4]:
            if c not in cartes_jouables(mains[j], pli, atout, j, regles):
                return False
            mains[j].remove(c)
            pli.append((j, c))
    return True


def tirage_naif(main_joueur, joueur, historique):
    """Référence : cartes inconnues distribuées au hasard, sans aucune déduction."""
    vues = set(main_joueur) | {c for _, c in historique}
    inconnues = [(r, c) for c in COULEURS for r in RANGS if (r, c) not in vues]
    random.shuffle(inconnues)
    mains = [None] * 4
    mains[joueur] = list(main_joueur)
    cur = 0
    for k in (1, 2, 3):
        p = (joueur + k) % 4
        n = 8 - sum(1 for j, _ in historique if j == p)
        mains[p] = inconnues[cur:cur + n]
        cur += n
    return mains


def hasard_filtre(m, j, h, e, a, r):
    """Hasard pur, mais on jette les donnes impossibles."""
    imag = None
    for _ in range(200):
        imag = tirage_naif(m, j, h)
        if coherente(imag, h, a, r):
            return imag
    return imag


GENERATEURS = {
    "Hasard pur":      lambda m, j, h, e, a, r: tirage_naif(m, j, h),
    "Hasard filtré":   hasard_filtre,
    "Détective SANS":  lambda m, j, h, e, a, r: imaginer_donnes_contraintes(m, j, h, [], a, r),
    "Détective AVEC":  lambda m, j, h, e, a, r: imaginer_donnes_contraintes(m, j, h, e, a, r),
    "AVEC + filtre":   lambda m, j, h, e, a, r: imaginer_filtre(m, j, h, e, a, r),
}



def interroger(stats, moment, mains, j, historique, encheres, atout, regles):
    jouees = {c for _, c in historique}
    cartes_cles = [c for c in [("V", atout), ("9", atout)] if c not in mains[j] and c not in jouees]
    for nom, gen in GENERATEURS.items():
        s = stats[(nom, moment)]
        for _ in range(NB_IMAGINEES):
            imag = gen(mains[j], j, historique, encheres, atout, regles)
            s["total"] += 1
            if not donne_coherente_avec_le_jeu(imag, mains, historique, atout, regles):
                s["impossibles"] += 1
            for k in (1, 2, 3):
                p = (j + k) % 4
                vraie = set(mains[p])
                s["bonnes"] += sum(1 for c in imag[p] if c in vraie)
                s["cartes"] += len(mains[p])
            for c in cartes_cles:
                proprio = next(p for p in range(4) if c in mains[p])
                s["cles_total"] += 1
                if c in imag[proprio]:
                    s["cles_bonnes"] += 1


def tester_une_donne(graine, stats, regles):
    random.seed(graine)
    mains = distribuer()
    donneur = graine % 4
    joueurs = [JoueurIA() for _ in range(4)]
    contrat = phase_annonces(mains, donneur, joueurs, regles, afficher=False)
    if contrat is None:
        return False
    encheres = list(joueurs[(donneur + 1) % 4].encheres)
    atout = contrat["atout"]

    ia = JoueurIA()
    mains = [list(m) for m in mains]
    historique = []
    premier = (donneur + 1) % 4
    for num_pli in range(8):
        if num_pli in MOMENTS:
            interroger(stats, num_pli, mains, premier, historique, encheres, atout, regles)
        pli = []
        for i in range(4):
            j = (premier + i) % 4
            jouables = cartes_jouables(mains[j], pli, atout, j, regles)
            ia.historique = list(historique)
            ia.encheres = list(encheres)
            c = ia.jouer_carte(mains[j], jouables, pli, contrat, j, regles)
            mains[j].remove(c)
            pli.append((j, c))
            historique.append((j, c))
        premier = gagnant_pli(pli, atout)[0]
    return True

if __name__ == "__main__":
    regles = REGLES_STANDARD
    stats = {(nom, m): {"total": 0, "impossibles": 0, "bonnes": 0, "cartes": 0,
                        "cles_total": 0, "cles_bonnes": 0}
             for nom in GENERATEURS for m in MOMENTS}
    debut = time.time()
    faites, erreurs, graine = 0, 0, PREMIERE_GRAINE
    while faites < NB_DONNES:
        try:
            if tester_une_donne(graine, stats, regles):
                faites += 1
                if faites % 20 == 0:
                    print(f"  {faites}/{NB_DONNES} donnes ({(time.time() - debut) / 60:.1f} min)", flush=True)
        except Exception as e:
            erreurs += 1
            print(f"  ⚠️ Erreur graine {graine} : {e!r}", flush=True)
            if erreurs >= 10:
                print("⛔ Trop d'erreurs, arrêt. Envoie-moi le message ci-dessus.")
                break
        graine += 1

    print()
    print("=" * 74)
    print(f"QUALITÉ DES DÉTECTIVES  ({faites} donnes, {NB_IMAGINEES} donnes imaginées par question)")
    print("=" * 74)
    for m in MOMENTS:
        print(f"\n--- Après {m} pli(s) joué(s) ---")
        print(f"{'Générateur':<16} | {'% impossibles':>13} | {'% bien placées':>14} | {'% V/9 bien placés':>17}")
        print("-" * 70)
        for nom in GENERATEURS:
            s = stats[(nom, m)]
            imp = 100 * s["impossibles"] / max(1, s["total"])
            bp = 100 * s["bonnes"] / max(1, s["cartes"])
            cl = 100 * s["cles_bonnes"] / max(1, s["cles_total"])
            print(f"{nom:<16} | {imp:12.1f}% | {bp:13.1f}% | {cl:16.1f}%")

    print("\nCOMMENT LIRE :")
    print(" - % impossibles : donnes imaginées qui contredisent une carte déjà jouée (0 = parfait).")
    print(" - % bien placées : cartes attribuées à leur vrai propriétaire (plus c'est haut, mieux c'est).")
    print(" - % V/9 bien placés : idem pour le Valet et le 9 d'atout, les cartes clés.")
    print(" - Après 0 pli, rien n'a été joué : « impossibles » vaut forcément 0.")
    print(f"Filtre du détective : {STATS['echecs']} échecs sur {STATS['appels']} appels")

    print(f"\nTerminé en {(time.time() - debut) / 60:.1f} minutes.")
