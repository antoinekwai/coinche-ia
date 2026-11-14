"""
etude_encheres_disputees.py
Laboratoire d'extraction de données sur les enchères disputées :
Quand l'adversaire surenchérit au-delà de [valeur_base + 10] :
- Simule l'espérance de Passe, Surenchère (+20, +30, +40) et Coinche sur 30 donnes.
- Enregistre la morphologie complète de la main du joueur et le choix optimal mathématique.
- Sortie : donnees_combat_encheres.jsonl
"""
import os, time, json, random
import numpy as np
import torch
from regles import REGLES_STANDARD
from moteur import distribuer, COULEURS, RANGS, points, cartes_jouables, gagnant_pli, decompte, equipe_belote
from partie import phase_annonces
from ia_modele_v2 import JoueurIA_V2
from bot_mc_ia_v6 import BotMCIAv6, FICHIER_V6_RESEAU
from detective_v5 import imaginer_v5
from montecarlo import belote_imaginee, contrat_reussi

NB_DONNES = 1500
FICHIER_SORTIE = "donnees_combat_encheres.jsonl"
GRAINE_BASE = 300_000_000

print(f"=== LABORATOIRE D'ENCHÈRES DISPUTÉES : {NB_DONNES} donnes ===")
print(f"Enregistrement des décisions de combat dans : {FICHIER_SORTIE}")
print("-" * 75)

_BOT = BotMCIAv6(nb_simulations=1, fichier_reseau=FICHIER_V6_RESEAU)

def morphologie_main(main, atout, coul_adverse):
    """Extrait tous les descripteurs physiques d'une main pour l'analyse."""
    nb_at = sum(1 for c in main if c[1] == atout)
    has_v = ('V', atout) in main
    has_9 = ('9', atout) in main
    has_as_atout = ('A', atout) in main
    
    as_ext = sum(1 for c in main if c[0] == 'A' and c[1] != atout)
    dix_ext = sum(1 for c in main if c[0] == '10' and c[1] != atout)
    
    # Répartition des couleurs annexes
    longueurs_annexes = []
    chicanes = 0
    singletons = 0
    doubletons = 0
    longue_4 = 0
    
    for c in COULEURS:
        if c != atout:
            l = sum(1 for carte in main if carte[1] == c)
            longueurs_annexes.append(l)
            if l == 0: chicanes += 1
            elif l == 1: singletons += 1
            elif l == 2: doubletons += 1
            elif l >= 4: longue_4 += 1
            
    # Tient-on des honneurs dans la couleur adverse ?
    honneurs_adv = sum(1 for c in main if c[1] == coul_adverse and c[0] in ('A', '10', 'R', 'D'))
    nb_adv = sum(1 for c in main if c[1] == coul_adverse)

    return {
        "atouts_nb": nb_at,
        "atout_valet": has_v,
        "atout_neuf": has_9,
        "atout_as": has_as_atout,
        "as_ext": as_ext,
        "dix_ext": dix_ext,
        "chicanes": chicanes,
        "singletons": singletons,
        "doubletons": doubletons,
        "a_longue_4": longue_4 > 0,
        "honneurs_couleur_adverse": honneurs_adv,
        "cartes_couleur_adverse": nb_adv,
    }

def evaluer_options_combat(main, joueur, encheres_avant, contrat_actuel, coul_choisie, val_surenchere, nb_simuls=25):
    """Simule par Monte-Carlo la marque moyenne de Passe, Surenchère et Coinche."""
    atout = coul_choisie
    coul_adv = contrat_actuel["atout"]
    val_adv = contrat_actuel["valeur"]
    preneur_adv = contrat_actuel["joueur"]
    camp = joueur % 2
    r = REGLES_STANDARD
    
    # 3 options testées
    c_passe = {"valeur": val_adv, "atout": coul_adv, "joueur": preneur_adv, "coinche": 0, "capot": False}
    c_surench = {"valeur": val_surenchere, "atout": atout, "joueur": joueur, "coinche": 0, "capot": False}
    c_coinche = {"valeur": val_adv, "atout": coul_adv, "joueur": preneur_adv, "coinche": 1, "capot": False}
    
    mains_sims = [imaginer_v5(main, joueur, [], encheres_avant, atout, r) for _ in range(nb_simuls)]
    
    bilan = {"passe": 0.0, "surenchere": 0.0, "coinche": 0.0}
    
    for nom_opt, c_opt in [("passe", c_passe), ("surenchere", c_surench), ("coinche", c_coinche)]:
        gains = []
        mult = 2 if c_opt["coinche"] else 1
        v_c = c_opt["valeur"]
        camp_p = c_opt["joueur"] % 2
        
        for m_v in mains_sims:
            pts_t, pl_t = _BOT.simuler_avec_ia_v2(m_v, [], c_opt["atout"], c_opt, joueur, m_v[joueur][0], r)
            bel = belote_imaginee(m_v, [], c_opt["atout"])
            reussi = contrat_reussi(c_opt, pts_t[camp_p], pl_t[camp_p], bel == camp_p, r)
            if camp_p == camp:
                gain = (v_c * mult) if reussi else (-v_c * mult)
            else:
                gain = (v_c * mult) if not reussi else (-v_c * mult)
            gains.append(gain)
        bilan[nom_opt] = round(float(np.mean(gains)), 1)
        
    return bilan

