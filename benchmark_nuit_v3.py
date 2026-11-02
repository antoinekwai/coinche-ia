"""
benchmark_nuit_v2.py
Grand benchmark : toutes les IA comparées à l'Oracle, sur les mêmes donnes.

UTILISATION (dans le Terminal) :
    python benchmark_nuit_v2.py            -> lance (ou reprend) le calcul
    python benchmark_nuit_v2.py --analyse  -> affiche seulement les résultats

Les résultats sont écrits donne par donne dans FICHIER_RESULTATS.
Si le programme s'arrête, on le relance : il reprend là où il en était.
"""
import time
import random
import os
import sys
import json
import multiprocessing as mp
import numpy as np
import torch
from regles import REGLES_STANDARD
from moteur import distribuer, cartes_jouables, gagnant_pli, points, equipe_belote, decompte
from partie import phase_annonces
from test_mc_encheres import MCEncheres
from ia_joueur import JoueurIA, charger, FICHIER
from ia_encodage import encoder_situation, encoder_carte
from joueurs import JoueurRegles
from solveur_exact import SolveurExact
from bot_mc_ia import BotMCIA
from bot_coop import BotCoop

# ======================================================================
# RÉGLAGES (les seules lignes que tu as besoin de modifier)
# ======================================================================
NB_DONNES = 1000                 # Nombre de donnes VALIDES voulues (40 = test rapide)
PLIS_RESEAU_ORACLE = 1         # Nb de plis où l'Oracle utilise le réseau au lieu du calcul exact
                               #   2 = comme l'ancien script ; 1 = plus honnête ; 0 = Oracle pur (lent)
FICHIER_RESULTATS = "resultats_benchmark_encheres.jsonl"

PREMIERE_GRAINE = 1_000_000    # Même départ que l'ancien script -> mêmes donnes
MAX_ERREURS = 20               # Le calcul s'arrête si trop de donnes plantent

MOTEURS = ["oracle", "mcia", "mc_encheres", "coop", "ia", "regles"]
NOMS = {
    "oracle": "Oracle (plafond)",
    "mcia": "Bot-MC-IA",
    "mc_encheres": "MC-Enchères",
    "coop": "Bot-Coop",
    "ia": "IA pure (11 ms)",
    "regles": "Joueur à Règles",
}

# ======================================================================
# OUTILS
# ======================================================================
_RESEAU = None

def reseau():
    """Charge le réseau UNE SEULE FOIS (avant : à chaque carte, très lent)."""
    global _RESEAU
    if _RESEAU is None:
        _RESEAU = charger(FICHIER)
        if hasattr(_RESEAU, "eval"):
            _RESEAU.eval()
    return _RESEAU


def fixer_hasard(graine):
    """Fixe tous les générateurs de hasard (Python, numpy, torch)."""
    random.seed(graine)
    np.random.seed(graine % (2**32))
    torch.manual_seed(graine)


def init_worker():
    """Exécuté une fois au démarrage de chaque processus de calcul.
    Empêche les processus de se disputer les cœurs du processeur."""
    torch.set_num_threads(1)


# ======================================================================
# L'ORACLE (voit toutes les cartes)
# ======================================================================
class OracleJoueur:
    def jouer_carte(self, mains_reelles, jouables, pli, contrat, joueur, historique, regles):
        if len(jouables) == 1:
            return jouables[0]

        atout = contrat["atout"]
        equipe = joueur % 2

        # Début de donne : réseau (le calcul exact serait trop long)
        if len(historique) < 4 * PLIS_RESEAU_ORACLE and len(jouables) > 3:
            s = encoder_situation(mains_reelles[joueur], pli, historique, contrat, joueur, regles, [])
            vec_c = np.stack([encoder_carte(c, atout) for c in jouables])
            x_in = np.concatenate([np.repeat(s[None, :], len(jouables), axis=0), vec_c], axis=1)
            with torch.no_grad():
                notes = reseau()(torch.from_numpy(x_in)).squeeze(1).numpy()
            return jouables[int(notes.argmax())]

        # Sinon : calcul exact cartes ouvertes
        premier_du_pli = (joueur - len(pli)) % 4
        solveur = SolveurExact(atout, regles)
        meilleure_carte, meilleur_score = jouables[0], -9999
        for c in jouables:
            m_copie = [list(m) for m in mains_reelles]
            m_copie[joueur].remove(c)
            pli_v = list(pli) + [(joueur, c)]
            score_net_02 = solveur.minimax(m_copie, pli_v, premier_du_pli, -999, 999)
            score_mon_camp = score_net_02 if equipe == 0 else -score_net_02
            if score_mon_camp > meilleur_score:
                meilleur_score, meilleure_carte = score_mon_camp, c
        return meilleure_carte


