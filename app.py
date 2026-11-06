import os
import json
import time
import uuid
from flask import Flask, render_template, jsonify, request, session
from regles import REGLES_STANDARD
from moteur import distribuer, cartes_jouables, gagnant_pli, points, equipe_belote, decompte
from jouer import BotIA, trier_main
from bot_mc_ia import BotMCIA
from bot_mc_ia_v5 import BotMCIAv5
from bot_coop import BotCoop
from professeur import evaluer_decision_carte, analyser_encheres_humain

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "coinche-cle-secrete-production-2026")


# Grand Maître utilise notre champion officiel : BotMCIAv5 (Hybride P1-3 IA, P4-8 MC 40s)
class BotGrandMaitre(BotMCIAv5):
    nom = "Grand Maître (v5 Hybride)"


def obtenir_bots(niveau):
    if niveau == "normal":
        return [None, BotIA(), BotIA(), BotIA()]
    # Niveau par défaut : notre champion officiel Grand Maître v5
    return [None, BotGrandMaitre(), BotGrandMaitre(), BotGrandMaitre()]


# --- GESTIONNAIRE DE SESSIONS ISOLÉES PAR JOUEUR ---
SESSIONS_UTILISATEURS = {}


def creer_partie_vierge():
    return {
        "scores": [0, 0],
        "donneur": 0,
        "etat": "annonces",      # "annonces", "jeu", "pli_termine", "debrief"
        "mains": [[], [], [], []],
        "main_initiale_humain": [],
        "mains_initiales_toutes": [[], [], [], []],
        "contrat": None,
        "encheres": [],
        "tour": 1,
        "pli_en_cours": [],
        "historique": [],
        "plis_faits": [0, 0],
        "pts_cartes": [0, 0],
        "belote_equipe": None,
        "joueur_belote": None,
        "belote_etape": 0,
        "match_termine": False,
        "bilan_match": None,
        "stats_match": {
            "donnes_jouees": 0,
            "contrats_pris": [0, 0],
            "contrats_reussis": [0, 0],
            "coinches_reussies": 0,
            "total_coups_humain": 0,
            "coups_parfaits_humain": 0.0,
            "erreurs_humain": 0,
            "total_encheres_humain": 0,
            "bonnes_encheres_humain": 0
        },
        "bilan_donne": None,
        "debrief_carte": [],
        "debrief_encheres": [],
        "dernier_pli": None,
        "message": "",
        "bulles": ["", "", "", ""],
        "info_pli_termine": None
    }


def obtenir_session():
    """Récupère la session du joueur connecté ou lui en initialise une nouvelle."""
    if "sid" not in session:
        session["sid"] = uuid.uuid4().hex
    sid = session["sid"]
    maintenant = time.time()

    # Nettoyage automatique des sessions inactives (> 2h) pour libérer la RAM Render
    if len(SESSIONS_UTILISATEURS) > 40:
        expires = [s for s, d in SESSIONS_UTILISATEURS.items() if maintenant - d["ts"] > 7200]
        for s in expires:
            del SESSIONS_UTILISATEURS[s]

    if sid not in SESSIONS_UTILISATEURS:
        p = creer_partie_vierge()
        b = obtenir_bots("expert")
        SESSIONS_UTILISATEURS[sid] = {"partie": p, "bots": b, "niveau": "expert", "ts": maintenant}
    else:
        SESSIONS_UTILISATEURS[sid]["ts"] = maintenant

    data = SESSIONS_UTILISATEURS[sid]
    return data["partie"], data["bots"], data


def nom_joueur(j):
    return ["Vous (Sud)", "Ouest", "Partenaire (Nord)", "Est"][j]


def joueur_avec_belote(mains, atout):
    for j in range(4):
        if ("R", atout) in mains[j] and ("D", atout) in mains[j]:
            return j
    return None


