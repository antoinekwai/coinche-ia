import numpy as np
from moteur import cartes_jouables, COULEURS, points, gagnant_pli
from systeme_v2 import niveau_v2
from montecarlo import manques, bilan_passe, belote_imaginee, simuler, contrat_reussi
from test_mc_encheres import MCEncheres

# Instance du professeur Monte Carlo Enchères
PROF_BOT = MCEncheres()
PROF_BOT.nb_simulations = 30

def cartes_sont_equivalentes(c1, c2, main, pli, atout, historique):
    """Vérifie si deux cartes sont strictement équivalentes en pouvoir de levée."""
    if c1[1] != c2[1]:
        return False
    coul = c1[1]
    ordre = ["V", "9", "A", "10", "R", "D", "8", "7"] if coul == atout else ["A", "10", "R", "D", "V", "9", "8", "7"]

    vues = {c for _, c in historique} | {c for _, c in pli}
    restantes = [r for r in ordre if (r, coul) not in vues]

    maitres_en_main = []
    for r in restantes:
        if (r, coul) in main:
            maitres_en_main.append(r)
        else:
            break

    if c1[0] in maitres_en_main and c2[0] in maitres_en_main:
        return True

    if coul != atout and c1[0] in ("7", "8") and c2[0] in ("7", "8"):
        return True

    return False

def diagnostiquer_erreur(c_jouee, top_c, jouables, main, pli, contrat, joueur, historique):
    """Génère un diagnostic clair, précis et sans jargon."""
    atout = contrat["atout"]
    attaque = (contrat["joueur"] % 2 == joueur % 2)
    partenaire = (joueur + 2) % 4
    est_preneur = (contrat["joueur"] == joueur)
    
    pts_jouee = points(c_jouee, atout)
    pts_top = points(top_c, atout)

    # CAS 1 : À l'entame (pli vide)
    if len(pli) == 0:
        if est_preneur:
            if top_c[1] == atout and c_jouee[1] != atout:
                return f"En tant que preneur, il est préférable d'entamer atout ({top_c[0]}{top_c[1]}) pour désarmer la défense avant de jouer vos couleurs annexes."
            if top_c[0] == "V" and top_c[1] == atout:
                return "Quand vous purgez l'atout, commencez toujours par le Valet pour faire tomber les gros atouts sans risque."
            if top_c[0] == "A" and c_jouee[0] != "A":
                return f"Encaisser votre As de {top_c[1]} est plus sûr à ce stade pour faire une levée nette."
        else: # En défense
            if c_jouee[1] == atout and top_c[1] != atout:
                return f"En défense, éviter d'entamer atout : cela aide le preneur à purger. Jouez plutôt dans une couleur annexe comme {top_c[0]}{top_c[1]}."
            if top_c[0] == "A":
                return f"En défense, encaisser votre As de {top_c[1]} assure des points directs pour faire chuter le contrat."

    # CAS 2 : En cours de pli
    else:
        maitre_actuel, carte_maitresse = gagnant_pli(pli, atout)
        partenaire_maitre = (maitre_actuel == partenaire)
        adversaire_maitre = not partenaire_maitre

        # A. Le partenaire est maître
        if partenaire_maitre:
            # On a coupé alors que le partenaire tenait le pli
            if c_jouee[1] == atout and top_c[1] != atout:
                return f"Votre partenaire est déjà maître du pli avec {carte_maitresse[0]}{carte_maitresse[1]} : ne dépensez pas d'atout inutilement, défaussez {top_c[0]}{top_c[1]}."
            # En dernier de parole (pli de 3 cartes)
            if len(pli) == 3:
                if not attaque and top_c[0] == "10" and c_jouee[0] != "10":
                    return "En défense, votre partenaire gagne le pli de façon certaine : chargez votre 10 pour empocher des points cruciaux vers la chute."
                if pts_jouee > pts_top and attaque:
                    return f"En attaque, inutile de surcharger ce pli déjà gagné : préservez vos points ({c_jouee[0]}{c_jouee[1]}) et mettez plutôt {top_c[0]}{top_c[1]}."

        # B. L'adversaire est maître
        if adversaire_maitre:
            # On donne des points sur un pli perdu
            if pts_jouee >= 10 and pts_top < pts_jouee:
                return f"Le pli est perdu au profit de l'adversaire : ne lui donnez pas {c_jouee[0]}{c_jouee[1]} ({pts_jouee} pts). Sacrifiez plutôt {top_c[0]}{top_c[1]}."
            # On pouvait remporter le pli avec un maître
            if top_c[0] in ("V", "A") and c_jouee[0] not in ("V", "A"):
                return f"Prenez la main avec {top_c[0]}{top_c[1]} pour stopper l'attaque adverse et reprendre le contrôle."

    # Explication générale par défaut si aucun cas typique n'est isolé
    if pts_jouee > pts_top:
        return f"Économisez vos points : jouer {c_jouee[0]}{c_jouee[1]} coûte plus cher que {top_c[0]}{top_c[1]} sans apporter d'avantage sur ce pli."
    
    return f"Monte Carlo Enchères démontre que jouer {top_c[0]}{top_c[1]} offre une meilleure probabilité de remplir l'objectif de contrat sur l'ensemble des donnes simulées."

