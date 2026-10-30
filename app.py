import os
from flask import Flask, render_template, jsonify, request
from regles import REGLES_STANDARD
from moteur import distribuer, cartes_jouables, gagnant_pli, points, equipe_belote, decompte
from jouer import BotIA, trier_main
from professeur import evaluer_decision_carte, analyser_encheres_humain

app = Flask(__name__)

PARTIE = {
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
    "bilan_donne": None,
    "debrief_carte": [],
    "debrief_encheres": [],
    "dernier_pli": None,
    "message": "",
    "bulles": ["", "", "", ""],
    "info_pli_termine": None
}

BOTS = [None, BotIA(), BotIA(), BotIA()]

def nom_joueur(j):
    return ["Vous (Sud)", "Ouest", "Partenaire (Nord)", "Est"][j]

def demarrer_nouvelle_donne():
    mains = distribuer()
    PARTIE["mains"] = mains
    PARTIE["main_initiale_humain"] = list(mains[0])
    PARTIE["mains_initiales_toutes"] = [list(m) for m in mains]
    PARTIE["contrat"] = None
    PARTIE["encheres"] = []
    PARTIE["pli_en_cours"] = []
    PARTIE["historique"] = []
    PARTIE["plis_faits"] = [0, 0]
    PARTIE["pts_cartes"] = [0, 0]
    PARTIE["belote_equipe"] = None
    PARTIE["bilan_donne"] = None
    PARTIE["debrief_carte"] = []
    PARTIE["debrief_encheres"] = []
    PARTIE["dernier_pli"] = None
    PARTIE["bulles"] = ["", "", "", ""]
    PARTIE["info_pli_termine"] = None
    PARTIE["etat"] = "annonces"
    PARTIE["tour"] = (PARTIE["donneur"] + 1) % 4
    PARTIE["message"] = f"Nouvelle donne. Donneur : {nom_joueur(PARTIE['donneur'])}."

def executer_un_coup_bot_enchere():
    regles = REGLES_STANDARD
    j = PARTIE["tour"]
    bot = BOTS[j]
    bot.encheres = PARTIE["encheres"]
    dec = bot.annoncer(PARTIE["mains"][j], j, PARTIE["contrat"], regles)
    traiter_decision_enchere(j, dec)

def traiter_decision_enchere(joueur, dec):
    regles = REGLES_STANDARD
    if dec == "coinche" and PARTIE["contrat"] and PARTIE["contrat"]["joueur"] % 2 != joueur % 2:
        PARTIE["contrat"]["coinche"] = 1
        PARTIE["encheres"].append((joueur, "coinche"))
        PARTIE["bulles"][joueur] = "🔥 COINCHE !"
        PARTIE["message"] = f"{nom_joueur(joueur)} COINCHE le contrat !"
        terminer_encheres()
        return

    if isinstance(dec, tuple):
        val, coul = dec
        capot = regles["capot_autorise"] and val == regles["valeur_capot"]
        declarant = joueur
        if PARTIE["contrat"] and PARTIE["contrat"]["atout"] == coul:
            if PARTIE["contrat"]["joueur"] % 2 == joueur % 2:
                declarant = PARTIE["contrat"]["joueur"]

        PARTIE["contrat"] = {"valeur": val, "atout": coul, "joueur": declarant, "dernier_encherisseur": joueur, "coinche": 0, "capot": capot}
        PARTIE["encheres"].append((joueur, dec))
        PARTIE["bulles"][joueur] = f"{'CAPOT' if capot else val} {coul}"
        PARTIE["message"] = f"{nom_joueur(joueur)} annonce {val} {coul}."
    else:
        PARTIE["encheres"].append((joueur, "passe"))
        PARTIE["bulles"][joueur] = "Passe"
        PARTIE["message"] = f"{nom_joueur(joueur)} passe."

    passes = 0
    for _, d in reversed(PARTIE["encheres"]):
        if d == "passe": passes += 1
        else: break

    if PARTIE["contrat"] is None and len(PARTIE["encheres"]) == 4:
        PARTIE["message"] = "4 passes générales. On redistribue..."
        PARTIE["donneur"] = (PARTIE["donneur"] + 1) % 4
        demarrer_nouvelle_donne()
        return

    if PARTIE["contrat"] is not None and passes == 3:
        terminer_encheres()
        return

    PARTIE["tour"] = (joueur + 1) % 4

def terminer_encheres():
    PARTIE["etat"] = "jeu"
    atout = PARTIE["contrat"]["atout"]
    PARTIE["belote_equipe"] = equipe_belote(PARTIE["mains"], atout)
    PARTIE["tour"] = (PARTIE["donneur"] + 1) % 4
    c_nom = "CAPOT" if PARTIE["contrat"]["capot"] else PARTIE["contrat"]["valeur"]
    coinche_txt = " (COINCHÉ)" if PARTIE["contrat"]["coinche"] else ""
    PARTIE["message"] = f"Contrat : {c_nom} {atout}{coinche_txt} par {nom_joueur(PARTIE['contrat']['joueur'])}. À {nom_joueur(PARTIE['tour'])} d'entamer !"

