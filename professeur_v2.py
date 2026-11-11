"""
professeur_v2.py
MODULE PÉDAGOGIQUE OFFICIEL COINCHE IA (Novembre 2026) :
1. Jeu de la carte : évaluation par le moteur champion BotMCIAv6 (Réseau V2 + Détective v3).
   Zéro JoueurRegles, vraies simulations neuronales V2.
2. Diagnostics tactiques précis (As-10, atout au preneur, don de points, timing de purge).
3. Enchères : évaluation par rapport à la grille officielle du Système v2 et à la formule de coinche.
"""
import random
import numpy as np
import torch
from moteur import cartes_jouables, COULEURS, points, gagnant_pli, RANGS
from regles import REGLES_STANDARD
from systeme_v2 import SysV2, niveau_v2
from montecarlo import manques, bilan_passe, belote_imaginee, contrat_reussi
from detective_v3 import imaginer_v3
from ia_joueur import cartes_sont_equivalentes_rapide
from bot_mc_ia_v6 import BotMCIAv6, FICHIER_V6_RESEAU

# Instance singleton du champion pour évaluer les coups
_PROF_BOT = BotMCIAv6(nb_simulations=25, fichier_reseau=FICHIER_V6_RESEAU)


def diagnostiquer_erreur_carte(c_jouee, top_c, jouables, main, pli, contrat, joueur, historique, sont_equiv, ecart_proba, ecart_pts):
    """Génère un diagnostic tactique rigoureux et pédagogique."""
    atout = contrat["atout"]
    attaque = (contrat["joueur"] % 2 == joueur % 2)
    partenaire = (joueur + 2) % 4
    est_preneur = (contrat["joueur"] == joueur)
    est_partenaire_preneur = (attaque and not est_preneur)
    
    pts_jouee = points(c_jouee, atout)
    pts_top = points(top_c, atout)

    # 1. CAS DU MEILLEUR COUP OU COUP ÉQUIVALENT (ZÉRO ERREUR !)
    if c_jouee == top_c:
        if len(pli) == 0 and est_preneur and c_jouee[0] == "V" and c_jouee[1] == atout:
            return "Entame d'école : en tant que preneur, purger au Valet maître désarme immédiatement la défense."
        if len(pli) == 0 and est_partenaire_preneur and c_jouee[1] == atout:
            return "Excellent jeu d'équipe : jouer atout vers votre preneur lui donne la main et purge les adversaires."
        return "Choix optimal. Votre décision maximise les chances de réussite du contrat."

    if sont_equiv:
        return f"Coup équivalent. Vous possédez les cartes maîtresses consécutives ({c_jouee[0]} et {top_c[0]} de {c_jouee[1]}). Jouer l'une ou l'autre est parfaitement équivalent en levée."

    # 2. NON-RESPECT DE LA CONVENTION AS-10 EN ATTAQUE
    if attaque and c_jouee[1] != atout and top_c[1] != atout and c_jouee[1] == top_c[1]:
        if c_jouee[0] == "10" and top_c[0] == "A" and ("A", c_jouee[1]) in main:
            return f"Convention As-10 manquée : sur pli garanti, défaussez impérativement votre As de {c_jouee[1]} pour signaler à votre partenaire que votre 10 est maître derrière !"

    # 3. ERREURS À L'ENTAME (Pli vide)
    if len(pli) == 0:
        # Partenaire du preneur qui a de l'atout mais joue une couleur annexe
        if est_partenaire_preneur and top_c[1] == atout and c_jouee[1] != atout:
            return f"Votre partenaire est preneur : la doctrine commande de lui jouer atout ({top_c[0]}{top_c[1]}) pour lui donner la main et faire tomber les atouts adverses !"
        # Preneur qui oublie de purger
        if est_preneur and top_c[1] == atout and c_jouee[1] != atout:
            return f"Purger les atouts avec {top_c[0]}{top_c[1]} était prioritaire pour neutraliser les coupes adverses avant d'attaquer vos couleurs franches."
        # Encaisser un As extérieur
        if top_c[0] == "A" and top_c[1] != atout and c_jouee[0] != "A":
            return f"Encaisser votre As de {top_c[1]} dès l'entame sécurise une levée nette (+11 pts) avant que la défense ne puisse couper."

    # 4. ERREURS EN COURS DE PLI
    else:
        maitre_actuel, carte_maitresse = gagnant_pli(pli, atout)
        partenaire_maitre = (maitre_actuel == partenaire)
        adversaire_maitre = not partenaire_maitre

        # A. Partenaire maître
        if partenaire_maitre:
            # Gâcher un atout sur le maître du partenaire
            if c_jouee[1] == atout and top_c[1] != atout:
                return f"Votre partenaire tient déjà le pli avec {carte_maitresse[0]}{carte_maitresse[1]} : économisez vos atouts, défaussez une petite carte ({top_c[0]}{top_c[1]})."
            # Oubli de charger en défense en 4e position
            if len(pli) == 3 and not attaque and top_c[0] in ("10", "A") and c_jouee[0] not in ("10", "A"):
                return f"En 4e position, le pli de votre partenaire est 100 % garanti : chargez votre {top_c[0]}{top_c[1]} pour empocher des points précieux pour le camp !"

        # B. Adversaire maître
        if adversaire_maitre:
            # Couper manqué
            pli_virtuel = list(pli) + [(joueur, top_c)]
            top_gagne = (gagnant_pli(pli_virtuel, atout)[0] == joueur)
            carte_jouee_gagne = (gagnant_pli(pli + [(joueur, c_jouee)], atout)[0] == joueur)

            if top_gagne and not carte_jouee_gagne:
                return f"Vous aviez l'opportunité de couper ou reprendre le pli avec {top_c[0]}{top_c[1]} pour briser l'offensive adverse."

            # Don gratuit de points en 4e position sur pli perdu certain
            if len(pli) == 3 and pts_jouee >= 10 and pts_top < pts_jouee:
                return f"Le pli est définitivement remporté par l'adversaire : ne lui offrez pas {c_jouee[0]}{c_jouee[1]} ({pts_jouee} pts gratuits), sacrifiez une petite carte sans valeur."

            # Risque de charge sur pli non garanti (en 3e position)
            if len(pli) == 2 and pts_jouee >= 10 and pts_top < pts_jouee:
                return f"Attention : un adversaire joue encore derrière vous ! Charger {c_jouee[0]}{c_jouee[1]} était trop risqué car le pli n'était pas garanti."

    # 5. NUANCE PURE DE STATISTIQUE
    if ecart_proba <= 0.15:
        return f"Coup solide et tout à fait jouable. L'option {top_c[0]}{top_c[1]} apporte une légère sécurité supplémentaire sur les plis futurs (+{abs(int(ecart_pts))} pts estimés)."
    else:
        return f"Ligne de jeu sous-optimale : jouer {top_c[0]}{top_c[1]} offrait une bien meilleure chance de réussite du contrat (+{int(ecart_proba*100)} % de succès)."