# ======================================================================
# UNE PARTIE = une donne jouée par un moteur contre MC-Enchères
# ======================================================================
def simuler_une_table(graine, mains_depart, contrat, donneur, regles, type_moteur, camp_teste, encheres):
    # Même hasard de départ pour toutes les parties de cette donne
    fixer_hasard(graine * 10 + 7)

    atout = contrat["atout"]
    premier = (donneur + 1) % 4
    mains = [list(m) for m in mains_depart]

    adversaire = MCEncheres()
    oracle = OracleJoueur()
    bots = {"mcia": BotMCIA, "mc_encheres": MCEncheres, "coop": BotCoop,
            "ia": JoueurIA, "regles": JoueurRegles}
    bot_teste = bots[type_moteur]() if type_moteur != "oracle" else None

    historique, pts_eq, plis_eq = [], [0, 0], [0, 0]

    for num in range(1, 9):
        pli = []
        for i in range(4):
            j = (premier + i) % 4
            jouables = cartes_jouables(mains[j], pli, atout, j, regles)

            if j % 2 == camp_teste and type_moteur == "oracle":
                c = oracle.jouer_carte(mains, jouables, pli, contrat, j, historique, regles)
            else:
                b = bot_teste if j % 2 == camp_teste else adversaire
                b.historique = list(historique)
                b.encheres = list(encheres)   # les vraies enchères de la donne
                c = b.jouer_carte(mains[j], jouables, pli, contrat, j, regles)

            mains[j].remove(c)
            pli.append((j, c))
            historique.append((j, c))

        gagnant, _ = gagnant_pli(pli, atout)
        eq = gagnant % 2
        pts = sum(points(c, atout) for _, c in pli)
        if num == 8:
            pts += regles["dix_de_der"]
        pts_eq[eq] += pts
        plis_eq[eq] += 1
        premier = gagnant

    belote = equipe_belote(mains_depart, atout)
    marque, reussi = decompte(contrat, pts_eq, plis_eq, belote, regles)
    est_attaque = (camp_teste == contrat["joueur"] % 2)
    succes = reussi if est_attaque else (not reussi)
    return int(pts_eq[camp_teste]), bool(succes)


def evaluer_donne_complete(graine):
    """Joue une donne avec les 6 moteurs. Ne plante jamais : renvoie l'erreur à la place."""
    try:
        random.seed(graine)            # Comme l'ancien script -> mêmes donnes
        mains = distribuer()
        donneur = graine % 4
        regles = REGLES_STANDARD

        joueurs_annonce = [JoueurIA() for _ in range(4)]
        contrat = phase_annonces(mains, donneur, joueurs_annonce, regles, afficher=False)
        if contrat is None:
            return {"graine": graine, "passe": True}
        # Le premier à parler a toujours le carnet complet des enchères
        encheres = list(joueurs_annonce[(donneur + 1) % 4].encheres)


        camp_teste = 0
        res = {"graine": graine,
               "role": "attaque" if contrat["joueur"] % 2 == 0 else "defense",
               "valeur": int(contrat["valeur"]),
               "plis_reseau_oracle": PLIS_RESEAU_ORACLE}
        res["encheres"] = encheres

        for mot in MOTEURS:
            t0 = time.time()
            pts, ok = simuler_une_table(graine, mains, contrat, donneur, regles, mot, camp_teste, encheres)

            res[f"{mot}_pts"] = pts
            res[f"{mot}_ok"] = ok
            res[f"{mot}_sec"] = round(time.time() - t0, 3)
        return res
    except Exception as e:
        return {"graine": graine, "erreur": repr(e)}


# ======================================================================
# LECTURE DU FICHIER DE RÉSULTATS
# ======================================================================
def lire_resultats():
    lignes = []
    if os.path.exists(FICHIER_RESULTATS):
        with open(FICHIER_RESULTATS, encoding="utf-8") as f:
            for ligne in f:
                ligne = ligne.strip()
                if ligne:
                    try:
                        lignes.append(json.loads(ligne))
                    except json.JSONDecodeError:
                        pass   # ligne coupée par un arrêt brutal : on l'ignore
    return lignes


# ======================================================================
# ANALYSE : points perdus par rapport à l'Oracle, avec marge d'erreur
# ======================================================================
def moyenne_et_marge(valeurs):
    """Moyenne et marge d'erreur à 95 % (« vraie valeur probablement dans ± marge »)."""
    v = np.array(valeurs, dtype=float)
    if len(v) < 2:
        return (float(v.mean()) if len(v) else 0.0), 0.0
    return float(v.mean()), float(1.96 * v.std(ddof=1) / np.sqrt(len(v)))