def executer_un_coup_bot_carte():
    regles = REGLES_STANDARD
    j = PARTIE["tour"]
    bot = BOTS[j]
    bot.historique = PARTIE["historique"]
    bot.encheres = PARTIE["encheres"]
    atout = PARTIE["contrat"]["atout"]
    
    jouables = cartes_jouables(PARTIE["mains"][j], PARTIE["pli_en_cours"], atout, j, regles)
    carte = bot.jouer_carte(PARTIE["mains"][j], jouables, PARTIE["pli_en_cours"], PARTIE["contrat"], j, regles)
    
    PARTIE["mains"][j].remove(carte)
    PARTIE["pli_en_cours"].append((j, carte))
    PARTIE["historique"].append((j, carte))
    PARTIE["message"] = f"{nom_joueur(j)} a joué {carte[0]}{carte[1]}."

    if len(PARTIE["pli_en_cours"]) == 4:
        preparer_fin_pli()
    else:
        PARTIE["tour"] = (j + 1) % 4

def preparer_fin_pli():
    regles = REGLES_STANDARD
    atout = PARTIE["contrat"]["atout"]
    pli = PARTIE["pli_en_cours"]
    gagnant, c_gagnante = gagnant_pli(pli, atout)
    eq = gagnant % 2
    pts = sum(points(c, atout) for _, c in pli)
    if len(PARTIE["historique"]) == 32:
        pts += regles["dix_de_der"]
    
    PARTIE["pts_cartes"][eq] += pts
    PARTIE["plis_faits"][eq] += 1
    PARTIE["etat"] = "pli_termine"
    PARTIE["info_pli_termine"] = {
        "gagnant": gagnant,
        "nom_gagnant": nom_joueur(gagnant),
        "carte": f"{c_gagnante[0]}{c_gagnante[1]}",
        "pts": pts
    }
    PARTIE["message"] = f"👉 Pli remporté par {nom_joueur(gagnant)} ({c_gagnante[0]}{c_gagnante[1]}) : +{pts} pts !"

def ramasser_pli_et_continuer():
    gagnant = PARTIE["info_pli_termine"]["gagnant"]
    PARTIE["dernier_pli"] = list(PARTIE["pli_en_cours"])
    PARTIE["pli_en_cours"] = []
    PARTIE["info_pli_termine"] = None
    
    if len(PARTIE["historique"]) == 32:
        cloturer_donne()
    else:
        PARTIE["etat"] = "jeu"
        PARTIE["tour"] = gagnant
        PARTIE["message"] = f"À {nom_joueur(gagnant)} d'entamer le pli suivant."

def cloturer_donne():
    regles = REGLES_STANDARD
    marque, reussi = decompte(PARTIE["contrat"], PARTIE["pts_cartes"], PARTIE["plis_faits"], PARTIE["belote_equipe"], regles)
    PARTIE["scores"][0] += marque[0]
    PARTIE["scores"][1] += marque[1]
    PARTIE["etat"] = "debrief"
    
    PARTIE["bilan_donne"] = {
        "pts_nous": PARTIE["pts_cartes"][0],
        "pts_eux": PARTIE["pts_cartes"][1],
        "plis_nous": PARTIE["plis_faits"][0],
        "plis_eux": PARTIE["plis_faits"][1],
        "belote": "Votre équipe (+20)" if PARTIE["belote_equipe"] == 0 else ("Équipe adverse (+20)" if PARTIE["belote_equipe"] == 1 else "Aucune"),
        "reussi": reussi,
        "marque_nous": marque[0],
        "marque_eux": marque[1],
        "preneur": nom_joueur(PARTIE["contrat"]["joueur"]),
        "contrat_nom": f"{PARTIE['contrat']['valeur']} {PARTIE['contrat']['atout']}"
    }

    PARTIE["debrief_encheres"] = analyser_encheres_humain(PARTIE["main_initiale_humain"], PARTIE["encheres"], 0)
    statut = "RÉUSSI" if reussi else "CHUTÉ"
    PARTIE["message"] = f"Donne terminée ! Contrat {PARTIE['contrat']['valeur']} {PARTIE['contrat']['atout']} {statut}. Points cartes : {PARTIE['pts_cartes'][0]} à {PARTIE['pts_cartes'][1]}."

# --- API ---

@app.route("/")
def index():
    if not PARTIE["mains"][0]:
        demarrer_nouvelle_donne()
    return render_template("index.html")