def evaluer_decision_carte(main, jouables, pli, contrat, joueur, carte_jouee, historique, encheres, regles):
    """Évalue la décision de carte de l'humain avec le champion BotMCIAv6."""
    atout = contrat["atout"]
    num_pli = len(historique) // 4 + 1
    
    snapshot = {
        "num_pli": num_pli,
        "main_moment": list(main),
        "pli_moment": [(j, f"{c[0]}{c[1]}") for j, c in pli],
        "carte_jouee": carte_jouee,
        "jouables": list(jouables),
        "est_force": len(jouables) <= 1
    }

    if len(jouables) <= 1:
        snapshot.update({
            "label": "Forcé",
            "couleur": "grey",
            "message": "Coup forcé (une seule carte légale).",
            "explication": "Choix imposé par les règles de la belote.",
            "options": [{"carte": f"{carte_jouee[0]}{carte_jouee[1]}", "proba": "100 %", "pts": "-", "top": True}]
        })
        return snapshot

    eq, attaque = joueur % 2, contrat["joueur"] % 2
    N = _PROF_BOT.nb_simulations

    # Tirage de N mains avec le détective v3 par rejeu des enchères
    mains_echantillons = [
        imaginer_v3(main, joueur, list(historique), list(encheres) if encheres else [], atout, regles)
        for _ in range(N)
    ]

    victoires = {c: 0 for c in jouables}
    pts_totaux = {c: 0 for c in jouables}

    # Points et plis déjà réalisés dans les plis passés de la donne
    passe_pts, passe_plis = bilan_passe(historique, atout)

    # Simulations déroulées par le réseau V2 d'élite
    for m_sim in mains_echantillons:
        bel = belote_imaginee(m_sim, historique, atout)
        for c in jouables:
            pts_futurs, plis_futurs = _PROF_BOT.simuler_avec_ia_v2(m_sim, pli, atout, contrat, joueur, c, regles)
            # Total cumulé de la donne : points passés + points futurs
            pts_cumules = [passe_pts[e] + pts_futurs[e] for e in (0, 1)]
            plis_cumules = [passe_plis[e] + plis_futurs[e] for e in (0, 1)]

            reussi = contrat_reussi(contrat, pts_cumules[attaque], plis_cumules[attaque], bel == attaque, regles)
            gagne = reussi if eq == attaque else not reussi
            if gagne:
                victoires[c] += 1
            pts_totaux[c] += pts_cumules[eq]

    scores_compares = {c: (victoires[c] / N) * 1000.0 + (pts_totaux[c] / N) for c in jouables}
    top_carte = max(jouables, key=scores_compares.get)

    sont_equiv = cartes_sont_equivalentes_rapide(carte_jouee, top_carte, main, pli, atout, historique)
    
    p_top = victoires[top_carte] / N
    p_jouee = victoires[carte_jouee] / N
    ecart_proba = 0.0 if sont_equiv else max(0.0, p_top - p_jouee)
    ecart_pts = (pts_totaux[top_carte] - pts_totaux[carte_jouee]) / N

    # Formatage des options évaluées
    options = []
    for c in sorted(jouables, key=scores_compares.get, reverse=True):
        is_top = (c == top_carte)
        options.append({
            "carte": f"{c[0]}{c[1]}",
            "proba": f"{int((victoires[c] / N) * 100)} %",
            "pts": f"{int(pts_totaux[c] / N)} pts",
            "top": is_top
        })

    # Diagnostic tactique
    explication = diagnostiquer_erreur_carte(
        carte_jouee, top_carte, jouables, main, pli, contrat, joueur,
        historique, sont_equiv, ecart_proba, ecart_pts
    )

    # Étiquettes pédagogiques
    if carte_jouee == top_carte or sont_equiv or ecart_proba <= 0.05:
        apprec = ("Meilleur coup", "green", "🌟 Excellent choix")
    elif ecart_proba <= 0.15:
        apprec = ("Solide", "blue", "👍 Coup solide")
    elif ecart_proba <= 0.25:
        apprec = ("Imprécision", "orange", f"⚠️ Préférable : {top_carte[0]}{top_carte[1]}")
    else:
        apprec = ("Erreur", "red", f"❌ Erreur tactique (meilleur : {top_carte[0]}{top_carte[1]})")

    snapshot.update({
        "label": apprec[0],
        "couleur": apprec[1],
        "message": apprec[2],
        "top_carte": top_carte,
        "ecart": ecart_proba,
        "explication": explication,
        "options": options
    })
    return snapshot


