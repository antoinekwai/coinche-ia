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
    """Génère un diagnostic clair, uniquement en cas d'erreur tactique avérée."""
    atout = contrat["atout"]
    attaque = (contrat["joueur"] % 2 == joueur % 2)
    partenaire = (joueur + 2) % 4
    est_preneur = (contrat["joueur"] == joueur)
    
    pts_jouee = points(c_jouee, atout)
    pts_top = points(top_c, atout)

    # 1. ERREURS À L'ENTAME (Pli vide)
    if len(pli) == 0:
        if est_preneur and top_c[0] == "V" and top_c[1] == atout and c_jouee[1] != atout:
            return "En tant que preneur, purger les atouts au Valet d'entrée est prioritaire pour désarmer la défense."
        if not attaque and c_jouee[1] == atout and top_c[1] != atout:
            return "En défense, évitez d'entamer atout : cela aide le preneur à purger ses atouts sans effort."
        if top_c[0] == "A" and top_c[1] != atout and c_jouee[0] != "A":
            return f"Encaisser votre As de {top_c[1]} à l'entame garantit une levée nette avant l'apparition des coupes."

    # 2. ERREURS EN COURS DE PLI
    else:
        maitre_actuel, carte_maitresse = gagnant_pli(pli, atout)
        partenaire_maitre = (maitre_actuel == partenaire)
        adversaire_maitre = not partenaire_maitre

        # A. Partenaire maître
        if partenaire_maitre:
            # Dépenser un atout sur le maître du partenaire
            if c_jouee[1] == atout and top_c[1] != atout:
                return f"Votre partenaire gagne déjà le pli avec {carte_maitresse[0]}{carte_maitresse[1]} : économisez vos atouts, défaussez {top_c[0]}{top_c[1]}."
            # Oubli de charger en défense en 4e position
            if len(pli) == 3 and not attaque and top_c[0] == "10" and c_jouee[0] != "10":
                return "En défense, le pli de votre partenaire est garanti en dernier : chargez votre 10 pour empocher des points décisifs."

        # B. Adversaire maître
        if adversaire_maitre:
            pli_virtuel = list(pli) + [(joueur, top_c)]
            top_gagne = (gagnant_pli(pli_virtuel, atout)[0] == joueur)
            
           
            # Possibilité de couper ou remporter le pli manquée (uniquement si vous ne gagnez PAS déjà le pli !)
            carte_jouee_gagne = (gagnant_pli(pli + [(joueur, c_jouee)], atout)[0] == joueur)
            if top_gagne and not carte_jouee_gagne:
                return f"Vous pouviez remporter le pli avec {top_c[0]}{top_c[1]} pour couper l'offensive adverse."

            # Cadeau de points sur un pli perdu certain (en 4e position)
            if len(pli) == 3 and pts_jouee >= 10 and pts_top < pts_jouee:
                return f"Le pli est définitivement perdu au profit de l'adversaire : ne lui donnez pas {c_jouee[0]}{c_jouee[1]} ({pts_jouee} pts), sacrifiez une petite carte."

    # Si aucune faute de doctrine n'est isolée : neutralité et humilité
    return f"Vos cartes étaient d'une valeur très proche compte tenu des incertitudes de la donne. L'alternative {top_c[0]}{top_c[1]} obtient un léger avantage statistique sur les simulations."

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
    # SEUILS DE TOLÉRANCE RÉALISTES
    if carte_jouee == top_carte or ecart_proba <= 0.05:
        apprec = ("Meilleur coup", "green", "🌟 Excellent choix")
    elif sont_equiv:
        apprec = ("Meilleur coup", "green", f"🌟 Excellent choix (équivalent à {top_carte[0]}{top_carte[1]})")
        explication = f"Vous possédez les cartes maîtresses consécutives ({carte_jouee[0]} et {top_carte[0]} de {carte_jouee[1]}). Jouer l'une ou l'autre est parfaitement équivalent."
    elif ecart_proba <= 0.15:
        apprec = ("Solide", "blue", "👍 Coup solide")
    elif ecart_proba <= 0.28:
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
import random
from dispute import coherent
from moteur import decompte, equipe_belote, RANGS
def simuler_esperance_tour(main_depart, encheres_jusqu_ici, action_choisie, joueur_humain=0, nb_simuls=30):
    """Calcule par Monte Carlo l'espérance des options à un tour précis des enchères."""
    from regles import REGLES_STANDARD
    regles = REGLES_STANDARD
    
    # Contrat en cours avant que l'humain ne parle à ce tour
    dernier_contrat = None
    for j, d in encheres_jusqu_ici:
        if isinstance(d, tuple):
            dernier_contrat = (j, d[0], d[1])

    # Options à tester
    options_a_tester = ["passe"]
    est_adverse = False
    
    if dernier_contrat:
        preneur_actuel, val_actuelle, coul_actuelle = dernier_contrat
        est_adverse = (preneur_actuel % 2 != joueur_humain % 2)
        if est_adverse:
            options_a_tester.append("coinche")
        palier_suivant = val_actuelle + 10
        if palier_suivant <= 160:
            coul_pref = max(COULEURS, key=lambda c: sum(1 for x in main_depart if x[1] == c))
            options_a_tester.append((palier_suivant, coul_pref))
            if coul_actuelle != coul_pref and (palier_suivant, coul_actuelle) not in options_a_tester:
                options_a_tester.append((palier_suivant, coul_actuelle))
    else:
        # En ouverture : tester Passe et la meilleure couleur au niveau 80, 90, 100
        coul_pref = max(COULEURS, key=lambda c: sum(1 for x in main_depart if x[1] == c))
        for v in (80, 90, 100):
            options_a_tester.append((v, coul_pref))

    # Ajouter l'action réellement choisie si pas déjà dedans
    if action_choisie not in options_a_tester:
        options_a_tester.append(action_choisie)

    autres = [p for p in range(4) if p != joueur_humain]
    inconnues = [(r, c) for c in COULEURS for r in RANGS if (r, c) not in main_depart]
    
    donnes_valides = []
    for _ in range(2000):
        random.shuffle(inconnues)
        m = [None] * 4
        m[joueur_humain] = list(main_depart)
        for k, p in enumerate(autres):
            m[p] = inconnues[8*k : 8*k+8]
        if all(coherent(m[p], p, encheres_jusqu_ici) for p in autres):
            donnes_valides.append(m)
            if len(donnes_valides) == nb_simuls:
                break

    if len(donnes_valides) < 8:
        return None

    from dispute import JoueurDispute
    bot_simul = JoueurDispute()
    bot_simul.encheres = list(encheres_jusqu_ici)
    eq_humain = joueur_humain % 2
    bilan = {}

    for opt in options_a_tester:
        if opt == "passe":
            if dernier_contrat is None:
                bilan["Passe"] = 0.0
                continue
            c = {"valeur": val_actuelle, "atout": coul_actuelle, "joueur": preneur_actuel, "coinche": 0, "capot": False}
            lbl = f"Passe ({val_actuelle} {coul_actuelle})"
        elif opt == "coinche":
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
        for m in donnes_valides:
            pts, plis, bel = bot_simul.jouer(m, c, regles)
            s, _ = decompte(c, pts, plis, bel, regles)
            gains.append(s[eq_humain] - s[1 - eq_humain])
        bilan[lbl] = round(float(np.mean(gains)), 1)

    return bilan