def demarrer_nouvelle_donne(partie):
    mains = distribuer()
    partie["mains"] = mains
    partie["main_initiale_humain"] = list(mains[0])
    partie["mains_initiales_toutes"] = [list(m) for m in mains]
    partie["contrat"] = None
    partie["encheres"] = []
    partie["pli_en_cours"] = []
    partie["historique"] = []
    partie["plis_faits"] = [0, 0]
    partie["pts_cartes"] = [0, 0]
    partie["belote_equipe"] = None
    partie["joueur_belote"] = None
    partie["belote_etape"] = 0
    partie["bilan_donne"] = None
    partie["debrief_carte"] = []
    partie["debrief_encheres"] = []
    partie["dernier_pli"] = None
    partie["bulles"] = ["", "", "", ""]
    partie["info_pli_termine"] = None
    partie["etat"] = "annonces"
    partie["tour"] = (partie["donneur"] + 1) % 4
    qui_commence = "À VOUS d'ouvrir les enchères !" if partie["tour"] == 0 else f"À {nom_joueur(partie['tour'])} de parler."
    partie["message"] = f"Nouvelle donne. Donneur : {nom_joueur(partie['donneur'])}. {qui_commence}"


def executer_un_coup_bot_enchere(partie, bots):
    regles = REGLES_STANDARD
    j = partie["tour"]
    bot = bots[j]
    bot.encheres = partie["encheres"]
    dec = bot.annoncer(partie["mains"][j], j, partie["contrat"], regles)
    traiter_decision_enchere(partie, bots, j, dec)


def traiter_decision_enchere(partie, bots, joueur, dec):
    regles = REGLES_STANDARD
    if dec == "coinche" and partie["contrat"] and partie["contrat"]["joueur"] % 2 != joueur % 2:
        partie["contrat"]["coinche"] = 1
        partie["encheres"].append((joueur, "coinche"))
        partie["bulles"][joueur] = "🔥 COINCHE !"
        partie["message"] = f"{nom_joueur(joueur)} COINCHE le contrat !"
        terminer_encheres(partie)
        return

    if dec == "surcoinche" and partie["contrat"] and partie["contrat"].get("coinche", 0) == 1 and partie["contrat"]["joueur"] % 2 == joueur % 2:
        partie["contrat"]["coinche"] = 2
        partie["encheres"].append((joueur, "surcoinche"))
        partie["bulles"][joueur] = "💣 SURCOINCHE !"
        partie["message"] = f"{nom_joueur(joueur)} SURCOINCHE le contrat !"
        terminer_encheres(partie)
        return

    if isinstance(dec, tuple):
        val, coul = dec
        capot = regles["capot_autorise"] and val == regles["valeur_capot"]
        declarant = joueur
        for j_prec, d_prec in partie["encheres"]:
            if isinstance(d_prec, tuple) and d_prec[1] == coul and (j_prec % 2 == joueur % 2):
                declarant = j_prec
                break

        partie["contrat"] = {"valeur": val, "atout": coul, "joueur": declarant, "dernier_encherisseur": joueur, "coinche": 0, "capot": capot}
        partie["encheres"].append((joueur, dec))
        partie["bulles"][joueur] = f"{'CAPOT' if capot else val} {coul}"
        partie["message"] = f"{nom_joueur(joueur)} annonce {'CAPOT' if capot else val} {coul}."
    else:
        partie["encheres"].append((joueur, "passe"))
        partie["bulles"][joueur] = "Passe"
        partie["message"] = f"{nom_joueur(joueur)} passe."

    passes = 0
    for _, d in reversed(partie["encheres"]):
        if d == "passe": passes += 1
        else: break

    if partie["contrat"] is None and len(partie["encheres"]) == 4:
        partie["message"] = "4 passes générales. On redistribue..."
        partie["donneur"] = (partie["donneur"] + 1) % 4
        demarrer_nouvelle_donne(partie)
        return

    if partie["contrat"] is not None and passes == 3:
        terminer_encheres(partie)
        return

    partie["tour"] = (joueur + 1) % 4


