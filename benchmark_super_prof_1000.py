"""
benchmark_super_prof_1000.py
GRAND BENCHMARK D'ANALYSE DÉTAILLÉE : 1 000 DONNES APPARIÉES
v6 (Champion officiel) vs Super-Prof (Top-3 IA + MC 60s au début)
Découpage automatique :
- Attaque vs Défense
- Contrats standards (<= 100) vs Gros contrats (>= 110)
- Contrats normaux vs Coinchés
"""
import os, sys, time, json, random
import numpy as np
import torch
from regles import REGLES_STANDARD
from moteur import distribuer, cartes_jouables, gagnant_pli, points, equipe_belote, decompte
from partie import phase_annonces
from test_mc_encheres import MCEncheres
from ia_modele_v2 import JoueurIA_V2, charger_v2
from bot_mc_ia_v6 import BotMCIAv6, FICHIER_V6_RESEAU
from detective_v3 import imaginer_v3
from detective_v5 import imaginer_v5
from montecarlo import belote_imaginee, contrat_reussi
from ia_encodage_v2 import encoder_situation_v2, encoder_carte_v2

NB_DONNES = 1000
FICHIER_RESULTATS = "resultats_super_prof_1000.jsonl"
GRAINE_BASE = 170_000_000


class BotSuperProfesseur(BotMCIAv6):
    nom = "Super-Prof"
    nb_sims_debut = 60
    nb_sims_fin = 40
    top_k = 3

    def jouer_carte(self, main, jouables, pli, contrat, joueur, regles):
        if len(jouables) == 1:
            return jouables[0]

        atout = contrat["atout"]
        eq, attaque = joueur % 2, contrat["joueur"] % 2

        # Plis 1 à 3 : Élagage Top-3 IA + MC 60s avec Détective v5
        if len(self.historique) < 12:
            self.ia_v2.historique = list(self.historique)
            self.ia_v2.encheres = list(self.encheres) if self.encheres else []

            s = encoder_situation_v2(main, pli, self.historique, contrat, joueur, regles, self.encheres)
            def_p = bool(s[282] == 1.0)
            vec_c = np.stack([encoder_carte_v2(cand, atout, main, self.historique, pli, def_p) for cand in jouables])
            s_rep = np.repeat(s[None, :], len(jouables), axis=0)
            x_eval = np.concatenate([s_rep, vec_c], axis=1)

            with torch.no_grad():
                notes = charger_v2(self.fichier_reseau)(torch.from_numpy(x_eval)).squeeze(1).numpy()

            k_gardees = min(self.top_k, len(jouables))
            indices_tries = np.argsort(notes)[::-1][:k_gardees]
            finalistes = [jouables[i] for i in indices_tries]

            # Si le premier écrase nettement le deuxième (>= 0.35), jouer direct
            if len(finalistes) >= 2 and (notes[indices_tries[0]] - notes[indices_tries[1]] >= 0.35):
                return finalistes[0]

            mains_ech = [imaginer_v5(main, joueur, self.historique, self.encheres, atout, regles)
                         for _ in range(self.nb_sims_debut)]

            scores = {c: 0.0 for c in finalistes}
            for m_sim in mains_ech:
                bel = belote_imaginee(m_sim, self.historique, atout)
                for c in finalistes:
                    pts_t, pl_t = self.simuler_avec_ia_v2(m_sim, pli, atout, contrat, joueur, c, regles)
                    reussi = contrat_reussi(contrat, pts_t[attaque], pl_t[attaque], bel == attaque, regles)
                    gagne = reussi if eq == attaque else not reussi
                    scores[c] += (1000.0 if gagne else -1000.0) + (pts_t[eq] - pts_t[1 - eq])

            return max(finalistes, key=scores.get)

        # Plis 4 à 8 : MC 40s avec Détective v3
        mains_ech = [imaginer_v3(main, joueur, self.historique, self.encheres, atout, regles)
                     for _ in range(self.nb_sims_fin)]

        scores = {c: 0.0 for c in jouables}
        for m_sim in mains_ech:
            bel = belote_imaginee(m_sim, self.historique, atout)
            for c in jouables:
                pts_t, pl_t = self.simuler_avec_ia_v2(m_sim, pli, atout, contrat, joueur, c, regles)
                reussi = contrat_reussi(contrat, pts_t[attaque], pl_t[attaque], bel == attaque, regles)
                gagne = reussi if eq == attaque else not reussi
                scores[c] += (1000.0 if gagne else -1000.0) + (pts_t[eq] - pts_t[1 - eq])

        return max(jouables, key=scores.get)


MOTS = {
    "v6_champion": BotMCIAv6,
    "super_prof":  BotSuperProfesseur,
}

if os.path.exists(FICHIER_RESULTATS):
    os.remove(FICHIER_RESULTATS)

print(f"=== BENCHMARK ANALYTIQUE : {NB_DONNES:,} DONNES APPARIÉES ===")
print("v6 (Champion) vs Super-Prof (Top-3 IA + MC 60s)")
print(f"Fichier de sortie : {FICHIER_RESULTATS}")
print("-" * 75)

donnes_faites = 0
res_marque = {"v6_champion": [], "super_prof": []}
res_pts = {"v6_champion": [], "super_prof": []}
res_ok = {"v6_champion": [], "super_prof": []}
t_debut = time.time()