# =============================================================================
# MODULE ENCHÈRES OFFICIEL : ESPÉRANCES CHIFFRÉES + SYSTÈME V2 & COINCHE
# =============================================================================

def simuler_esperance_options_tour(main_depart, encheres_avant, action_choisie, joueur_humain=0, nb_simuls=20):
    """Calcule par simulation l'espérance en points de marque des différentes options."""
    regles = REGLES_STANDARD

    # 1. Contrat en cours avant que l'humain ne parle
    dernier_contrat = None
    for j_p, d_p in encheres_avant:
        if isinstance(d_p, tuple):
            dernier_contrat = (j_p, d_p[0], d_p[1])

    # 2. Options à tester
    options = ["passe"]
    est_adverse = False
    val_actuelle = 80
    coul_actuelle = "♠"
    preneur_actuel = 1

    if dernier_contrat:
        preneur_actuel, val_actuelle, coul_actuelle = dernier_contrat
        est_adverse = (preneur_actuel % 2 != joueur_humain % 2)
        if est_adverse:
            options.append("coinche")

        palier_suivant = val_actuelle + 10
        if palier_suivant <= 160:
            # Meilleure couleur en main (la plus longue)
            coul_pref = max(COULEURS, key=lambda c: sum(1 for x in main_depart if x[1] == c))
            options.append((palier_suivant, coul_pref))
            if coul_actuelle != coul_pref and (palier_suivant, coul_actuelle) not in options:
                options.append((palier_suivant, coul_actuelle))
    else:
        # En ouverture : tester Passe, 80, 90, 100 dans la meilleure couleur
        coul_pref = max(COULEURS, key=lambda c: sum(1 for x in main_depart if x[1] == c))
        for v in (80, 90, 100):
            options.append((v, coul_pref))

    # Ajouter le choix réel du joueur s'il n'est pas déjà dans la liste
    if action_choisie not in options:
        options.append(action_choisie)

    # 3. Tirage de donnes cohérentes avec les enchères passées
    donneur = (encheres_avant[0][0] - 1) % 4 if encheres_avant else 0
    atout_sim = coul_actuelle if dernier_contrat else "♠"
    
    mains_sims = []
    for _ in range(nb_simuls):
        mains_sims.append(imaginer_v3(main_depart, joueur_humain, [], list(encheres_avant), atout_sim, regles))

    eq_humain = joueur_humain % 2
    bilan = {}

    # 4. Évaluation de chaque option en marque nette
    for opt in options:
        if opt == "passe":
            if dernier_contrat is None:
                # Passe générale = 0 point
                bilan["Passe (redistribution)"] = 0.0
                continue
            c = {"valeur": val_actuelle, "atout": coul_actuelle, "joueur": preneur_actuel, "coinche": 0, "capot": False}
            lbl = f"Passe ({val_actuelle} {coul_actuelle})"
        elif opt == "coinche":
            if dernier_contrat is None:
                continue
            c = {"valeur": val_actuelle, "atout": coul_actuelle, "joueur": preneur_actuel, "coinche": 1, "capot": False}
            lbl = f"Coinche ({val_actuelle} {coul_actuelle})"
        elif isinstance(opt, tuple):
            v, co = opt
            est_capot = (v == regles["valeur_capot"])
            c = {"valeur": v, "atout": co, "joueur": joueur_humain, "coinche": 0, "capot": est_capot}
            lbl = f"{'Capot' if est_capot else v} {co}"
        else:
            continue

        gains = []
        mult = 2 if c.get("coinche", 0) > 0 else 1
        val_c = c["valeur"]

        for m in mains_sims:
            # Évaluation rapide par simulation réseau
            pts_tot, plis_tot = _PROF_BOT.simuler_avec_ia_v2(m, [], c["atout"], c, joueur_humain, m[joueur_humain][0], regles)
            bel = belote_imaginee(m, [], c["atout"])
            camp_p = c["joueur"] % 2
            reussi = contrat_reussi(c, pts_tot[camp_p], plis_tot[camp_p], bel == camp_p, regles)
            
            # Marque pour le camp de l'humain
            if camp_p == eq_humain:
                gain = (val_c * mult) if reussi else (-val_c * mult)
            else:
                gain = (val_c * mult) if not reussi else (-val_c * mult)
            gains.append(gain)

        bilan[lbl] = round(float(np.mean(gains)), 1)

    return bilan