if os.path.exists(FICHIER_SORTIE):
    os.remove(FICHIER_SORTIE)

cas_enregistres = 0
t0 = time.time()

with open(FICHIER_SORTIE, "w", encoding="utf-8") as f_out:
    for g in range(GRAINE_BASE, GRAINE_BASE + NB_DONNES * 2):
        if cas_enregistres >= 500: # 500 cas d'enchères disputées suffisent largement
            break

        random.seed(g); np.random.seed(g % 2**32); torch.manual_seed(g)
        mains_init = distribuer()
        donneur = g % 4
        joueurs_ench = [JoueurIA_V2(fichier=FICHIER_V6_RESEAU) for _ in range(4)]
        
        # Simuler les enchères tour par tour pour attraper les surenchères
        # On déroule phase_annonces en observant les moments de combat
        contrat = phase_annonces(mains_init, donneur, joueurs_ench, REGLES_STANDARD, afficher=False)
        if contrat is None: continue
        
        ench_completes = list(joueurs_ench[(donneur + 1) % 4].encheres)
        
        # Chercher dans l'historique une situation où un camp a été surenchéri par l'autre
        for idx in range(1, len(ench_completes)):
            j_actuel, decision = ench_completes[idx]
            ench_avant = ench_completes[:idx]
            
            # Y avait-il un contrat adverse sur la table juste avant ?
            dernier_adverse = None
            for jj, dd in reversed(ench_avant):
                if isinstance(dd, tuple) and (jj % 2 != j_actuel % 2):
                    dernier_adverse = {"joueur": jj, "valeur": dd[0], "atout": dd[1]}
                    break
                    
            # Notre camp avait-il déjà annoncé une couleur d'atout ?
            mon_camp_atout = None
            valeur_base_notre_camp = 0
            for jj, dd in ench_avant:
                if isinstance(dd, tuple) and (jj % 2 == j_actuel % 2):
                    mon_camp_atout = dd[1]
                    valeur_base_notre_camp = dd[0]
                    break
                    
            if dernier_adverse and mon_camp_atout and dernier_adverse["atout"] != mon_camp_atout:
                val_suivante = dernier_adverse["valeur"] + 10
                depassement = val_suivante - valeur_base_notre_camp
                
                # CAS DE COMBAT CRITIQUE : Il faut monter à +20, +30 ou +40 au-dessus de notre base !
                if depassement in (20, 30, 40) and val_suivante <= 140:
                    main_j = mains_init[j_actuel]
                    partenaire = (j_actuel + 2) % 4
                    partenaire_a_parle = any(jj == partenaire and isinstance(dd, tuple) for jj, dd in ench_avant)
                    partenaire_a_passe = any(jj == partenaire and dd == "passe" for jj, dd in ench_avant)

                    # Simulation des 3 options
                    bilan = evaluer_options_combat(main_j, j_actuel, ench_avant, dernier_adverse, mon_camp_atout, val_suivante)
                    meilleure_action = max(bilan, key=bilan.get)
                    
                    morph = morphologie_main(main_j, mon_camp_atout, dernier_adverse["atout"])
                    
                    donnee = {
                        "graine": g,
                        "joueur": j_actuel,
                        "depassement": depassement,
                        "valeur_adverse": dernier_adverse["valeur"],
                        "atout_adverse": dernier_adverse["atout"],
                        "notre_atout": mon_camp_atout,
                        "valeur_surenchere_testee": val_suivante,
                        "partenaire_a_parle": partenaire_a_parle,
                        "partenaire_a_passe": partenaire_a_passe,
                        "morphologie": morph,
                        "bilan_esperances": bilan,
                        "meilleure_action": meilleure_action,
                        "decision_reelle_joueur": decision if isinstance(decision, str) else decision[0]
                    }
                    
                    f_out.write(json.dumps(donnee, ensure_ascii=False) + "\n")
                    f_out.flush()
                    cas_enregistres += 1
                    
                    if cas_enregistres % 50 == 0:
                        print(f"  {cas_enregistres:3d}/500 cas critiques enregistrés en {time.time()-t0:.1f}s...", flush=True)

print("=" * 75)
print(f"✅ EXTRACTION TERMINÉE : {cas_enregistres} cas de combat réels enregistrés dans {FICHIER_SORTIE} !")
