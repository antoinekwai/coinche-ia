"""
diagnostic_regret.py (version corrigée)
Décomposition du regret : sur les donnes où l'Oracle bat le v3,
que fait le v3 si on lui donne la VRAIE distribution des cartes ?
- Gagne -> Regret informationnel (brouillard de guerre / détective)
- Chute -> Regret tactique (faiblesse du simulateur interne IA)
"""
import time
import json
import random
import numpy as np
import torch
from regles import REGLES_STANDARD
from moteur import distribuer, cartes_jouables, gagnant_pli, points, equipe_belote, decompte
from test_mc_encheres import MCEncheres
from bot_mc_ia_v3 import BotMCIAv3
import bot_mc_ia

FICHIER_RESULTATS = "resultats_v4.jsonl"
NB_TESTS = 100  # 100 donnes d'écart analysées


class BotMCIAv3Omniscient(BotMCIAv3):
    """Même bot que le v3, mais son détective renvoie la vraie donne courante."""
    nom = "Bot-v3-Omniscient"

    def __init__(self, vraie_donne_courante_ref):
        super().__init__()
        self.vraie_donne_ref = vraie_donne_courante_ref

    def jouer_carte(self, main, jouables, pli, contrat, joueur, regles):
        if len(jouables) == 1:
            return jouables[0]

        # Détective parfait : renvoie la vraie répartition actuelle des 4 mains
        def detective_parfait(*args, **kwargs):
            return [list(m) for m in self.vraie_donne_ref]

        ancien = bot_mc_ia.imaginer_donnes_contraintes
        bot_mc_ia.imaginer_donnes_contraintes = detective_parfait
        try:
            return super().jouer_carte(main, jouables, pli, contrat, joueur, regles)
        finally:
            bot_mc_ia.imaginer_donnes_contraintes = ancien


# 1. Sélectionner les NB_TESTS premières donnes où Oracle bat v3
candidats = []
with open(FICHIER_RESULTATS, encoding="utf-8") as f:
    for ligne in f:
        try:
            d = json.loads(ligne)
        except:
            continue
        if d.get("oracle_ok") and not d.get("mcia_v3_ok"):
            candidats.append(d)
        if len(candidats) >= NB_TESTS:
            break

print(f"=== DIAGNOSTIC DU REGRET SUR {len(candidats)} DONNES CRITIQUES ===")
print("Régime : v3 Standard (KO dans la nuit) vs v3 Omniscient (cartes visibles dans sa tête)")
print("-" * 75)

bilan = {
    "attaque": {"total": 0, "omni_reussis": 0},
    "defense": {"total": 0, "omni_reussis": 0}
}

t_debut = time.time()
for idx, d in enumerate(candidats, 1):
    graine = d["graine"]
    role = d["role"]

    # Conversion propre des enchères JSON en tuples Python
    encheres_propres = []
    for item in d["encheres"]:
        j = item[0]
        act = item[1]
        if isinstance(act, list):
            act = tuple(act)
        encheres_propres.append((j, act))

    # Trouver le dernier contrat annoncé
    dernier_c = None
    for j_e, act in encheres_propres:
        if isinstance(act, tuple):
            dernier_c = (j_e, act[0], act[1])

    preneur = dernier_c[0] if dernier_c else (0 if role == "attaque" else 1)
    valeur = dernier_c[1] if dernier_c else d["valeur"]
    atout = dernier_c[2] if dernier_c else "♠"
    est_coinche = 1 if any(dec == "coinche" for _, dec in encheres_propres) else 0

    contrat_dict = {
        "valeur": valeur,
        "atout": atout,
        "joueur": preneur,
        "coinche": est_coinche,
        "capot": False
    }

    # Reconstituer la donne initiale exacte
    random.seed(graine)
    mains_depart = distribuer()
    donneur = graine % 4

    # Hasard identique à la table du benchmark
    random.seed(graine * 10 + 7)
    np.random.seed((graine * 10 + 7) % (2**32))
    torch.manual_seed(graine * 10 + 7)

    mains_courantes = [list(m) for m in mains_depart]
    bot_omni = BotMCIAv3Omniscient(mains_courantes)
    adversaire = MCEncheres()

    historique, pts_eq, plis_eq = [], [0, 0], [0, 0]
    premier = (donneur + 1) % 4
    camp_teste = 0

    while len(historique) < 32:
        pli = []
        for k in range(4):
            j = (premier + k) % 4
            jouables = cartes_jouables(mains_courantes[j], pli, atout, j, REGLES_STANDARD)
            if j % 2 == camp_teste:
                bot_omni.historique = list(historique)
                bot_omni.encheres = list(encheres_propres)
                c = bot_omni.jouer_carte(mains_courantes[j], jouables, pli, contrat_dict, j, REGLES_STANDARD)
            else:
                adversaire.historique = list(historique)
                adversaire.encheres = list(encheres_propres)
                c = adversaire.jouer_carte(mains_courantes[j], jouables, pli, contrat_dict, j, REGLES_STANDARD)
            mains_courantes[j].remove(c)
            pli.append((j, c))
            historique.append((j, c))

        gagnant = gagnant_pli(pli, atout)[0]
        premier = gagnant
        p = sum(points(c, atout) for _, c in pli)
        if len(historique) == 32:
            p += REGLES_STANDARD["dix_de_der"]
        pts_eq[gagnant % 2] += p
        plis_eq[gagnant % 2] += 1

    bel = equipe_belote(mains_depart, atout)
    marque, reussi = decompte(contrat_dict, pts_eq, plis_eq, bel, REGLES_STANDARD)

    gagne_omni = reussi if role == "attaque" else not reussi
    bilan[role]["total"] += 1
    if gagne_omni:
        bilan[role]["omni_reussis"] += 1

    symbole = "✅ GAGNÉ (Regret Info)" if gagne_omni else "❌ PERDU (Regret Tactique)"
    print(f"[{idx:3d}/{NB_TESTS}] Graine {graine} ({role:<7s} {contrat_dict['valeur']:3d} {atout}) : {symbole}", flush=True)

ecoule = time.time() - t_debut
tot = bilan["attaque"]["total"] + bilan["defense"]["total"]
reussis = bilan["attaque"]["omni_reussis"] + bilan["defense"]["omni_reussis"]

print("\n" + "=" * 75)
print(f"RÉSULTAT DU DIAGNOSTIC SUR {tot} DONNES CRITIQUES (en {ecoule:.1f}s) :")
print("=" * 75)
print(f"GLOBAL : Le v3 Omniscient réussit {reussis} / {tot} ({100*reussis/tot:.1f} %)")
pct_info = 100 * reussis / tot
pct_tact = 100 * (tot - reussis) / tot
print(f"  👉 REGRET INFORMATIONNEL (détective / cartes cachées) : {pct_info:.1f} %")
print(f"  👉 REGRET TACTIQUE       (moteur de jeu / simulateur) : {pct_tact:.1f} %")
print("-" * 75)
att_tot = bilan["attaque"]["total"]
att_ok = bilan["attaque"]["omni_reussis"]
print(f"En Attaque : {att_ok} / {att_tot} sauvées ({100*att_ok/att_tot:.1f} %)")
def_tot = bilan["defense"]["total"]
def_ok = bilan["defense"]["omni_reussis"]
print(f"En Défense : {def_ok} / {def_tot} sauvées ({100*def_ok/def_tot:.1f} %)")
