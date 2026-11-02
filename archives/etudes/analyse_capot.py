import random
from moteur import COULEURS, RANGS, equipe_belote
from systeme import niveau_ouverture, increment_reponse, maitresses_en_plus
from experience_coinche import SysCoinche
from montecarlo import JoueurMonteCarloContrat
from partie import jouer_manche


def valeurs_au_passage(encheres):
    """Pour chaque joueur : valeur du contrat lors de sa première passe (None = personne n'avait parlé)."""
    valeur, res = None, {}
    for j, d in encheres:
        if isinstance(d, tuple):
            valeur = d[0]
        elif d == "passe" and j not in res:
            res[j] = valeur
    return res


def partenaire_coherent(m, nous, a, maxi):
    """Le partenaire aurait-il fait exactement les mêmes réponses avec cette main ?"""
    ouverture = nous[0][1][0]
    if min(ouverture + increment_reponse(m, ouverture, a), maxi) != nous[1][1][0]:
        return False
    if len(nous) >= 4:   # réponse à la demande de capot
        if min(nous[2][1][0] + 10 * maitresses_en_plus(m, a), maxi) != nous[3][1][0]:
            return False
    return True


def adversaire_coherent(m, valeur, marge, plafond, regles):
    """L'adversaire aurait-il passé avec cette main (selon votre système) ?"""
    niv = max(niveau_ouverture(m, c) for c in COULEURS)
    if niv == 0:
        return True
    if valeur is None or niv == 250:
        return False                              # il aurait ouvert
    limite = min(niv + marge, max(niv, plafond), regles["annonce_max"])
    return valeur + regles["palier"] > limite     # il ne pouvait pas intervenir


class JoueurAnalyseCapot(SysCoinche):
    """Votre système complet, mais le capot est décidé par simulation."""
    nom = "AnalyseCapot"
    declenchement = 7      # plis théoriques (ouvreur + partenaire) qui lancent l'analyse
    nb_donnes = 30         # donnes imaginées puis jouées
    nb_simulations = 10    # réflexion de Monte Carlo dans chaque donne imaginée
    critere = "gain"       # "gain" (meilleur gain moyen) ou "seuil" (probabilité minimale)
    seuil_proba = 0.9
    declenche = False      # passe à True quand l'analyse a été lancée (pour les statistiques)

    def imaginer_donnes(self, main, joueur, nous, a, regles):
        """Donnes au hasard, conservées seulement si elles collent aux enchères."""
        partenaire = (joueur + 2) % 4
        adversaires = [(joueur + 1) % 4, (joueur + 3) % 4]
        passages = valeurs_au_passage(self.encheres)
        inconnues = [(r, c) for c in COULEURS for r in RANGS if (r, c) not in main]
        donnes = []
        for _ in range(20000):
            random.shuffle(inconnues)
            mains = [None] * 4
            mains[joueur] = main[:]
            mains[partenaire] = inconnues[0:8]
            mains[adversaires[0]] = inconnues[8:16]
            mains[adversaires[1]] = inconnues[16:24]
            if not partenaire_coherent(mains[partenaire], nous, a, regles["annonce_max"]):
                continue
            if all(adversaire_coherent(mains[p], passages.get(p), self.marge, self.plafond, regles)
                   for p in adversaires):
                donnes.append(mains)
                if len(donnes) == self.nb_donnes:
                    break
        return donnes
    def jouer_donnes(self, donnes, joueur, a, regles):
        """Joue chaque donne imaginée en visant le capot. Renvoie [(points, capot réalisé)]."""
        equipe = joueur % 2
        premier = self.encheres[0][0]          # le premier à parler entame
        contrat = {"valeur": regles["valeur_capot"], "atout": a, "joueur": joueur,
                   "coinche": 0, "capot": True}
        resultats = []
        for mains in donnes:
            copie = [m[:] for m in mains]
            belote = equipe_belote(copie, a)
            joueurs = [JoueurMonteCarloContrat(self.nb_simulations) for _ in range(4)]
            pts, plis = jouer_manche(copie, contrat, premier, joueurs, regles)
            total = pts[equipe]
            if belote == equipe and regles["belote_pour_contrat"]:
                total += regles["points_belote"]
            resultats.append((total, plis[equipe] == 8))
        return resultats

    def decision_capot(self, main, joueur, contrat, regles, total, a):
        """Lance l'analyse si l'ouvreur compte assez de plis théoriques."""
        if total < self.declenchement or not regles["capot_autorise"]:
            return None                        # règles habituelles
        moi = joueur % 2
        nous = [(j, d) for (j, d) in self.encheres if isinstance(d, tuple) and j % 2 == moi]
        donnes = self.imaginer_donnes(main, joueur, nous, a, regles)
        if len(donnes) < 10:
            return None                        # trop peu de donnes cohérentes : règles habituelles
        self.declenche = True
        res = self.jouer_donnes(donnes, joueur, a, regles)
        n = len(res)

        # Options : rester au contrat actuel, monter d'un ou plusieurs paliers, ou capot
        options = [(contrat["valeur"], "passe")]
        v = contrat["valeur"] + regles["palier"]
        while v <= regles["annonce_max"]:
            options.append((v, (v, a)))
            v += regles["palier"]
        evaluees = [(valeur, sum(t >= valeur for t, _ in res) / n, dec) for valeur, dec in options]
        p_capot = sum(c for _, c in res) / n
        evaluees.append((regles["valeur_capot"], p_capot, (regles["valeur_capot"], a)))

        if self.critere == "seuil":
            # Votre règle : l'annonce la plus haute qui réussit au moins seuil_proba du temps
            ok = [e for e in evaluees if e[1] >= self.seuil_proba]
            return max(ok, key=lambda e: e[0])[2] if ok else "passe"
        # Sinon : l'annonce au meilleur gain moyen, V × (2p − 1)
        return max(evaluees, key=lambda e: e[0] * (2 * e[1] - 1))[2]
