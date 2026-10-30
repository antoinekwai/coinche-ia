# ============================================================
# RÈGLES DU JEU : tout ce qui peut varier est réglé ici
# ============================================================

REGLES_STANDARD = {
    # --- Annonces ---
    "annonce_min": 80,
    "annonce_max": 160,
    "palier": 10,

    # --- Capot ---
    "capot_autorise": True,
    "valeur_capot": 250,
    "capot_non_annonce": False,  # True = faire tous les plis sans l'annoncer rapporte aussi 250


    # --- Coinche ---
    "multi_coinche": 2,
    "multi_surcoinche": 3,

    # --- Décompte ---
    # "contrat"             : on marque (ou la défense marque) seulement le contrat
    # "contrat_plus_points" : on marque le contrat + les points faits
    "mode_score": "contrat",
    "points_belote": 20,
    "belote_pour_contrat": True,   # la belote aide à atteindre le contrat
    "belote_au_score": False,      # la belote s'ajoute au score final
    "dix_de_der": 10,

    # --- Jeu de la carte ---
    "monter_si_partenaire_maitre": True,   # à l'atout, monter même si le partenaire est maître
    "couper_si_partenaire_maitre": False,  # couper même si le partenaire est maître

    # --- Partie ---
    "score_objectif": 1000,
}


# ============================================================
# VARIANTES : on copie les règles standard et on change une valeur
# ============================================================

VARIANTE_POINTS_FAITS = dict(REGLES_STANDARD, mode_score="contrat_plus_points")

VARIANTE_BELOTE_AU_SCORE = dict(REGLES_STANDARD, belote_au_score=True)
