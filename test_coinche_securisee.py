from regles import REGLES_STANDARD
from systeme import evaluer_chute_contrat_mc

def tester():
    # Main exacte de Nord dans votre donne
    main_nord = [("9", "♠"), ("7", "♠"), ("9", "♥"), ("7", "♥"), ("D", "♣"), ("9", "♣"), ("D", "♦"), ("V", "♦")]
    atout = "♦"
    contrat = {"valeur": 100, "atout": atout, "joueur": 3, "coinche": 0, "capot": False} # Est preneur
    encheres = [(2, "passe"), (3, (80, "♦")), (0, (90, "♥")), (1, (100, "♦"))]
    
    print("=== TEST DE COINCHE SUR LA DONNE RÉELLE ===")
    print("Main de Nord : V D de carreau (2 atouts seulement)")
    print("Contrat adverse : 100 Carreau\n")
    
    # 1. Vérification du pré-filtre
    nb_atouts = sum(1 for c in main_nord if c[1] == atout)
    if nb_atouts < 3:
        print("👉 Pré-filtre actif : Seulement 2 atouts en main -> PASSE IMMÉDIATE (Coinche rejetée sans risque !)")
        return

    # 2. Si par hypothèse il avait eu 3 atouts :
    taux = evaluer_chute_contrat_mc(main_nord, 2, contrat, encheres, [], REGLES_STANDARD, nb_simuls=30)
    print(f"Taux de chute calculé par Monte Carlo : {100 * taux:.1f} %")
    if taux >= 0.80:
        print("Verdict : COINCHE !")
    else:
        print("Verdict : PASSE (sécurisée car < 80 %)")

if __name__ == "__main__":
    tester()