def evaluer_decision_carte(main, jouables, pli, contrat, joueur, carte_jouee, historique, encheres, regles):
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
            "message": "Une seule carte autorisée.",
            "explication": "Choix imposé par les règles de la belote.",
            "options": [{"carte": f"{carte_jouee[0]}{carte_jouee[1]}", "proba": "100%", "pts": "-", "top": True}]
        })
        return snapshot

    # --- SIMULATION MONTE CARLO ENCHÈRES ---
    PROF_BOT.historique = list(historique)
    PROF_BOT.encheres = list(encheres)

    eq, attaque = joueur % 2, contrat["joueur"] % 2
    manque = manques(historique, atout, regles)
    plis_faits = (len(historique) - len(pli)) // 4
    passe_pts, passe_plis = bilan_passe(historique, atout)

    victoires = {c: 0 for c in jouables}
    pts_totaux = {c: 0 for c in jouables}
    N = PROF_BOT.nb_simulations

    for _ in range(N):
        mains = PROF_BOT.imaginer(main, joueur, manque, atout)
        belote = belote_imaginee(mains, historique, atout)
        for c in jouables:
            pts, plis = simuler(mains, pli, contrat, joueur, c, plis_faits, regles)
            total = [passe_pts[e] + pts[e] for e in (0, 1)]
            reussi = contrat_reussi(contrat, total[attaque], passe_plis[attaque] + plis[attaque],
                                    belote == attaque, regles)
            gagne = reussi if eq == attaque else not reussi
            victoires[c] += int(gagne)
            pts_totaux[c] += total[eq]  # <--- POINTS TOTAUX DE LA DONNE (DÉJÀ FAITS + FUTURS)

    scores_compares = {c: (victoires[c] / N) * 1000 + (pts_totaux[c] / N) for c in jouables}
    top_carte = max(jouables, key=scores_compares.get)

    sont_equiv = cartes_sont_equivalentes(carte_jouee, top_carte, main, pli, atout, historique)
    
    p_top = victoires[top_carte] / N
    p_jouee = victoires[carte_jouee] / N
    ecart_proba = 0.0 if sont_equiv else (p_top - p_jouee)

    options = []
    for c in sorted(jouables, key=scores_compares.get, reverse=True):
        is_top = (c == top_carte) or cartes_sont_equivalentes(c, top_carte, main, pli, atout, historique)
        p_c = int(round(100 * victoires[c] / N))
        pts_tot = int(round(pts_totaux[c] / N)) # TOTAL ESTIMÉ SUR LA PARTIE
        options.append({
            "carte": f"{c[0]}{c[1]}",
            "proba": f"{p_c} %",
            "pts": f"{pts_tot} pts",
            "top": is_top
        })

    explication = diagnostiquer_erreur(carte_jouee, top_carte, jouables, main, pli, contrat, joueur, historique)

    if carte_jouee == top_carte or ecart_proba <= 0.03:
        apprec = ("Meilleur coup", "green", "🌟 Excellent choix")
    elif sont_equiv:
        apprec = ("Meilleur coup", "green", f"🌟 Excellent choix (strictement équivalent à {top_carte[0]}{top_carte[1]})")
        explication = f"Vous possédez les cartes maîtresses consécutives ({carte_jouee[0]} et {top_carte[0]} de {carte_jouee[1]}). Jouer l'une ou l'autre a exactement le même pouvoir de levée."
    elif ecart_proba <= 0.10:
        apprec = ("Solide", "blue", "👍 Coup solide")
    elif ecart_proba <= 0.25:
        apprec = ("Imprécision", "orange", f"⚠️ Préférable : {top_carte[0]}{top_carte[1]}")
    else:
        apprec = ("Erreur", "red", f"❌ Erreur (meilleur : {top_carte[0]}{top_carte[1]})")

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
import random
from dispute import coherent
from moteur import decompte, equipe_belote, RANGS

