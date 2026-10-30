from moteur import COULEURS
from joueurs import JoueurRegles, estimer

ORDRE_ATOUT_DESC = ["V", "9", "A", "10", "R", "D", "8", "7"]
ORDRE_COULEUR_DESC = ["A", "10", "R", "D", "V", "9", "8", "7"]


def nb_atouts(main, a):
    return len([c for c in main if c[1] == a])


def nb_as(main, a):
    return len([c for c in main if c[0] == "A" and c[1] != a])


def maitres(main, couleur, a):
    """Cartes maîtresses consécutives dans une couleur, en partant de la plus forte."""
    ordre = ORDRE_ATOUT_DESC if couleur == a else ORDRE_COULEUR_DESC
    n = 0
    for rang in ordre:
        if (rang, couleur) not in main:
            break
        n += 1
    return n


def plis_surs(main, a):
    return sum(maitres(main, c, a) for c in COULEURS)


def maitresses_en_plus(main, a):
    """Au-delà des as : 10 (avec l'as), roi (avec as et 10), atouts maîtres."""
    total = sum(max(0, maitres(main, c, a) - 1) for c in COULEURS if c != a)
    if ("V", a) in main:
        total += maitres(main, a, a)
    elif ("9", a) in main:
        total += 1
    return total


def niveau_ouverture(main, a):
    n, nas = nb_atouts(main, a), nb_as(main, a)
    valet, neuf = ("V", a) in main, ("9", a) in main
    if n >= 4 and plis_surs(main, a) == len(main):
        return 250
    if estimer(main, a) >= 130:
        return 130
    if valet and neuf and n >= 4:
        return 100
    if valet and neuf and n >= 3 and nas >= 1:
        return 90
    if (valet or neuf) and n >= 3 and nas >= 1:
        return 80
    return 0


