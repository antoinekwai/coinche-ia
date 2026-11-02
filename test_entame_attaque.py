import random
from regles import REGLES_STANDARD
from moteur import COULEURS, RANGS
from ia_joueur import JoueurIA

def tester_entames():
    bot = JoueurIA()
    atout = "♠"
    cotes = [c for c in COULEURS if c != atout]
    petits_atouts = ["7", "8", "9", "10", "D", "R"]

    for role_nom, joueur_preneur in [("JE SUIS DÉCLARANT", 0), ("MON PARTENAIRE EST DÉCLARANT", 2)]:
        stats = {"valet": 0, "as": 0, "autre": 0}
        total = 1000

        for i in range(total):
            random.seed(i + (1000 if joueur_preneur == 2 else 0))
            
            # Main critique : Valet d'atout + 2 ou 3 petits atouts + 1 ou 2 As annexes
            nb_atouts = random.choice([3, 4])
            mes_atouts = [("V", atout), ("9", atout)] + [(r, atout) for r in random.sample(["7", "8", "10", "D", "R"], nb_atouts - 2)]
            
            # 1 ou 2 As hors atout
            as_annexes = [("A", c) for c in random.sample(cotes, random.choice([1, 2]))]
            
            reste_pool = [(r, c) for c in cotes for r in RANGS if (r, c) not in as_annexes]
            main = mes_atouts + as_annexes + random.sample(reste_pool, 8 - len(mes_atouts) - len(as_annexes))
            
            contrat = {"valeur": 100, "atout": atout, "joueur": joueur_preneur, "coinche": 0, "capot": False}
            bot.historique = []
            
            if joueur_preneur == 0:
                bot.encheres = [(0, (100, atout)), (1, "passe"), (2, "passe"), (3, "passe")]
            else:
                bot.encheres = [(2, (90, atout)), (3, "passe"), (0, (100, atout)), (1, "passe"), (2, "passe"), (3, "passe")]

            jouables = list(main)
            choix = bot.jouer_carte(main, jouables, [], contrat, 0, REGLES_STANDARD)

            if choix == ("V", atout):
                stats["valet"] += 1
            elif choix[0] == "A" and choix[1] != atout:
                stats["as"] += 1
            else:
                stats["autre"] += 1

        print(f"\n=== {role_nom} (1 000 donnes avec Valet + As annexes) ===")
        print(f"  👉 Purge au Valet d'atout : {stats['valet']} ({100 * stats['valet'] / total:.1f} %)")
        print(f"  🃏 Tente d'encaisser un As : {stats['as']} ({100 * stats['as'] / total:.1f} %)")
        print(f"  ⚪ Autre carte jouée      : {stats['autre']} ({100 * stats['autre'] / total:.1f} %)")

if __name__ == "__main__":
    tester_entames()