def force_defensive_coinche(main, atout):
    """Calcule la force de coinche sur les atouts selon la formule validée."""
    force = 0
    atouts_main = [c for c in main if c[1] == atout]
    nb_atouts = len(atouts_main)
    rangs_atout = [c[0] for c in atouts_main]

    if "V" in rangs_atout: force += 2
    if "9" in rangs_atout and nb_atouts >= 3: force += 1
    if nb_atouts >= 3: force += (nb_atouts - 2)
    if ("R" in rangs_atout or "D" in rangs_atout): force += 1
    return force


def analyser_encheres_humain(main_depart, encheres_partie, joueur_humain=0):
    """Analyse complète tour par tour : Espérances chiffrées + Doctrine Système v2."""
    commentaires = []
    actions_humain = [(idx, d) for idx, (j, d) in enumerate(encheres_partie) if j == joueur_humain]
    if not actions_humain:
        return ["ℹ️ Aucune action enregistrée pour le joueur Sud."]

    sys_v2 = SysV2()

    for tour_num, (idx_action, action) in enumerate(actions_humain, 1):
        encheres_avant = encheres_partie[:idx_action]
        action_nom = f"{action[0]} {action[1]}" if isinstance(action, tuple) else str(action).upper()
        
        dernier_c = None
        for j_prec, act_prec in encheres_avant:
            if isinstance(act_prec, tuple):
                dernier_c = {
                    "valeur": act_prec[0],
                    "atout": act_prec[1],
                    "joueur": j_prec,
                    "coinche": 0,
                    "capot": False
                }

        commentaires.append(f"📍 **Tour {tour_num} : Vous avez choisi [{action_nom}]**")

        # 1. TABLEAU COMPARATIF DES ESPÉRANCES CHIFFRÉES (Monte Carlo)
        try:
            bilan_tour = simuler_esperance_options_tour(main_depart, encheres_avant, action, joueur_humain)
            if bilan_tour:
                meilleure_opt = max(bilan_tour, key=bilan_tour.get)
                # Trier les options par espérance décroissante
                tries = sorted(bilan_tour.items(), key=lambda x: x[1], reverse=True)
                # Garder le top 2 ou 3, en s'assurant d'inclure le choix du joueur s'il est plus bas
                top_opts = dict(tries[:3])
                for opt_lbl, esp in bilan_tour.items():
                    if action_nom in opt_lbl and opt_lbl not in top_opts:
                        top_opts[opt_lbl] = esp

                commentaires.append("  *Espérances comparées (meilleures options) :*")
                for opt_lbl, esp in sorted(top_opts.items(), key=lambda x: x[1], reverse=True):
                    etoile = " 🌟 (Optimal)" if opt_lbl == meilleure_opt else ""
                    signe = "+" if esp > 0 else ""
                    commentaires.append(f"    • {opt_lbl} : **{signe}{esp} pts**{etoile}")
        except Exception as e:
            pass

        # 2. CONSEIL DOCTRINAL SYSTÈME V2 (AVEC LES 4 CRITÈRES OBJECTIFS)
        sys_v2.encheres = list(encheres_avant)
        decision_recommandee = sys_v2.annoncer(main_depart, joueur_humain, dernier_c, REGLES_STANDARD)
        nom_reco = f"{decision_recommandee[0]} {decision_recommandee[1]}" if isinstance(decision_recommandee, tuple) else str(decision_recommandee).upper()

        action_est_optimale = bool(bilan_tour and meilleure_opt and (action_nom.lower() in meilleure_opt.lower()))

        if action == decision_recommandee or action_est_optimale:
            if action == decision_recommandee:
                commentaires.append(f"  • *Système officiel* : Votre décision **{action_nom}** est 100 % conforme aux critères du Système v2.")
            else:
                commentaires.append(f"  • *Décision tactique validée* : Même si la grille théorique envisageait {nom_reco}, votre choix **{action_nom}** maximise l'espérance réelle à la table.")
        else:
            action_verbe = "d'ouvrir" if not dernier_c else "de surenchérir"
            commentaires.append(f"  • *Recommandation Système v2* : Le système conseillait **{nom_reco}**.")
            if action != "passe" and decision_recommandee == "passe":
                commentaires.append(f"    -> *Prise de risque* : Surenchérir à {action_nom} est dangereux sans critères de sécurité (il faut soit 5 atouts, soit 4 avec chicane, soit la Belote R-D en main, soit le soutien du partenaire).")
            elif action == "passe" and decision_recommandee != "passe":
                commentaires.append(f"    -> *Occasion manquée* : Votre jeu remplissait les critères de sécurité pour disputer le contrat à {nom_reco}.")

        # 3. CONSEIL COINCHE SI CONTRAT ADVERSE
        if dernier_c and (dernier_c["joueur"] % 2 != joueur_humain % 2):
            force = force_defensive_coinche(main_depart, dernier_c["atout"])
            val = dernier_c["valeur"]
            seuil_reco = max(1, 4 - (val - 80) // 20)
            if force >= seuil_reco and action != "coinche":
                commentaires.append(f"  • 💡 *Coinche manquée* : Force défensive de {force} (seuil: {seuil_reco}). Coincher rapportait gros !")
            elif action == "coinche" and force < seuil_reco:
                commentaires.append(f"  • ⚠️ *Coinche téméraire* : Force d'atout ({force}) trop faible (seuil: {seuil_reco}). Danger de réussite adverse.")

        if tour_num < len(actions_humain):
            commentaires.append("---")

    return commentaires