def analyser():
    toutes = lire_resultats()
    donnes = [d for d in toutes if "role" in d]
    erreurs = [d for d in toutes if "erreur" in d]
    passes = [d for d in toutes if d.get("passe")]

    if erreurs:
        print(f"\n⚠️  {len(erreurs)} donne(s) en erreur. Exemple :")
        print("   ", erreurs[0]["erreur"])
    if not donnes:
        print("Aucune donne exploitable dans", FICHIER_RESULTATS)
        return

    print("=" * 96)
    print(f"RÉSULTATS SUR {len(donnes)} DONNES   (donnes passées : {len(passes)}, erreurs : {len(erreurs)})")
    print("=" * 96)

    for role, titre in [("attaque", "EN ATTAQUE"), ("defense", "EN DÉFENSE"), ("tout", "GLOBAL")]:
        sel = donnes if role == "tout" else [d for d in donnes if d["role"] == role]
        if not sel:
            continue
        print(f"\n--- {titre} ({len(sel)} donnes) ---")
        print(f"{'Moteur':<18} | {'Pts faits':>9} | {'Perdus vs Oracle':>17} | "
              f"{'Écart vs MC-IA':>15} | {'Succès':>7} | {'Sec/partie':>10}")
        print("-" * 96)
        for mot in MOTEURS:
            pts = [d[f"{mot}_pts"] for d in sel]
            perdus = [d["oracle_pts"] - d[f"{mot}_pts"] for d in sel]
            ecart = [d[f"{mot}_pts"] - d["mcia_pts"] for d in sel]
            m_p, e_p = moyenne_et_marge(perdus)
            m_e, e_e = moyenne_et_marge(ecart)
            succes = 100 * np.mean([d[f"{mot}_ok"] for d in sel])
            sec = np.mean([d.get(f"{mot}_sec", 0) for d in sel])
            print(f"{NOMS[mot]:<18} | {np.mean(pts):9.1f} | {m_p:7.1f} ± {e_p:5.1f}   | "
                  f"{m_e:+6.1f} ± {e_e:4.1f}  | {succes:6.1f}% | {sec:9.2f}s")

    print("\nCOMMENT LIRE :")
    print(" - « Perdus vs Oracle » : points abandonnés par donne par rapport au jeu parfait.")
    print(" - « Écart vs MC-IA » : + = mieux que Bot-MC-IA, - = moins bien.")
    print(" - Si le ± est plus grand que l'écart lui-même, la différence N'EST PAS prouvée.")
    print(" - « Sec/partie » : si Bot-MC-IA est aussi rapide que l'IA pure, son Monte-Carlo ne tourne pas.")


# ======================================================================
# LANCEMENT DU CALCUL (avec reprise automatique)
# ======================================================================
def lancer():
    deja = lire_resultats()

    # Sécurité : ne pas mélanger des résultats obtenus avec des réglages différents
    anciens_reglages = {d.get("plis_reseau_oracle") for d in deja if "role" in d}
    if anciens_reglages and anciens_reglages != {PLIS_RESEAU_ORACLE}:
        print(f"⛔ Le fichier {FICHIER_RESULTATS} contient des résultats faits avec un autre")
        print("   réglage PLIS_RESEAU_ORACLE. Renomme ou supprime ce fichier, puis relance.")
        return

    graines_faites = {d["graine"] for d in deja}
    nb_valides = sum(1 for d in deja if "role" in d)
    nb_erreurs = sum(1 for d in deja if "erreur" in d)

    if nb_valides >= NB_DONNES:
        print(f"Objectif déjà atteint ({nb_valides} donnes). Affichage des résultats :")
        analyser()
        return
    if nb_valides:
        print(f"♻️  Reprise : {nb_valides} donnes déjà faites, on continue.")

    graines = [g for g in range(PREMIERE_GRAINE, PREMIERE_GRAINE + NB_DONNES * 5)
               if g not in graines_faites]

    print("=" * 70)
    print(f"🌙 BENCHMARK : objectif {NB_DONNES} donnes, Oracle exact dès le pli {PLIS_RESEAU_ORACLE + 1}")
    print(f"   Résultats écrits au fur et à mesure dans : {FICHIER_RESULTATS}")
    print("=" * 70)

    debut = time.time()
    nb_nouvelles = 0
    with open(FICHIER_RESULTATS, "a", encoding="utf-8") as f, \
         mp.get_context("fork").Pool(os.cpu_count(), initializer=init_worker) as pool:
        for res in pool.imap_unordered(evaluer_donne_complete, graines, chunksize=1):
            f.write(json.dumps(res, ensure_ascii=False) + "\n")
            f.flush()   # écrit vraiment sur le disque, tout de suite

            if "erreur" in res:
                nb_erreurs += 1
                print(f"  ⚠️ Erreur sur la graine {res['graine']} : {res['erreur']}", flush=True)
                if nb_erreurs >= MAX_ERREURS:
                    print("⛔ Trop d'erreurs, arrêt. Envoie-moi le message d'erreur ci-dessus.")
                    break
                continue
            if "role" not in res:
                continue   # donne où tout le monde a passé

            nb_valides += 1
            nb_nouvelles += 1
            if nb_valides % 10 == 0 or nb_valides >= NB_DONNES:
                ecoule = time.time() - debut
                restant = ecoule / nb_nouvelles * (NB_DONNES - nb_valides)
                print(f"  {nb_valides:5d}/{NB_DONNES} donnes  |  écoulé {ecoule/60:6.1f} min  "
                      f"|  reste ≈ {restant/60:6.1f} min", flush=True)
            if nb_valides >= NB_DONNES:
                break

    print(f"\nCalcul terminé en {(time.time() - debut) / 60:.1f} minutes.\n")
    analyser()


if __name__ == "__main__":
    if "--analyse" in sys.argv:
        analyser()
    else:
        lancer()