def increment_reponse(main, ouverture, a):
    """De combien le partenaire remonte l'ouverture."""
    n, nas = nb_atouts(main, a), nb_as(main, a)
    if ouverture == 80:
        return 10 * nas + 10 * (("V", a) in main) + 10 * (("9", a) in main)
    if ouverture == 90:
        if n >= 2:
            return 10 * nas
        if n == 1:
            return 10 * (nas // 2)
        return 0
    if ouverture in (100, 110, 120):
        return 10 * nas
    return 0   # 130 ou plus : le partenaire passe

def reponse_partenaire(encheres, ouvreur):
    """Annonce du partenaire de l'ouvreur, si elle a été faite avant toute annonce adverse."""
    partenaire = (ouvreur + 2) % 4
    for j, d in encheres:
        if isinstance(d, tuple):
            if j % 2 != ouvreur % 2:
                return None              # les adversaires ont parlé avant
            if j == partenaire:
                return d[0]
    return None

class JoueurSysteme(JoueurRegles):
    """Vos annonces. Coinche et jeu de la carte identiques au joueur à règles."""
    nom = "Système"
    marge = 10          # marge accordée quand les adversaires parlent
    plafond = 130       # la marge ne permet pas de dépasser ce niveau
    seuil_capot = 9     # plis sûrs exigés pour annoncer capot
    malus_sans_entame = 1   # plis sûrs supplémentaires exigés si l'adversaire entame
    ouvreur_compte_reponse = False   # l'ouvreur se défend sur le niveau de l'équipe
    bonus_belote = 0                 # points ajoutés au niveau si l'on a la belote

    def bonus_belote_main(self, main, a):
        if ("R", a) in main and ("D", a) in main:
            return self.bonus_belote
        return 0


    encheres = []

    def niveau(self, main, a):
        """Niveau d'ouverture d'une main (remplaçable par le réseau)."""
        return niveau_ouverture(main, a)
    
    def decision_capot(self, main, joueur, contrat, regles, total, a):
        """Point d'entrée pour l'analyse capot (None = règles habituelles)."""
        return None
   
    def decision_disputee(self, main, joueur, contrat, regles, a, valeur):
        """Point d'entrée pour les enchères disputées (None = règle de la marge)."""
        return None

    def reponse(self, main, ouverture, a):
        """Réponse du partenaire (remplaçable pour tester des variantes)."""
        return increment_reponse(main, ouverture, a)


    def veut_coincher(self, main, contrat):
        a = contrat["atout"]
        return (("V", a) in main and nb_atouts(main, a) >= 3
                and nb_as(main, a) >= 1 and contrat["valeur"] >= 100)

    def annoncer(self, main, joueur, contrat, regles):
        moi = joueur % 2
        if contrat is not None and contrat["joueur"] % 2 != moi and self.veut_coincher(main, contrat):
            return "coinche"
        if contrat is not None and contrat["capot"]:
            return "passe"

        annonces = [(j, d) for (j, d) in self.encheres if isinstance(d, tuple)]
        nous = [(j, d) for (j, d) in annonces if j % 2 == moi]
        adv_parle = any(j % 2 != moi for (j, d) in annonces)
        suivante = regles["annonce_min"] if contrat is None else contrat["valeur"] + regles["palier"]
        maxi = regles["annonce_max"]

        # 1. Notre équipe n'a pas encore parlé : ouverture ou intervention
        if not nous:
            couleur = max(COULEURS, key=lambda c: (self.niveau(main, c), estimer(main, c)))
            niv = self.niveau(main, couleur)

            if niv == 0:
                return "passe"
            if niv == 250:
                if regles["capot_autorise"]:
                    return (regles["valeur_capot"], couleur)
                niv = maxi
            if contrat is None:
                return (niv, couleur)
            decision = self.decision_disputee(main, joueur, contrat, regles, couleur, niv)
            if decision is not None:
                return decision
            niv_def = niv + self.bonus_belote_main(main, couleur)
            if suivante <= min(niv_def + self.marge, max(niv_def, self.plafond), maxi):
        
                return (min(max(suivante, niv), maxi), couleur)
            return "passe"

        ouvreur, (ouverture, a) = nous[0]

        # 2. Les adversaires ont surenchéri : on se bat jusqu'à notre limite
        if contrat["joueur"] % 2 != moi:
            if joueur == ouvreur:
                valeur = self.niveau(main, a)
                rep = reponse_partenaire(self.encheres, ouvreur)
                if self.ouvreur_compte_reponse and rep is not None:
                    valeur += rep - ouverture
            else:
                valeur = ouverture + self.reponse(main, ouverture, a)
            valeur += self.bonus_belote_main(main, a)

            decision = self.decision_disputee(main, joueur, contrat, regles, a, valeur)
            if decision is not None:
                return decision

            limite = min(valeur + self.marge, max(valeur, self.plafond), maxi)

            return (suivante, a) if suivante <= limite else "passe"

        # 3. Le contrat est à nous : on ne dialogue que si les adversaires se taisent
        if adv_parle:
            return "passe"

        # 3a. Le partenaire de l'ouvreur
        if joueur != ouvreur:
            if len(nous) == 1:                                   # réponse à l'ouverture
                inc = self.reponse(main, ouverture, a)
            elif len(nous) == 3 and nous[2][0] == ouvreur:       # réponse à la demande de capot
                inc = 10 * maitresses_en_plus(main, a)
            else:
                return "passe"
            valeur = min(contrat["valeur"] + inc, maxi)
            return (valeur, a) if inc > 0 and valeur >= suivante else "passe"

        # 3b. L'ouvreur : capot, demande de capot, ou passe
        if len(nous) not in (2, 4):
            return "passe"
        demande = 10 if len(nous) == 4 else 0
        aide = (contrat["valeur"] - ouverture - demande) // 10   # plis promis par le partenaire
        total = plis_surs(main, a) + aide
        entame = self.encheres[0][0]   # le premier à parler entame la donne
        seuil = self.seuil_capot + (0 if entame % 2 == moi else self.malus_sans_entame)
        decision = self.decision_capot(main, joueur, contrat, regles, total, a)
        if decision is not None:
            return decision


        if total >= seuil and regles["capot_autorise"]:

            return (regles["valeur_capot"], a)
        if len(nous) == 2 and total >= seuil - 2 and suivante <= maxi:

            return (suivante, a)                                 # demande de capot (+10)
        return "passe"
