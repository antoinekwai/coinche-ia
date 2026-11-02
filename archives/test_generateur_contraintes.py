from generateur_contraintes import imaginer_donnes_contraintes
from regles import REGLES_STANDARD

def tester_cas_extreme():
    atout = "♠"
    # Sud n'a qu'un atout (le 7 de Pique)
    main_sud = [("7", "♠"), ("A", "♥"), ("9", "♥"), ("V", "♣"), ("D", "♣"), ("7", "♣"), ("A", "♦"), ("8", "♦")]
    
    # Enchères : Nord ouvre à 80 ♠, Est pousse à 120 ♠
    encheres = [
        (1, "passe"),
        (2, (80, "♠")),
        (3, (120, "♠")),
        (0, "passe"),
        (1, "passe"),
        (2, "passe"),
        (3, "passe")
    ]
    
    print("=== TEST DU GÉNÉRATEUR SOUS CONTRAINTES COUPLÉES ===")
    print("Données du problème :")
    print("  • Sud a 1 atout (7♠).")
    print("  • Nord a ouvert à 80 ♠ (promet au moins 3 atouts).")
    print("  • Est a annoncé 120 ♠ (promet au moins 4-5 atouts).")
    print("  • Ouest a passé.\n")

    # Générer 5 donnes
    chicanes_ouest = 0
    chicanes_carreau_est = 0
    total = 200

    for i in range(total):
        mains = imaginer_donnes_contraintes(main_sud, 0, [], encheres, atout, REGLES_STANDARD)
        n_ouest = sum(1 for c in mains[1] if c[1] == atout)
        n_nord = sum(1 for c in mains[2] if c[1] == atout)
        n_est = sum(1 for c in mains[3] if c[1] == atout)
        
        # Vérifier si Est est chicane Carreau
        if not any(c[1] == "♦" for c in mains[3]):
            chicanes_carreau_est += 1
            
        if n_ouest == 0:
            chicanes_ouest += 1

        if i < 3:
            print(f"Tirage n°{i+1} :")
            print(f"  Ouest (passe)   : {n_ouest} atouts | {' '.join(r+c for r,c in mains[1])}")
            print(f"  Nord (ouvreur)  : {n_nord} atouts | {' '.join(r+c for r,c in mains[2])}")
            print(f"  Est (preneur 120): {n_est} atouts | {' '.join(r+c for r,c in mains[3])}")
            print()

    print(f"Sur {total} donnes générées :")
    print(f"  👉 Ouest est chicane atout dans {100 * chicanes_ouest / total:.1f} % des cas (déduction exacte !)")
    print(f"  👉 Est (preneur 120) a une chicane Carreau dans {100 * chicanes_carreau_est / total:.1f} % des cas !")

if __name__ == "__main__":
    tester_cas_extreme()