def simuler_esperance_encheres(main_depart, encheres_partie, joueur_humain=0, nb_simuls=35):
    """
    Évalue par simulation l'espérance mathématique des options au moment 
    de la dernière prise de décision de l'humain.
    """
    if not encheres_partie:
        return None

    # Retrouver le dernier moment où l'humain a parlé
    idx_decision = -1
    for idx, (j, d) in enumerate(encheres_partie):
        if j == joueur_humain:
            idx_decision = idx

    if idx_decision == -1:
        return None

    encheres_jusqu_ici = encheres_partie[:idx_decision]
    
    # Identifier le contrat en cours au moment de décider
    dernier_contrat = None
    for j, d in encheres_jusqu_ici:
        if isinstance(d, tuple):
            dernier_contrat = (j, d[0], d[1])

    if dernier_contrat is None:
        return None # Cas de l'ouverture pure

    preneur_actuel, val_actuelle, coul_actuelle = dernier_contrat
    est_adverse = (preneur_actuel % 2 != joueur_humain % 2)
    from app import nom_joueur
    nom_preneur = nom_joueur(preneur_actuel)

    from regles import REGLES_STANDARD
    regles = REGLES_STANDARD
    autres = [p for p in range(4) if p != joueur_humain]
    inconnues = [(r, c) for c in COULEURS for r in RANGS if (r, c) not in main_depart]
    
    donnes_valides = []
    for _ in range(2500):
        random.shuffle(inconnues)
        m = [None] * 4
        m[joueur_humain] = list(main_depart)
        for k, p in enumerate(autres):
            m[p] = inconnues[8*k : 8*k+8]
        if all(coherent(m[p], p, encheres_jusqu_ici) for p in autres):
            donnes_valides.append(m)
            if len(donnes_valides) == nb_simuls:
                break

    if len(donnes_valides) < 10:
        return None

    from dispute import JoueurDispute
    bot_simul = JoueurDispute()
    bot_simul.encheres = list(encheres_partie)  # <--- Ajout de cette ligne
    bilan = {}
    eq_humain = joueur_humain % 2


    # 1. Option "PASSE"
    label_passe = f"Passe (laisser jouer {val_actuelle} {coul_actuelle} par {nom_preneur})"
    c_actuel = {"valeur": val_actuelle, "atout": coul_actuelle, "joueur": preneur_actuel, "coinche": 0, "capot": False}
    gains_passe = []
    for m in donnes_valides:
        pts, plis, bel = bot_simul.jouer(m, c_actuel, regles)
        s, _ = decompte(c_actuel, pts, plis, bel, regles)
        gains_passe.append(s[eq_humain] - s[1 - eq_humain])
    bilan[label_passe] = round(float(np.mean(gains_passe)), 1)

    # 2. Option "COINCHER" (si adverse)
    if est_adverse:
        label_coinche = f"Coinche (sur {val_actuelle} {coul_actuelle})"
        c_coinche = {"valeur": val_actuelle, "atout": coul_actuelle, "joueur": preneur_actuel, "coinche": 1, "capot": False}
        gains_coinche = []
        for m in donnes_valides:
            pts, plis, bel = bot_simul.jouer(m, c_coinche, regles)
            s, _ = decompte(c_coinche, pts, plis, bel, regles)
            gains_coinche.append(s[eq_humain] - s[1 - eq_humain])
        bilan[label_coinche] = round(float(np.mean(gains_coinche)), 1)

    # 3. Option "SURENCHÉRIR"
    palier_suivant = val_actuelle + 10
    if palier_suivant <= 160:
        coul_attaque = max(COULEURS, key=lambda c: sum(1 for x in main_depart if x[1] == c))
        c_attaque = {"valeur": palier_suivant, "atout": coul_attaque, "joueur": joueur_humain, "coinche": 0, "capot": False}
        gains_attaque = []
        for m in donnes_valides:
            pts, plis, bel = bot_simul.jouer(m, c_attaque, regles)
            s, _ = decompte(c_attaque, pts, plis, bel, regles)
            gains_attaque.append(s[eq_humain] - s[1 - eq_humain])
        bilan[f"Surenchérir à {palier_suivant} {coul_attaque}"] = round(float(np.mean(gains_attaque)), 1)

    return bilan

