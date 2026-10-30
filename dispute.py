import random
from moteur import COULEURS, RANGS, decompte, equipe_belote
from joueurs import JoueurRegles
from partie import jouer_manche
from systeme_corrige import SysCorrige, niveau_corrige


def coherent(m, p, encheres):
    """La main m du joueur p est-elle compatible avec ses enchères ?"""
    contrat_en_cours = False
    equipes = set()                       # équipes qui ont déjà annoncé
    for j, d in encheres:
        if isinstance(d, tuple):
            # Ouverture ou intervention (pas une réponse au partenaire) : il fallait une main
            if j == p and j % 2 not in equipes and niveau_corrige(m, d[1]) == 0:
                return False
            equipes.add(j % 2)
            contrat_en_cours = True
        elif d == "passe" and j == p and not contrat_en_cours:
            # Il a passé alors que personne n'avait parlé : il n'avait pas de quoi ouvrir
            if max(niveau_corrige(m, c) for c in COULEURS) > 0:
                return False
    return True


class JoueurDispute(SysCorrige):
    """Système corrigé, mais les enchères disputées sont décidées par simulation."""
    nom = "Disputé"
    nb_donnes = 20       # donnes imaginées par décision
    essais = 3000        # tirages maximum pour les trouver
    prevoir_coinche = True   # tenir compte de la coinche adverse quand on monte

    def imaginer_disputee(self, main, joueur):

        autres = [p for p in range(4) if p != joueur]
        inconnues = [(r, c) for c in COULEURS for r in RANGS if (r, c) not in main]
        donnes = []
        for _ in range(self.essais):
            random.shuffle(inconnues)
            mains = [None] * 4
            mains[joueur] = main[:]
            for k, p in enumerate(autres):
                mains[p] = inconnues[8 * k:8 * k + 8]
            if all(coherent(mains[p], p, self.encheres) for p in autres):
                donnes.append(mains)
                if len(donnes) == self.nb_donnes:
                    break
        return donnes

    def jouer(self, mains, contrat, regles):
        copie = [m[:] for m in mains]
        belote = equipe_belote(copie, contrat["atout"])
        robots = [JoueurRegles() for _ in range(4)]
        premier = self.encheres[0][0] if self.encheres else (contrat["joueur"] + 1) % 4
        pts, plis = jouer_manche(copie, contrat, premier, robots, regles)
        return pts, plis, belote


    def decision_disputee(self, main, joueur, contrat, regles, a, valeur):
        donnes = self.imaginer_disputee(main, joueur)

        if len(donnes) < 8:
            return None                   # trop peu de donnes cohérentes : règle de la marge
        moi = joueur % 2
        suivante = contrat["valeur"] + regles["palier"]
        peut_monter = suivante <= regles["annonce_max"]
        leur = dict(contrat, coinche=0)
        leur_coinche = dict(contrat, coinche=1)
        notre = {"valeur": suivante, "atout": a, "joueur": joueur, "coinche": 0, "capot": False}
        totaux = {"passe": 0, "coinche": 0}
        if peut_monter:
            totaux["monter"] = 0

        for mains in donnes:
            # Leur contrat : une seule partie jouée, comptée sans puis avec coinche
            pts, plis, belote = self.jouer(mains, leur, regles)
            for nom, c in (("passe", leur), ("coinche", leur_coinche)):
                s, _ = decompte(c, pts, plis, belote, regles)
                totaux[nom] += s[moi] - s[1 - moi]
            # Notre contrat, un palier au-dessus
            
            if peut_monter:
                adversaires = [(joueur + 1) % 4, (joueur + 3) % 4]
                c = notre
                if self.prevoir_coinche and any(self.veut_coincher(mains[p], notre) for p in adversaires):
                    c = dict(notre, coinche=1)
                pts, plis, belote = self.jouer(mains, c, regles)
                s, _ = decompte(c, pts, plis, belote, regles)
                totaux["monter"] += s[moi] - s[1 - moi]


        choix = max(totaux, key=totaux.get)
        return {"passe": "passe", "coinche": "coinche", "monter": (suivante, a)}[choix]