def analyser_encheres_humain(main_depart, encheres_partie, joueur_humain=0):
    commentaires = []
    partenaire = (joueur_humain + 2) % 4
    
    actions_humain = [(idx, d) for idx, (j, d) in enumerate(encheres_partie) if j == joueur_humain]
    if not actions_humain:
        return ["ℹ️ Aucune action enregistrée."]

    for tour_num, (idx_action, action) in enumerate(actions_humain, 1):
        encheres_avant = encheres_partie[:idx_action]
        action_nom = f"{action[0]} {action[1]}" if isinstance(action, tuple) else str(action).upper()
        
        commentaires.append(f"📍 **Tour {tour_num} : Vous avez choisi [{action_nom}]**")
        
        # Simulation MC à ce tour précis
        bilan_tour = simuler_esperance_tour(main_depart, encheres_avant, action, joueur_humain)
        if bilan_tour:
            meilleure = max(bilan_tour, key=bilan_tour.get)
            for opt, esp in bilan_tour.items():
                etoile = " 🌟 (Optimal)" if opt == meilleure else ""
                signe = "+" if esp > 0 else ""
                commentaires.append(f"  • {opt} : **{signe}{esp} pts**{etoile}")
        else:
            commentaires.append("  • (Situation standard évaluée selon la règle v2)")

        if tour_num < len(actions_humain):
            commentaires.append("---")

    return commentaires