def terminer_encheres(partie):
    partie["etat"] = "jeu"
    atout = partie["contrat"]["atout"]
    partie["belote_equipe"] = equipe_belote(partie["mains"], atout)
    partie["joueur_belote"] = joueur_avec_belote(partie["mains"], atout)
    partie["belote_etape"] = 0
    for k in range(4):
        if "COINCHE" not in partie["bulles"][k]:
            partie["bulles"][k] = ""

    partie["tour"] = (partie["donneur"] + 1) % 4
    c_nom = "CAPOT" if partie["contrat"]["capot"] else partie["contrat"]["valeur"]
    coinche_txt = " (COINCHÉ)" if partie["contrat"]["coinche"] else ""
    partie["message"] = f"Contrat : {c_nom} {atout}{coinche_txt} par {nom_joueur(partie['contrat']['joueur'])}. À {nom_joueur(partie['tour'])} d'entamer !"


def verifier_belote_pose(partie, joueur, carte):
    if not partie["contrat"]: return
    atout = partie["contrat"]["atout"]
    if joueur == partie["joueur_belote"] and carte in [("R", atout), ("D", atout)]:
        if partie["belote_etape"] == 0:
            partie["belote_etape"] = 1
            partie["bulles"][joueur] = "🔔 Belote !"
        elif partie["belote_etape"] == 1:
            partie["belote_etape"] = 2
            partie["bulles"][joueur] = "🔔 Rebelote !"


def executer_un_coup_bot_carte(partie, bots):
    regles = REGLES_STANDARD
    j = partie["tour"]
    bot = bots[j]
    bot.historique = partie["historique"]
    bot.encheres = partie["encheres"]
    atout = partie["contrat"]["atout"]

    jouables = cartes_jouables(partie["mains"][j], partie["pli_en_cours"], atout, j, regles)
    carte = bot.jouer_carte(partie["mains"][j], jouables, partie["pli_en_cours"], partie["contrat"], j, regles)

    verifier_belote_pose(partie, j, carte)
    partie["mains"][j].remove(carte)
    partie["pli_en_cours"].append((j, carte))
    partie["historique"].append((j, carte))
    partie["message"] = f"{nom_joueur(j)} a joué {carte[0]}{carte[1]}."

    if len(partie["pli_en_cours"]) == 4:
        preparer_fin_pli(partie)
    else:
        partie["tour"] = (j + 1) % 4


def preparer_fin_pli(partie):
    regles = REGLES_STANDARD
    atout = partie["contrat"]["atout"]
    pli = partie["pli_en_cours"]
    gagnant, c_gagnante = gagnant_pli(pli, atout)
    eq = gagnant % 2
    pts = sum(points(c, atout) for _, c in pli)
    if len(partie["historique"]) == 32:
        pts += regles["dix_de_der"]

    partie["pts_cartes"][eq] += pts
    partie["plis_faits"][eq] += 1
    partie["etat"] = "pli_termine"
    partie["info_pli_termine"] = {
        "gagnant": gagnant,
        "nom_gagnant": nom_joueur(gagnant),
        "carte": f"{c_gagnante[0]}{c_gagnante[1]}",
        "pts": pts
    }
    partie["message"] = f"👉 Pli remporté par {nom_joueur(gagnant)} ({c_gagnante[0]}{c_gagnante[1]}) : +{pts} pts !"


def ramasser_pli_et_continuer(partie, session_data):
    gagnant = partie["info_pli_termine"]["gagnant"]
    partie["dernier_pli"] = list(partie["pli_en_cours"])
    partie["pli_en_cours"] = []
    partie["info_pli_termine"] = None

    if len(partie["historique"]) == 32:
        cloturer_donne(partie, session_data)
    else:
        partie["etat"] = "jeu"
        partie["tour"] = gagnant
        partie["message"] = f"À {nom_joueur(gagnant)} d'entamer le pli suivant."


