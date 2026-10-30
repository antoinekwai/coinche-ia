import random
from regles import REGLES_STANDARD
from ia_joueur import JoueurIA
from moteur import distribuer, COULEURS, RANGS

def diagnostiquer_valet():
    bot = JoueurIA()
    total_cas = 0
    joue_valet = 0
    joue_petit = 0
    joue_autre = 0

    atout = "♠"
    petits_atouts = ["7", "8", "10", "D", "R"]

    for i in range(1000):
        # On construit une main de preneur : Valet + 2 ou 3 petits atouts, sans le 9
        nb_petits = random.choice([2, 3])
        mes_atouts = [("V", atout)] + [(r, atout) for r in random.sample(petits_atouts, nb_petits)]
        
        # Le reste en cartes hors atout (avec 1 ou 2 as)
        cotes = [(r, c) for c in COULEURS if c != atout for r in RANGS]
        reste = random.sample(cotes, 8 - len(mes_atouts))
        main = mes_atouts + reste
        
        contrat = {"valeur": 90, "atout": atout, "joueur": 0, "coinche": 0, "capot": False}
        bot.historique = []
        bot.encheres = [(0, (90, atout)), (1, "passe"), (2, "passe"), (3, "passe")]
        
        jouables = list(main)
        choix = bot.jouer_carte(main, jouables, [], contrat, 0, REGLES_STANDARD)
        
        total_cas += 1
        if choix == ("V", atout):
            joue_valet += 1
        elif choix[1] == atout:
            joue_petit += 1
        else:
            joue_autre += 1

    print(f"\nSur {total_cas} donnes où le preneur a le Valet d'atout (sans le 9) à l'entame :")
    print(f"  👉 Joue le Valet d'atout : {joue_valet} fois ({100 * joue_valet / total_cas:.1f} %)")
    print(f"  ❌ Joue un petit atout   : {joue_petit} fois ({100 * joue_petit / total_cas:.1f} %)")
    print(f"  🃏 Joue hors atout (As...) : {joue_autre} fois ({100 * joue_autre / total_cas:.1f} %)")

if __name__ == "__main__":
    diagnostiquer_valet()
