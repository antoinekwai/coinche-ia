from regles import REGLES_STANDARD
from ia_joueur import JoueurIA
from ia_lookahead import JoueurLookahead
from rapide import afficher_rapide

def tester_situation_valet_sept():
    bot = JoueurLookahead()
    atout = "♠"
    contrat = {"valeur": 90, "atout": atout, "joueur": 0, "coinche": 0, "capot": False}
    main = [("V", "♠"), ("7", "♠"), ("A", "♥"), ("10", "♥"), ("R", "♦"), ("8", "♦"), ("7", "♣"), ("8", "♣")]
    jouables = [("V", "♠"), ("7", "♠")]
    pli = []
    
    bot.historique = []
    bot.encheres = [(0, (90, "♠"))]
    
    carte = bot.jouer_carte(main, jouables, pli, contrat, 0, REGLES_STANDARD)
    print(f"👉 Situation de test (V 7 atout en main) : le Lookahead joue : {carte[0]}{carte[1]}")

if __name__ == "__main__":
    print("=== 1. Test tactique : le bot évite-t-il le 7 sous le Valet ? ===")
    tester_situation_valet_sept()

    print("\n=== 2. Duel : IA-Lookahead contre IA standard (1 000 donnes) ===")
    afficher_rapide(JoueurLookahead, JoueurIA, 1000, REGLES_STANDARD, graine=88888)
