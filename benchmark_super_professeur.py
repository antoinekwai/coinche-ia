"""
benchmark_super_professeur.py
Test de qualification du Super-Professeur (Policy-Guided Search) :
- Plis 1 à 3 : Top-3 cartes de IA_V2 départagées par MC 60 simulations + Détective v5
- Plis 4 à 8 : MC 40 simulations + Détective v3
Face au champion officiel BotMCIAv6 sur 150 donnes neuves appariées.
"""
import time
import random
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
import bot_mc_ia

NB_DONNES = 150
PREMIERE_GRAINE = 160_000_000


class BotSuperProfesseur(BotMCIAv6):
    nom = "Super-Prof (Top3 + MC60)"
    nb_sims_debut = 60
    nb_sims_fin = 40
    top_k = 3

    def jouer_carte(self, main, jouables, pli, contrat, joueur, regles):
        if len(jouables) == 1:
            return jouables[0]

        atout = contrat["atout"]
        eq, attaque = joueur % 2, contrat["joueur"] % 2

        # --- ÉTAGE 1 : PLIS 1 À 3 (Recherche guidée par IA_V2 + MC 60s + Det v5) ---
        if len(self.historique) < 12:
            # 1. Évaluation rapide de toutes les cartes par IA_V2
            self.ia_v2.historique = list(self.historique)
            self.ia_v2.encheres = list(self.encheres) if self.encheres else []

            s = encoder_situation_v2(main, pli, self.historique, contrat, joueur, regles, self.encheres)
            def_p = bool(s[282] == 1.0)
            vec_c = np.stack([encoder_carte_v2(cand, atout, main, self.historique, pli, def_p) for cand in jouables])
            s_rep = np.repeat(s[None, :], len(jouables), axis=0)
            x_eval = np.concatenate([s_rep, vec_c], axis=1)

            with torch.no_grad():
                notes = charger_v2(self.fichier_reseau)(torch.from_numpy(x_eval)).squeeze(1).numpy()

            # 2. Élagage : ne garder que les Top-K meilleures cartes selon l'IA
            k_gardees = min(self.top_k, len(jouables))
            indices_tries = np.argsort(notes)[::-1][:k_gardees]
            finalistes = [jouables[i] for i in indices_tries]

            # Si une carte écrase totalement les autres dans le réseau, la jouer direct
            if len(finalistes) >= 2 and (notes[indices_tries[0]] - notes[indices_tries[1]] >= 0.35):
                return finalistes[0]

            # 3. Départage haute précision des finalistes par MC 60 simulations + Détective v5
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

        # --- ÉTAGE 2 : PLIS 4 À 8 (Monte-Carlo 40s + Détective v3 standard) ---
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

print(f"=== QUALIFICATION DU SUPER-PROFESSEUR : {NB_DONNES} donnes appariées ===")
print("v6 (Champion officiel) vs Super-Prof (Top-3 IA + MC 60s au début)")
print("-" * 75)

donnes_jouees = 0
res_pts = {m: [] for m in MOTS}
res_sec = {m: [] for m in MOTS}
res_ok = {m: [] for m in MOTS}
res_marque = {m: [] for m in MOTS}

t_debut = time.time()

for g in range(PREMIERE_GRAINE, PREMIERE_GRAINE + NB_DONNES * 3):
    if donnes_jouees >= NB_DONNES:
        break

    random.seed(g); np.random.seed(g % 2**32); torch.manual_seed(g)
    mains_init = distribuer()
    donneur = g % 4
    joueurs_ench = [JoueurIA_V2(fichier=FICHIER_V6_RESEAU) for _ in range(4)]
    contrat = phase_annonces(mains_init, donneur, joueurs_ench, REGLES_STANDARD, afficher=False)
    if contrat is None:
        continue

    donnes_jouees += 1
    premier_parle = (donneur + 1) % 4
    encheres = list(joueurs_ench[premier_parle].encheres)
    camp = 0
    role = "attaque" if contrat["joueur"] % 2 == camp else "defense"
    val = contrat["valeur"]
    mult = 2 if contrat.get("coinche", 0) > 0 else 1
    atout = contrat["atout"]

    for nom, cls_m in MOTS.items():
        random.seed(g * 10 + 7); np.random.seed((g * 10 + 7) % 2**32); torch.manual_seed(g * 10 + 7)
        mains_c = [list(m) for m in mains_init]
        bot = cls_m()
        adv = MCEncheres()
        hist, p_eq = [], [0, 0]
        prem = (donneur + 1) % 4

        t0 = time.time()
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

        dt = time.time() - t0
        bel = equipe_belote(mains_init, atout)
        _, reussi = decompte(contrat, p_eq, [0,0], bel, REGLES_STANDARD)
        gagne = reussi if role == "attaque" else not reussi
        marque_camp = (val * mult) if gagne else (-val * mult)

        res_pts[nom].append(p_eq[camp])
        res_sec[nom].append(dt)
        res_ok[nom].append(gagne)
        res_marque[nom].append(marque_camp)

    if donnes_jouees % 25 == 0:
        ec = time.time() - t_debut
        m_v6 = np.mean(res_marque["v6_champion"])
        m_sp = np.mean(res_marque["super_prof"])
        diff = m_sp - m_v6
        print(f"  {donnes_jouees:3d}/{NB_DONNES} donnes | {ec/60:4.1f} min | Marque: v6={m_v6:+.1f} vs SuperProf={m_sp:+.1f} (diff: {diff:+.1f})", flush=True)

print("\n" + "=" * 75)
print(f"RÉSULTATS QUALIFICATION SUR {donnes_jouees} DONNES :")
print("=" * 75)
m6 = np.array(res_marque["v6_champion"], dtype=float)
msp = np.array(res_marque["super_prof"], dtype=float)
ecart = msp - m6
marge = 1.96 * ecart.std(ddof=1) / np.sqrt(len(ecart))

for nom in MOTS:
    p_m = np.mean(res_pts[nom])
    tx = 100 * np.mean(res_ok[nom])
    sc_m = np.mean(res_sec[nom])
    mq = np.mean(res_marque[nom])
    txt_diff = f"{ecart.mean():+.1f} ± {marge:.1f}" if nom == "super_prof" else "référence"
    print(f"{nom:<16} | Pts faits: {p_m:5.1f} | Succès: {tx:5.1f}% | Temps: {sc_m:4.2f}s | Marque: {mq:+6.1f} | Diff vs v6: {txt_diff}")