def analyser_encheres_humain(main_depart, encheres_partie, joueur_humain=0):
    commentaires = []
    partenaire = (joueur_humain + 2) % 4
    
    # Lister toutes les actions de l'humain dans la séquence
    actions_humain = [(idx, d) for idx, (j, d) in enumerate(encheres_partie) if j == joueur_humain]
    if not actions_humain:
        return ["ℹ️ Aucune action enregistrée."]

    # 1. ANALYSE DU PREMIER TOUR DE PAROLE DE L'HUMAIN (Ouverture ou première réponse)
    idx_premier, premier_choix = actions_humain[0]
    
    # Regarder ce qui s'était passé avant ce premier choix
    encheres_avant = encheres_partie[:idx_premier]
    ouverture_partenaire = next((d for j, d in encheres_avant if j == partenaire and isinstance(d, tuple)), None)
    
    # CAS A1 : Vous avez ouvert (personne n'avait ouvert dans votre camp)
    if ouverture_partenaire is None:
        couleur_recommandee = max(COULEURS, key=lambda c: niveau_v2(main_depart, c))
        niveau_recommande = niveau_v2(main_depart, couleur_recommandee)

        if niveau_recommande == 0:
            if premier_choix == "passe":
                commentaires.append("✅ **Tour 1 (Passe)** : Votre main ne justifiait pas d'ouvrir d'entrée.")
            else:
                commentaires.append(f"⚠️ **Tour 1 (Ouverture {premier_choix[0]} {premier_choix[1]})** : Audacieux. Selon les critères statistiques v2, votre main justifiait une passe.")
        else:
            if premier_choix == "passe":
                commentaires.append(f"⚠️ **Tour 1 (Passe)** : Occasion manquée. Vous pouviez ouvrir directement à **{niveau_recommande} {couleur_recommandee}** (réussite estimée ≥ 80 %).")
            elif isinstance(premier_choix, tuple):
                val, coul = premier_choix
                if coul == couleur_recommandee and val == niveau_recommande:
                    commentaires.append(f"🌟 **Tour 1 (Ouverture {val} {coul})** : Parfaitement calibrée selon le système recommandé.")
                elif coul == couleur_recommandee and val < niveau_recommande:
                    commentaires.append(f"ℹ️ **Tour 1 (Ouverture {val} {coul})** : Prudente. Vos cartes permettaient d'ouvrir à **{niveau_recommande} {coul}**.")
                else:
                    commentaires.append(f"⚠️ **Tour 1 (Ouverture {val} {coul})** : Prise de risque. Le système conseillait **{niveau_recommande} {coul}**.")

    # CAS A2 : Votre partenaire avait ouvert avant votre tour -> Votre premier choix était une réponse
    else:
        val_ouv, coul_ouv = ouverture_partenaire
        from experience_reponse import reponse_variante
        rep_fn = reponse_variante("court")
        mon_inc = rep_fn(None, main_depart, val_ouv, coul_ouv)
        
        if premier_choix == "passe":
            if mon_inc > 0:
                commentaires.append(f"⚠️ **Tour 1 (Passe sur {val_ouv} {coul_ouv})** : Soutien manqué. Vous deviez remonter de +{mon_inc} ({val_ouv + mon_inc} {coul_ouv}).")
            else:
                commentaires.append(f"✅ **Tour 1 (Passe sur {val_ouv} {coul_ouv})** : Passe correcte (critères de soutien non atteints).")
        elif isinstance(premier_choix, tuple):
            val_h, coul_h = premier_choix
            if coul_h == coul_ouv:
                inc_h = val_h - val_ouv
                if inc_h == mon_inc:
                    commentaires.append(f"🌟 **Tour 1 (Soutien à {val_h} {coul_h})** : Réponse impeccable (+{inc_h}).")
                elif inc_h < mon_inc:
                    commentaires.append(f"ℹ️ **Tour 1 (Soutien à {val_h} {coul_h})** : Timide (+{inc_h}). Vous pouviez monter de +{mon_inc}.")
                else:
                    commentaires.append(f"⚠️ **Tour 1 (Soutien à {val_h} {coul_h})** : Optimiste (+{inc_h}). Le modèle recommandait +{mon_inc}.")

    # 2. ANALYSE DU DERNIER TOUR DE PAROLE (Si vous avez parlé plusieurs fois)
    if len(actions_humain) > 1:
        idx_dernier, dernier_choix = actions_humain[-1]
        dernier_contrat = next((d for j, d in reversed(encheres_partie[:idx_dernier]) if isinstance(d, tuple)), None)
        
        if dernier_contrat:
            from app import nom_joueur
            preneur_nom = nom_joueur(next(j for j, d in reversed(encheres_partie[:idx_dernier]) if isinstance(d, tuple)))
            if dernier_choix == "passe":
                commentaires.append(f"✅ **Tour 2 (Passe)** : Vous vous arrêtez sagement sur {dernier_contrat[0]} {dernier_contrat[1]} de {preneur_nom}.")
            elif isinstance(dernier_choix, tuple):
                commentaires.append(f"👉 **Tour 2 (Surenchère)** : Vous poussez à {dernier_choix[0]} {dernier_choix[1]}.")
            elif dernier_choix == "coinche":
                commentaires.append(f"🔥 **Tour 2 (Coinche)** : Vous coinchez l'adversaire !")

    # 3. CALCUL D'ESPÉRANCE RÉELLE SUR VOTRE MAIN EXACTE (Simulation Monte Carlo)
    bilan_simul = simuler_esperance_encheres(main_depart, encheres_partie, joueur_humain)
    if bilan_simul:
        commentaires.append("---")
        commentaires.append("📊 **Calcul d'espérance réelle sur votre main exacte (Monte Carlo) :**")
        meilleure_opt = max(bilan_simul, key=bilan_simul.get)
        for opt, esp in bilan_simul.items():
            etoile = " 🌟 (Optimal)" if opt == meilleure_opt else ""
            signe = "+" if esp > 0 else ""
            commentaires.append(f"• **{opt}** : gain espéré de **{signe}{esp} pts**{etoile}")

    return commentaires