with open(FICHIER_RESULTATS, "w", encoding="utf-8") as f_out:
    for g in range(GRAINE_BASE, GRAINE_BASE + NB_DONNES * 3):
        if donnes_faites >= NB_DONNES:
            break

        random.seed(g); np.random.seed(g % 2**32); torch.manual_seed(g)
        mains_init = distribuer()
        donneur = g % 4
        joueurs_ench = [JoueurIA_V2(fichier=FICHIER_V6_RESEAU) for _ in range(4)]
        contrat = phase_annonces(mains_init, donneur, joueurs_ench, REGLES_STANDARD, afficher=False)
        if contrat is None:
            continue

        donnes_faites += 1
        premier_parle = (donneur + 1) % 4
        encheres = list(joueurs_ench[premier_parle].encheres)
        camp = 0
        role = "attaque" if contrat["joueur"] % 2 == camp else "defense"
        val = contrat["valeur"]
        coinche_flag = bool(contrat.get("coinche", 0) > 0)
        mult = 2 if coinche_flag else 1
        atout = contrat["atout"]

        donne_rec = {
            "graine": g, "role": role, "valeur": val, "atout": atout,
            "coinche": coinche_flag, "preneur": contrat["joueur"]
        }

        for nom, cls_m in MOTS.items():
            random.seed(g * 10 + 7); np.random.seed((g * 10 + 7) % 2**32); torch.manual_seed(g * 10 + 7)
            mains_c = [list(m) for m in mains_init]
            bot = cls_m()
            adv = MCEncheres()
            hist, p_eq = [], [0, 0]
            prem = (donneur + 1) % 4

            while len(hist) < 32:
                pli = []
                for step in range(4):
                    j = (prem + step) % 4
                    jbs = cartes_jouables(mains_c[j], pli, atout, j, REGLES_STANDARD)
                    if j % 2 == camp:
                        bot.historique = list(hist); bot.encheres = list(encheres)
                        c = bot.jouer_carte(mains_c[j], jbs, pli, contrat, j, REGLES_STANDARD)
                    else:
                        adv.historique = list(hist); adv.encheres = list(encheres)
                        c = adv.jouer_carte(mains_c[j], jbs, pli, contrat, j, REGLES_STANDARD)
                    mains_c[j].remove(c)
                    pli.append((j, c))
                    hist.append((j, c))
                g_pli = gagnant_pli(pli, atout)[0]
                prem = g_pli
                p_eq[g_pli % 2] += sum(points(cc, atout) for _, cc in pli)
                if len(hist) == 32: p_eq[g_pli % 2] += REGLES_STANDARD["dix_de_der"]

            bel = equipe_belote(mains_init, atout)
            _, reussi = decompte(contrat, p_eq, [0,0], bel, REGLES_STANDARD)
            gagne = reussi if role == "attaque" else not reussi
            marque_camp = (val * mult) if gagne else (-val * mult)

            res_marque[nom].append(marque_camp)
            res_pts[nom].append(p_eq[camp])
            res_ok[nom].append(gagne)
            donne_rec[f"{nom}_marque"] = marque_camp
            donne_rec[f"{nom}_ok"] = gagne

        f_out.write(json.dumps(donne_rec, ensure_ascii=False) + "\n")
        f_out.flush()

        if donnes_faites % 100 == 0:
            ec = time.time() - t_debut
            vitesse = donnes_faites / ec
            reste = (NB_DONNES - donnes_faites) / vitesse
            m_v6 = np.mean(res_marque["v6_champion"])
            m_sp = np.mean(res_marque["super_prof"])
            diff = m_sp - m_v6
            print(f"  {donnes_faites:4d}/{NB_DONNES} donnes | {ec/60:4.1f} min écoulées | reste ≈ {reste/60:4.1f} min | Marque: v6={m_v6:+.1f} vs SuperProf={m_sp:+.1f} (diff: {diff:+.1f})", flush=True)

# =========================================================================
# ANALYSE MULTI-DIMENSIONNELLE FINALE
# =========================================================================
print("\n" + "=" * 80)
print("RÉSULTATS DE L'ANALYSE DÉTAILLÉE SUR 1 000 DONNES :")
print("=" * 80)

with open(FICHIER_RESULTATS, encoding="utf-8") as f:
    toutes = [json.loads(l) for l in f]

def afficher_sous_groupe(titre_grp, sous_donnes):
    if not sous_donnes: return
    m6 = np.array([d["v6_champion_marque"] for d in sous_donnes], dtype=float)
    msp = np.array([d["super_prof_marque"] for d in sous_donnes], dtype=float)
    diff = msp - m6
    marge = 1.96 * diff.std(ddof=1) / np.sqrt(len(diff))
    tx6 = 100 * sum(1 for d in sous_donnes if d["v6_champion_ok"]) / len(sous_donnes)
    txsp = 100 * sum(1 for d in sous_donnes if d["super_prof_ok"]) / len(sous_donnes)
    print(f"{titre_grp:<32} ({len(sous_donnes):4d} donnes) | v6: {m6.mean():+5.1f} ({tx6:.1f}%) | SuperProf: {msp.mean():+5.1f} ({txsp:.1f}%) | Diff: {diff.mean():+5.1f} ± {marge:.1f}")

afficher_sous_groupe("GLOBAL COMPLET", toutes)
print("-" * 80)
afficher_sous_groupe("  • EN ATTAQUE", [d for d in toutes if d["role"] == "attaque"])
afficher_sous_groupe("  • EN DÉFENSE", [d for d in toutes if d["role"] == "defense"])
print("-" * 80)
afficher_sous_groupe("  • CONTRATS STANDARDS (<= 100)", [d for d in toutes if d["valeur"] <= 100])
afficher_sous_groupe("  • GROS CONTRATS (>= 110)", [d for d in toutes if d["valeur"] >= 110])
print("-" * 80)
afficher_sous_groupe("  • CONTRATS NORMAUX (non coinchés)", [d for d in toutes if not d["coinche"]])
afficher_sous_groupe("  • CONTRATS COINCHÉS (x2)", [d for d in toutes if d["coinche"]])
print("=" * 80)
