import math
import os
import random
import time
import multiprocessing as mp
from regles import REGLES_STANDARD
from moteur import distribuer
from partie import jouer_donne
from experience_coinche import SysCoinche
from montecarlo import JoueurMonteCarloContrat
from analyse_capot import JoueurAnalyseCapot

REGLES = REGLES_STANDARD
NB_CAS = 150      # nombre de donnes "capot potentiel" à analyser


class Detecteur(JoueurAnalyseCapot):
    """Repère les donnes où l'analyse se déclencherait, sans la lancer (rapide)."""
    def decision_capot(self, main, joueur, contrat, regles, total, a):
        if total >= self.declenchement:
            self.declenche = True
        return None


class Reference(JoueurMonteCarloContrat, SysCoinche):
    nom = "Référence (9 plis)"


class AnalyseGain(JoueurMonteCarloContrat, JoueurAnalyseCapot):
    nom = "Analyse (gain)"
    critere = "gain"


class AnalyseSeuil(AnalyseGain):
    nom = "Analyse (90 %)"
    critere = "seuil"


VARIANTES = [Reference, AnalyseGain, AnalyseSeuil]


def detecter(numero):
    random.seed(numero)
    mains = distribuer()
    js = [Detecteur(), SysCoinche(), Detecteur(), SysCoinche()]
    jouer_donne(numero % 4, js, REGLES, mains=mains)
    return js[0].declenche or js[2].declenche


def evaluer(numero):
    """Même donne jouée par chaque variante (équipe 0), contre les mêmes adversaires."""
    res = []
    for V in VARIANTES:
        random.seed(numero)
        mains = distribuer()
        r = jouer_donne(numero % 4, [V(), Reference(), V(), Reference()], REGLES, mains=mains)
        if r is None:
            res.append((0, False, False))
            continue
        s = r["scores"]
        capot = r["contrat"]["capot"] and r["contrat"]["joueur"] % 2 == 0
        res.append((s[0] - s[1], capot, capot and r["reussi"]))
    return res


if __name__ == "__main__":
    debut = time.time()
    ctx = mp.get_context("fork")

    # 1. Recherche rapide des donnes "capot potentiel"
    cas, examinees = [], 0
    with ctx.Pool(os.cpu_count()) as pool:
        for numero, ok in enumerate(pool.imap(detecter, range(500000), chunksize=200)):
            examinees = numero + 1
            if ok:
                cas.append(numero)
                if len(cas) >= NB_CAS:
                    break
    print(f"{len(cas)} donnes trouvées sur {examinees} "
          f"(1 toutes les {examinees // max(len(cas), 1)} donnes, {time.time() - debut:.0f} s)\n")

    # 2. Chaque donne jouée par les 3 variantes
    resultats = []
    with ctx.Pool(os.cpu_count()) as pool:
        for k, r in enumerate(pool.imap(evaluer, cas)):
            resultats.append(r)
            if (k + 1) % 25 == 0:
                print(f"  {k + 1}/{len(cas)} donnes analysées ({(time.time() - debut) / 60:.0f} min)")

    # 3. Bilan
    n = len(resultats)
    print(f"\nVariante            | Écart moyen | Capots annoncés | Réussis | Gain vs référence")
    for i, V in enumerate(VARIANTES):
        ecarts = [r[i][0] for r in resultats]
        annonces = sum(r[i][1] for r in resultats)
        reussis = sum(r[i][2] for r in resultats)
        ligne = f"{V.nom:19} | {sum(ecarts) / n:+11.1f} | {annonces:15} | {reussis:7}"
        if i > 0:
            d = [r[i][0] - r[0][0] for r in resultats]
            m = sum(d) / n
            sd = math.sqrt(sum((x - m) ** 2 for x in d) / (n - 1))
            ligne += f" | {m:+.1f} ± {1.96 * sd / math.sqrt(n):.1f}"
        print(ligne)
    print(f"\nTerminé en {(time.time() - debut) / 60:.0f} min")