@app.route("/api/etat")
def get_etat():
    regles = REGLES_STANDARD
    atout = PARTIE["contrat"]["atout"] if PARTIE["contrat"] else "♠"
    jouables = []
    if PARTIE["etat"] == "jeu" and PARTIE["tour"] == 0:
        jouables = cartes_jouables(PARTIE["mains"][0], PARTIE["pli_en_cours"], atout, 0, regles)
    
    h_plis = []
    for p_idx in range(len(PARTIE["historique"]) // 4):
        pli_k = PARTIE["historique"][4*p_idx : 4*p_idx+4]
        gagnant, c_gag = gagnant_pli(pli_k, atout)
        h_plis.append({
            "num": p_idx + 1,
            "cartes": [(nom_joueur(j), f"{c[0]}{c[1]}") for j, c in pli_k],
            "gagnant": nom_joueur(gagnant),
            "carte_gagnante": f"{c_gag[0]}{c_gag[1]}"
        })

    return jsonify({
        "etat": PARTIE["etat"],
        "scores": PARTIE["scores"],
        "main_humain": trier_main(PARTIE["mains"][0]),
        "mains_depart_toutes": [[f"{r}{c}" for r, c in trier_main(m)] for m in PARTIE["mains_initiales_toutes"]],
        "jouables": jouables,
        "tour": PARTIE["tour"],
        "nom_tour": nom_joueur(PARTIE["tour"]),
        "contrat": PARTIE["contrat"],
        "encheres": [(nom_joueur(j), d if isinstance(d, str) else f"{d[0]} {d[1]}") for j, d in PARTIE["encheres"]],
        "pli_en_cours": [(nom_joueur(j), f"{c[0]}{c[1]}") for j, c in PARTIE["pli_en_cours"]],
        "historique_plis": h_plis,
        "message": PARTIE["message"],
        "bulles": PARTIE["bulles"],
        "info_pli_termine": PARTIE["info_pli_termine"],
        "bilan_donne": PARTIE["bilan_donne"],
        "debrief_carte": PARTIE["debrief_carte"],
        "debrief_encheres": PARTIE["debrief_encheres"]
    })

@app.route("/api/step_bot", methods=["POST"])
def step_bot():
    if PARTIE["etat"] == "annonces" and PARTIE["tour"] != 0:
        executer_un_coup_bot_enchere()
    elif PARTIE["etat"] == "jeu" and PARTIE["tour"] != 0 and len(PARTIE["pli_en_cours"]) < 4:
        executer_un_coup_bot_carte()
    elif PARTIE["etat"] == "pli_termine":
        ramasser_pli_et_continuer()
    return jsonify({"succes": True})

@app.route("/api/action_enchere", methods=["POST"])
def action_enchere():
    if PARTIE["etat"] != "annonces" or PARTIE["tour"] != 0:
        return jsonify({"erreur": "Ce n'est pas votre tour"}), 400
    
    data = request.json
    choix = data.get("choix")
    
    if isinstance(choix, list):
        val = int(choix[0])
        # SÉCURITÉ : L'enchère doit obligatoirement dépasser le contrat en cours
        if PARTIE["contrat"] and val <= PARTIE["contrat"]["valeur"]:
            return jsonify({"erreur": "Enchère insuffisante"}), 400
        choix = (val, choix[1])
        
    traiter_decision_enchere(0, choix)
    return jsonify({"succes": True})

@app.route("/api/jouer_carte", methods=["POST"])
def route_jouer_carte():
    if PARTIE["etat"] != "jeu" or PARTIE["tour"] != 0:
        return jsonify({"erreur": "Ce n'est pas votre tour"}), 400
    data = request.json
    carte = (data["rang"], data["couleur"])
    regles = REGLES_STANDARD
    atout = PARTIE["contrat"]["atout"]
    jouables = cartes_jouables(PARTIE["mains"][0], PARTIE["pli_en_cours"], atout, 0, regles)
    
    if carte not in jouables:
        return jsonify({"erreur": "Carte interdite"}), 400

    analyse = evaluer_decision_carte(
        PARTIE["mains"][0], jouables, PARTIE["pli_en_cours"], PARTIE["contrat"],
        0, carte, PARTIE["historique"], PARTIE["encheres"], regles
    )
    if analyse:
        PARTIE["debrief_carte"].append(analyse)

    PARTIE["mains"][0].remove(carte)
    PARTIE["pli_en_cours"].append((0, carte))
    PARTIE["historique"].append((0, carte))
    PARTIE["message"] = f"Vous avez joué {carte[0]}{carte[1]}."

    if len(PARTIE["pli_en_cours"]) == 4:
        preparer_fin_pli()
    else:
        PARTIE["tour"] = 1
    return jsonify({"succes": True})

@app.route("/api/nouvelle_donne", methods=["POST"])
def route_nouvelle_donne():
    PARTIE["donneur"] = (PARTIE["donneur"] + 1) % 4
    demarrer_nouvelle_donne()
    return jsonify({"succes": True})

@app.route("/api/export_donne")
def route_export_donne():
    if not PARTIE["mains_initiales_toutes"][0]:
        return jsonify({"texte": "Aucune donne enregistrée."})

    lignes = []
    lignes.append("=" * 60)
    lignes.append("RAPPORT D'ANALYSE DE DONNE — COINCHE IA")
    lignes.append("=" * 60)

    lignes.append(f"\nDonneur : {nom_joueur(PARTIE['donneur'])}")
    if PARTIE["contrat"]:
        c = PARTIE["contrat"]
        coinche_str = ["Non coinché", "COINCHÉ (x2)", "SURCOINCHÉ (x3)"][c.get("coinche", 0)]
        lignes.append(f"Contrat final : {c['valeur']} {c['atout']} par {nom_joueur(c['joueur'])} — {coinche_str}")
    else:
        lignes.append("Contrat final : Aucun (passe générale)")

    lignes.append("\n--- DÉROULEMENT DES ENCHÈRES ---")
    for j, d in PARTIE["encheres"]:
        nom_j = nom_joueur(j)
        action = f"{d[0]} {d[1]}" if isinstance(d, tuple) else str(d).upper()
        lignes.append(f"  {nom_j:18} : {action}")

    lignes.append("\n--- MAINS DE DÉPART (cartes triées) ---")
    for p in range(4):
        cartes_str = " ".join(f"{r}{c}" for r, c in trier_main(PARTIE["mains_initiales_toutes"][p]))
        lignes.append(f"  {nom_joueur(p):18} : {cartes_str}")

    if PARTIE["historique"]:
        lignes.append("\n--- DÉROULEMENT DU JEU DE LA CARTE ---")
        atout = PARTIE["contrat"]["atout"] if PARTIE["contrat"] else "♠"
        regles = REGLES_STANDARD
        for num_pli in range(1, 9):
            idx_deb = (num_pli - 1) * 4
            idx_fin = num_pli * 4
            if idx_deb >= len(PARTIE["historique"]): break
            cartes_pli = PARTIE["historique"][idx_deb:idx_fin]
            detail_pli = "  ".join(f"{nom_joueur(j)}:{r}{c}" for j, (r, c) in cartes_pli)
            if len(cartes_pli) == 4:
                gagnant, c_gagnante = gagnant_pli(cartes_pli, atout)
                pts = sum(points(c, atout) for _, c in cartes_pli)
                if num_pli == 8: pts += regles["dix_de_der"]
                lignes.append(f"  Pli {num_pli} : {detail_pli}")
                lignes.append(f"         ==> Remporté par {nom_joueur(gagnant)} avec {c_gagnante[0]}{c_gagnante[1]} (+{pts} pts)")

    b = PARTIE["bilan_donne"]
    if b:
        lignes.append("\n--- BILAN DE LA DONNE ---")
        lignes.append(f"  Points cartes : Vous {b['pts_nous']} — {b['pts_eux']} Eux")
        lignes.append(f"  Plis faits    : Vous {b['plis_nous']} — {b['plis_eux']} Eux")
        lignes.append(f"  Belote        : {b['belote']}")
        statut = "RÉUSSI" if b["reussi"] else "CHUTÉ"
        lignes.append(f"  Résultat      : {b['contrat_nom']} est {statut}")
        lignes.append(f"  Marque donne  : Vous +{b['marque_nous']} | Eux +{b['marque_eux']}")
        lignes.append(f"  SCORE TOTAL   : Vous {PARTIE['scores'][0]} — {PARTIE['scores'][1]} Eux")

    if PARTIE["debrief_encheres"]:
        lignes.append("\n--- ANALYSE PROFESSEUR : ENCHÈRES ---")
        for txt in PARTIE["debrief_encheres"]:
            lignes.append(f"  {txt}")

    if PARTIE["debrief_carte"]:
        lignes.append("\n--- ANALYSE PROFESSEUR : JEU DE LA CARTE ---")
        for item in PARTIE["debrief_carte"]:
            lignes.append(f"\n  [Pli {item['num_pli']}] Vous avez joué {item['carte_jouee'][0]}{item['carte_jouee'][1]} — Note : {item['label']}")
            lignes.append(f"    Message : {item['message']}")
            lignes.append(f"    Tactique : {item['explication']}")
            if not item.get("est_force") and item.get("options"):
                opts_str = " | ".join(f"{o['carte']}: {o.get('proba', o.get('note', ''))}" for o in item['options'])
                lignes.append(f"    Options évaluées : {opts_str}")

    lignes.append("\n" + "=" * 60)
    return jsonify({"texte": "\n".join(lignes)})

port = int(os.environ.get("PORT", 5001))
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=port, debug=False)
