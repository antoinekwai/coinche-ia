"""
bot_mc_ia_adaptatif.py (v2 calibrée)
Bot-MC-IA v3 avec budget adaptatif de simulations :
- 15 simulations de base.
- Arrêt rapide si :
  * Écart de victoires >= 2 (suffisant sur 15 sim.)
  * Donne pliée (0 victoire partout ou 100% partout)
  * Plis 7 et 8 (fin de manche évidente, pas besoin de sur-simuler)
- Approfondissement à 45 simulations (+30) uniquement si égalité stricte ou 1 victoire d'écart sur les plis décisifs (1 à 6).
"""
import bot_mc_ia
from bot_mc_ia import BotMCIA
from bot_mc_ia_v3 import BotMCIAv3
from detective_v3 import imaginer_v3
from montecarlo import manques, belote_imaginee, contrat_reussi


class BotMCIAv3Adaptatif(BotMCIAv3):
    nom = "Bot-MC-IA v3 (Adaptatif 15/45)"
    n_base = 15          # simulations initiales
    n_extra = 30         # simulations ajoutées si serré (total = 45)
    seuil_victoires = 2  # écart de victoires pour arrêt immédiat (au lieu de 3)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stats_adaptatif = {"rapides": 0, "approfondies": 0}

    def jouer_carte(self, main, jouables, pli, contrat, joueur, regles):
        if len(jouables) == 1:
            return jouables[0]

        ancien = bot_mc_ia.imaginer_donnes_contraintes
        bot_mc_ia.imaginer_donnes_contraintes = imaginer_v3
        try:
            return self._jouer_carte_adaptatif(main, jouables, pli, contrat, joueur, regles)
        finally:
            bot_mc_ia.imaginer_donnes_contraintes = ancien

    def _evaluer_donne(self, m_sim, pli, contrat, joueur, jouables, regles, atout, eq, attaque):
        bel = belote_imaginee(m_sim, self.historique, atout)
        resultats = {}
        for c in jouables:
            pts_totaux, plis_totaux = self.simuler_avec_ia(m_sim, pli, atout, contrat, joueur, c, regles)
            reussi = contrat_reussi(contrat, pts_totaux[attaque], plis_totaux[attaque],
                                    bel == attaque, regles)
            gagne = reussi if eq == attaque else not reussi
            pts_net = pts_totaux[eq] - pts_totaux[1 - eq]
            resultats[c] = (gagne, pts_net)
        return resultats

    def _jouer_carte_adaptatif(self, main, jouables, pli, contrat, joueur, regles):
        atout = contrat["atout"]
        eq, attaque = joueur % 2, contrat["joueur"] % 2

        victoires = {c: 0 for c in jouables}
        points_net = {c: 0 for c in jouables}

        # --- PASSE 1 : N_BASE simulations ---
        for _ in range(self.n_base):
            m_sim = imaginer_v3(main, joueur, self.historique, self.encheres, atout, regles)
            res = self._evaluer_donne(m_sim, pli, contrat, joueur, jouables, regles, atout, eq, attaque)
            for c, (gagne, pts) in res.items():
                if gagne:
                    victoires[c] += 1
                points_net[c] += pts

        def score(c):
            return 1000.0 * victoires[c] + points_net[c]

        tries = sorted(jouables, key=score, reverse=True)
        c1, c2 = tries[0], tries[1]
        v_max = victoires[c1]
        v_min = min(victoires.values())

        # Critères d'arrêt rapide :
        # 1. Fin de manche (plis 7 et 8) : 15 simuls suffisent
        arret_fin_manche = (len(self.historique) >= 24)
        # 2. Écart de victoires suffisant (>= 2)
        arret_net = (victoires[c1] - victoires[c2] >= self.seuil_victoires)
        # 3. Cas désespéré (0 victoire partout)
        arret_desespere = (v_max == 0)
        # 4. Cas plié d'avance (100% victoires partout)
        arret_plie = (v_min == self.n_base and abs(points_net[c1] - points_net[c2]) >= 10 * self.n_base)

        if arret_fin_manche or arret_net or arret_desespere or arret_plie:
            self.stats_adaptatif["rapides"] += 1
            return c1

        # --- PASSE 2 : N_EXTRA simulations supplémentaires ---
        self.stats_adaptatif["approfondies"] += 1
        for _ in range(self.n_extra):
            m_sim = imaginer_v3(main, joueur, self.historique, self.encheres, atout, regles)
            res = self._evaluer_donne(m_sim, pli, contrat, joueur, jouables, regles, atout, eq, attaque)
            for c, (gagne, pts) in res.items():
                if gagne:
                    victoires[c] += 1
                points_net[c] += pts

        return max(jouables, key=score)