def cloturer_donne(partie, session_data):
    regles = REGLES_STANDARD
    marque, reussi = decompte(partie["contrat"], partie["pts_cartes"], partie["plis_faits"], partie["belote_equipe"], regles)
    partie["scores"][0] += marque[0]
    partie["scores"][1] += marque[1]
    partie["etat"] = "debrief"

    sm = partie.setdefault("stats_match", {
        "donnes_jouees": 0, "contrats_pris": [0, 0], "contrats_reussis": [0, 0],
        "coinches_reussies": 0, "total_coups_humain": 0, "coups_parfaits_humain": 0.0,
        "erreurs_humain": 0, "total_encheres_humain": 0, "bonnes_encheres_humain": 0,
        "chance_distribution_total": 0, "bad_beats": 0, "coups_de_chance": 0
    })

    sm["donnes_jouees"] += 1
    camp_preneur = partie["contrat"]["joueur"] % 2
    sm["contrats_pris"][camp_preneur] += 1
    if reussi:
        sm["contrats_reussis"][camp_preneur] += 1
    if partie["contrat"].get("coinche", 0) > 0 and not reussi:
        sm["coinches_reussies"] += 1

    c_str = "CAPOT" if partie["contrat"].get("capot") else partie["contrat"]["valeur"]
    partie["bilan_donne"] = {
        "pts_nous": partie["pts_cartes"][0],
        "pts_eux": partie["pts_cartes"][1],
        "plis_nous": partie["plis_faits"][0],
        "plis_eux": partie["plis_faits"][1],
        "belote": "Votre équipe (+20)" if partie["belote_equipe"] == 0 else ("Équipe adverse (+20)" if partie["belote_equipe"] == 1 else "Aucune"),
        "reussi": reussi,
        "marque_nous": marque[0],
        "marque_eux": marque[1],
        "preneur": nom_joueur(partie["contrat"]["joueur"]),
        "contrat_nom": f"{c_str} {partie['contrat']['atout']}"
    }

    statut = "RÉUSSI" if reussi else "CHUTÉ"
    partie["message"] = f"Donne terminée ! Contrat {c_str} {partie['contrat']['atout']} {statut}. Points : {partie['pts_cartes'][0]} à {partie['pts_cartes'][1]}."

    # Analyse du Professeur sécurisée
    try:
        partie["debrief_encheres"] = analyser_encheres_humain(partie["main_initiale_humain"], partie["encheres"], 0)
    except Exception as e:
        print(f"Avertissement analyse enchères: {e}")
        partie["debrief_encheres"] = ["Analyse des enchères indisponible pour cette donne."]

    # Enregistrement automatique JSONL de la donne
    try:
        donne_rec = {
            "donneur": partie["donneur"],
            "niveau_bot": session_data.get("niveau", "coop"),
            "contrat": partie["contrat"],
            "encheres": partie["encheres"],
            "mains_depart": [[f"{r}{c}" for r, c in m] for m in partie["mains_initiales_toutes"]],
            "historique": [[j, f"{r}{c}"] for j, (r, c) in partie["historique"]],
            "bilan": partie["bilan_donne"],
            "scores": list(partie["scores"])
        }
        with open("parties_humain.jsonl", "a", encoding="utf-8") as f_jsonl:
            f_jsonl.write(json.dumps(donne_rec, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"Avertissement sauvegarde JSONL: {e}")

    # Calcul de chance
    try:
        from moteur import POINTS_ATOUT, POINTS_NON_ATOUT
        atout = partie["contrat"]["atout"]
        pts_bruts_nous = sum(POINTS_ATOUT[r] if c == atout else POINTS_NON_ATOUT[r]
                             for p in (0, 2) for r, c in partie["mains_initiales_toutes"][p])
        ratio_donne = pts_bruts_nous / 152.0
        sm["chance_distribution_total"] = sm.get("chance_distribution_total", 0.0) + ratio_donne
        if camp_preneur == 0 and not reussi and partie["contrat"]["valeur"] <= 100:
            sm["bad_beats"] = sm.get("bad_beats", 0) + 1
    except Exception as e:
        print(f"Avertissement calcul chance: {e}")

    # Vérification fin de match (1 000 points)
    obj = regles["score_objectif"]
    if max(partie["scores"]) >= obj and partie["scores"][0] != partie["scores"][1]:
        partie["match_termine"] = True
        victoire = (partie["scores"][0] > partie["scores"][1])
        prec_carte = round(100.0 * sm.get("coups_parfaits_humain", 0.0) / max(1, sm.get("total_coups_humain", 0)), 1)
        prec_globale = prec_carte

        if prec_globale >= 85:
            mention = "🌟 Grand Maître"
        elif prec_globale >= 70:
            mention = "🎓 Expert"
        elif prec_globale >= 55:
            mention = "👍 Solide"
        else:
            mention = "📚 En apprentissage"

        chance_distrib = round(100 * sm.get("chance_distribution_total", 0.0) / max(1, sm["donnes_jouees"]), 1)
        avis_chance = "🍀 Chanceux" if chance_distrib >= 53 else ("😾 Malchanceux" if chance_distrib <= 47 else "⚖️ Équilibré")

        partie["bilan_match"] = {
            "victoire": victoire,
            "score_nous": partie["scores"][0],
            "score_eux": partie["scores"][1],
            "donnes": sm["donnes_jouees"],
            "precision_carte": f"{prec_carte} %",
            "precision_encheres": "-- (en calibration)",
            "mention": mention,
            "erreurs": sm["erreurs_humain"],
            "contrats_nous": f"{sm['contrats_reussis'][0]}/{sm['contrats_pris'][0]} réussis",
            "contrats_eux": f"{sm['contrats_reussis'][1]}/{sm['contrats_pris'][1]} réussis",
            "chance_distrib": f"{chance_distrib} %",
            "avis_chance": avis_chance,
            "bad_beats": sm.get("bad_beats", 0)
        }


# --- ROUTES HTTP FLASK (BRANCHÉES SUR LA SESSION COURANTE) ---

@app.route("/")
def index():
    partie, bots, data = obtenir_session()
    return render_template("index.html")


@app.route("/api/etat")
def get_etat():
    partie, bots, data = obtenir_session()
    regles = REGLES_STANDARD
    atout = partie["contrat"]["atout"] if partie["contrat"] else "♠"
    jouables = []
    if partie["etat"] == "jeu" and partie["tour"] == 0 and len(partie["pli_en_cours"]) < 4:
        jouables = cartes_jouables(partie["mains"][0], partie["pli_en_cours"], atout, 0, regles)

    h_plis = []
    for p_idx in range(len(partie["historique"]) // 4):
        pli_k = partie["historique"][4*p_idx : 4*p_idx+4]
        gagnant, c_gag = gagnant_pli(pli_k, atout)
        h_plis.append({
            "num": p_idx + 1,
            "cartes": [(nom_joueur(j), f"{c[0]}{c[1]}") for j, c in pli_k],
            "gagnant": nom_joueur(gagnant),
            "carte_gagnante": f"{c_gag[0]}{c_gag[1]}"
        })

    # Atout pris en compte pour le tri seulement PENDANT le jeu, ordre neutre pendant les annonces
    atout_tri = partie["contrat"]["atout"] if (partie["contrat"] and partie["etat"] != "annonces") else None
    return jsonify({
        "etat": partie["etat"],
        "donneur": partie["donneur"],
        "scores": partie["scores"],
        "main_humain": trier_main(partie["mains"][0], atout_tri),
        "main_brute_tirage": list(partie["main_initiale_humain"]),
        "mains_depart_toutes": [[f"{r}{c}" for r, c in trier_main(m)] for m in partie["mains_initiales_toutes"]],
        "jouables": jouables,
        "tour": partie["tour"],
        "nom_tour": nom_joueur(partie["tour"]),
        "contrat": partie["contrat"],
        "encheres": [(nom_joueur(j), d if isinstance(d, str) else f"{d[0]} {d[1]}") for j, d in partie["encheres"]],
        "pli_en_cours": [(nom_joueur(j), f"{c[0]}{c[1]}") for j, c in partie["pli_en_cours"]],
        "historique_plis": h_plis,
        "message": partie["message"],
        "bulles": partie["bulles"],
        "info_pli_termine": partie["info_pli_termine"],
        "nb_cartes_joueurs": [len(partie["mains"][j]) for j in range(4)],
        "dernier_pli_info": ({
            "cartes": [(nom_joueur(j), f"{c[0]}{c[1]}") for j, c in partie["dernier_pli"]],
            "gagnant": nom_joueur(gagnant_pli(partie["dernier_pli"], partie["contrat"]["atout"])[0]) if partie["contrat"] else "",
            "carte_gagnante": f"{gagnant_pli(partie['dernier_pli'], partie['contrat']['atout'])[1][0]}{gagnant_pli(partie['dernier_pli'], partie['contrat']['atout'])[1][1]}" if partie["contrat"] else ""
        } if partie.get("dernier_pli") and len(partie["dernier_pli"]) == 4 else None),
        "bilan_donne": partie["bilan_donne"],
        "debrief_carte": partie["debrief_carte"],
        "debrief_encheres": partie["debrief_encheres"],
        "match_termine": partie["match_termine"],
        "bilan_match": partie["bilan_match"],
    })


@app.route("/api/step_bot", methods=["POST"])
def step_bot():
    partie, bots, data = obtenir_session()
    if partie["etat"] == "annonces" and partie["tour"] != 0:
        executer_un_coup_bot_enchere(partie, bots)
    elif partie["etat"] == "jeu" and partie["tour"] != 0 and len(partie["pli_en_cours"]) < 4:
        executer_un_coup_bot_carte(partie, bots)
    elif partie["etat"] == "pli_termine":
        ramasser_pli_et_continuer(partie, data)
    return jsonify({"succes": True})


@app.route("/api/action_enchere", methods=["POST"])
def action_enchere():
    partie, bots, data = obtenir_session()
    if partie["etat"] != "annonces" or partie["tour"] != 0:
        return jsonify({"erreur": "Ce n'est pas votre tour"}), 400

    payload = request.json or {}
    choix = payload.get("choix")

    if isinstance(choix, list):
        val = int(choix[0])
        if partie["contrat"] and val <= partie["contrat"]["valeur"]:
            return jsonify({"erreur": "Enchère insuffisante"}), 400
        choix = (val, choix[1])

    traiter_decision_enchere(partie, bots, 0, choix)
    return jsonify({"succes": True})


@app.route("/api/jouer_carte", methods=["POST"])
def route_jouer_carte():
    partie, bots, data = obtenir_session()
    if partie["etat"] != "jeu" or partie["tour"] != 0:
        return jsonify({"erreur": "Ce n'est pas votre tour"}), 400

    payload = request.json or {}
    carte = (payload["rang"], payload["couleur"])
    regles = REGLES_STANDARD
    atout = partie["contrat"]["atout"]
    jouables = cartes_jouables(partie["mains"][0], partie["pli_en_cours"], atout, 0, regles)

    if carte not in jouables:
        return jsonify({"erreur": "Carte interdite"}), 400

    verifier_belote_pose(partie, 0, carte)

    analyse = evaluer_decision_carte(
        partie["mains"][0], jouables, partie["pli_en_cours"], partie["contrat"],
        0, carte, partie["historique"], partie["encheres"], regles
    )
    if analyse:
        partie["debrief_carte"].append(analyse)
        if not analyse.get("est_force"):
            sm = partie.setdefault("stats_match", {})
            sm["total_coups_humain"] = sm.get("total_coups_humain", 0) + 1
            lbl = analyse.get("label", "")
            if lbl == "Meilleur coup":
                sm["coups_parfaits_humain"] = sm.get("coups_parfaits_humain", 0.0) + 1.0
            elif lbl == "Solide":
                sm["coups_parfaits_humain"] = sm.get("coups_parfaits_humain", 0.0) + 0.8
            elif lbl == "Imprécision":
                sm["coups_parfaits_humain"] = sm.get("coups_parfaits_humain", 0.0) + 0.4
            elif lbl == "Erreur":
                sm["erreurs_humain"] = sm.get("erreurs_humain", 0) + 1

    partie["mains"][0].remove(carte)
    partie["pli_en_cours"].append((0, carte))
    partie["historique"].append((0, carte))
    partie["message"] = f"Vous avez joué {carte[0]}{carte[1]}."

    if len(partie["pli_en_cours"]) == 4:
        preparer_fin_pli(partie)
    else:
        partie["tour"] = 1
    return jsonify({"succes": True})


@app.route("/api/changer_niveau_ia", methods=["POST"])
def route_changer_niveau_ia():
    partie, bots, data = obtenir_session()
    niveau = (request.json or {}).get("niveau", "coop")
    if niveau not in ("normal", "expert"):
        return jsonify({"erreur": f"Niveau inconnu : {niveau}"}), 400

    data["bots"] = obtenir_bots(niveau)
    data["niveau"] = niveau
    print(f"Session {session.get('sid', '')[:8]} -> Niveau : {niveau}")
    return jsonify({"succes": True, "niveau": niveau})


@app.route("/api/nouvelle_donne", methods=["POST"])
def route_nouvelle_donne():
    partie, bots, data = obtenir_session()
    partie["donneur"] = (partie["donneur"] + 1) % 4
    demarrer_nouvelle_donne(partie)
    return jsonify({"succes": True})


@app.route("/api/export_donne")
def route_export_donne():
    partie, bots, data = obtenir_session()
    if not partie["mains_initiales_toutes"][0]:
        return jsonify({"texte": "Aucune donne enregistrée."})

    lignes = [
        "=" * 60,
        "RAPPORT D'ANALYSE DE DONNE — COINCHE IA",
        "=" * 60
    ]

    noms_niveaux = {
        "normal": "IA Classique (BotIA)",
        "expert": "Grand Maître (v5 Hybride 40s)",
        "coop": "Bot-Coop"
    }
    lignes.append(f"\nNiveau des bots : {noms_niveaux.get(data.get('niveau', 'coop'))}")
    lignes.append(f"Donneur : {nom_joueur(partie['donneur'])}")
    if partie["contrat"]:
        c = partie["contrat"]
        coinche_str = ["Non coinché", "COINCHÉ (x2)", "SURCOINCHÉ (x3)"][c.get("coinche", 0)]
        nom_c = "CAPOT" if c.get("capot") else c["valeur"]
        lignes.append(f"Contrat final : {nom_c} {c['atout']} par {nom_joueur(c['joueur'])} — {coinche_str}")
    else:
        lignes.append("Contrat final : Aucun (passe générale)")

    lignes.append("\n--- DÉROULEMENT DES ENCHÈRES ---")
    for j, d in partie["encheres"]:
        nom_j = nom_joueur(j)
        action = f"{d[0]} {d[1]}" if isinstance(d, tuple) else str(d).upper()
        lignes.append(f"  {nom_j:18} : {action}")

    lignes.append("\n--- MAINS DE DÉPART (cartes triées) ---")
    for p in range(4):
        cartes_str = " ".join(f"{r}{c}" for r, c in trier_main(partie["mains_initiales_toutes"][p]))
        lignes.append(f"  {nom_joueur(p):18} : {cartes_str}")

    if partie["historique"]:
        lignes.append("\n--- DÉROULEMENT DU JEU DE LA CARTE ---")
        atout = partie["contrat"]["atout"] if partie["contrat"] else "♠"
        regles = REGLES_STANDARD
        for num_pli in range(1, 9):
            idx_deb = (num_pli - 1) * 4
            idx_fin = num_pli * 4
            if idx_deb >= len(partie["historique"]): break
            cartes_pli = partie["historique"][idx_deb:idx_fin]
            detail_pli = "  ".join(f"{nom_joueur(j)}:{r}{c}" for j, (r, c) in cartes_pli)
            if len(cartes_pli) == 4:
                gagnant, c_gagnante = gagnant_pli(cartes_pli, atout)
                pts = sum(points(c, atout) for _, c in cartes_pli)
                if num_pli == 8: pts += regles["dix_de_der"]
                lignes.append(f"  Pli {num_pli} : {detail_pli}")
                lignes.append(f"         ==> Remporté par {nom_joueur(gagnant)} avec {c_gagnante[0]}{c_gagnante[1]} (+{pts} pts)")

    b = partie["bilan_donne"]
    if b:
        lignes.append("\n--- BILAN DE LA DONNE ---")
        lignes.append(f"  Points cartes : Vous {b['pts_nous']} — {b['pts_eux']} Eux")
        lignes.append(f"  Plis faits    : Vous {b['plis_nous']} — {b['plis_eux']} Eux")
        lignes.append(f"  Belote        : {b['belote']}")
        statut = "RÉUSSI" if b["reussi"] else "CHUTÉ"
        lignes.append(f"  Résultat      : {b['contrat_nom']} est {statut}")
        lignes.append(f"  Marque donne  : Vous +{b['marque_nous']} | Eux +{b['marque_eux']}")
        lignes.append(f"  SCORE TOTAL   : Vous {partie['scores'][0]} — {partie['scores'][1]} Eux")

    if partie["debrief_encheres"]:
        lignes.append("\n--- ANALYSE PROFESSEUR : ENCHÈRES ---")
        for txt in partie["debrief_encheres"]:
            lignes.append(f"  {txt}")

    if partie["debrief_carte"]:
        lignes.append("\n--- ANALYSE PROFESSEUR : JEU DE LA CARTE ---")
        for item in partie["debrief_carte"]:
            lignes.append(f"\n  [Pli {item['num_pli']}] Vous avez joué {item['carte_jouee'][0]}{item['carte_jouee'][1]} — Note : {item['label']}")
            lignes.append(f"    Message : {item['message']}")
            lignes.append(f"    Tactique : {item['explication']}")
            if not item.get("est_force") and item.get("options"):
                opts_str = " | ".join(f"{o['carte']}: {o.get('proba', o.get('note', ''))}" for o in item['options'])
                lignes.append(f"    Options évaluées : {opts_str}")

    lignes.append("\n" + "=" * 60)
    return jsonify({"texte": "\n".join(lignes)})


@app.route("/test_cartes")
def test_cartes():
    return render_template("test_cartes.html")


@app.route("/api/rejouer_match", methods=["POST"])
def route_rejouer_match():
    partie, bots, data = obtenir_session()
    partie["scores"] = [0, 0]
    partie["donneur"] = 0
    partie["match_termine"] = False
    partie["bilan_match"] = None
    partie["stats_match"] = {
        "donnes_jouees": 0,
        "contrats_pris": [0, 0],
        "contrats_reussis": [0, 0],
        "coinches_reussies": 0,
        "total_coups_humain": 0,
        "coups_parfaits_humain": 0.0,
        "chance_distribution_total": 0,
        "bad_beats": 0,
        "coups_de_chance": 0,
        "erreurs_humain": 0,
        "total_encheres_humain": 0,
        "bonnes_encheres_humain": 0
    }
    demarrer_nouvelle_donne(partie)
    return jsonify({"succes": True})


port = int(os.environ.get("PORT", 5001))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=port, debug=False)
