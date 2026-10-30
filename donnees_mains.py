# Familles triées de la plus faible à la plus forte (points moyens).
# Colonnes : (main, atouts, points moyens, P80, P100, P120, P140, palier 4 fois sur 5)

V9 = [
    ("V 9 secs + 1 as", 2, 106, 82, 58, 31, 11, "80"),
    ("V 9 + 1 petit, sans as", 3, 108, 88, 63, 33, 9, "80"),
    ("V 9 + 2 petits (avec un 10 sec)", 4, 116, 95, 76, 44, 15, "90"),
    ("V 9 secs + 2 as", 2, 117, 92, 73, 47, 21, "90"),
    ("V 9 + 1 petit + 1 as (avec un 10 sec)", 3, 117, 92, 75, 47, 19, "90"),
    ("V 9 + 1 petit + 1 as", 3, 119, 94, 79, 52, 21, "90"),
    ("V 9 + 2 petits, sans as", 4, 120, 98, 83, 52, 17, "100"),
    ("V 9 secs + 3 as", 2, 127, 97, 85, 63, 33, "100"),
    ("V 9 + 1 petit + 2 as", 3, 129, 98, 90, 70, 34, "110"),
    ("V 9 + 2 petits + 1 as", 4, 131, 99, 94, 74, 35, "110"),
    ("V 9 A + 1 petit + 1 as", 4, 135, 100, 97, 81, 40, "120"),
    ("V 9 A 10 + 1 as", 4, 137, 100, 98, 84, 43, "120"),
    ("V 9 + 2 petits + As-10", 4, 141, 100, 98, 90, 56, "120"),
    ("V 9 + 2 petits + 2 as", 4, 141, 100, 99, 92, 57, "120"),
]

VALET = [
    ("V + 2 petits, sans as", 3, 96, 71, 46, 21, 6, "passe"),
    ("V + 1 petit + 2 as", 2, 104, 78, 56, 31, 12, "passe"),
    ("V + 2 petits + 1 as (avec un 10 sec)", 3, 105, 82, 57, 31, 11, "80"),
    ("V + 2 petits + 1 as", 3, 107, 83, 61, 35, 13, "80"),
    ("V + 3 petits, sans as", 4, 108, 87, 64, 34, 10, "80"),
    ("V + 2 petits + As-10", 3, 113, 87, 69, 44, 18, "80"),
    ("V + 2 petits + 2 as", 3, 117, 92, 76, 49, 20, "90"),
    ("V + 3 petits + 1 as", 4, 120, 95, 82, 54, 21, "100"),
    ("V + 4 petits, sans as", 5, 121, 98, 85, 55, 19, "100"),
    ("V + 2 petits + 3 as", 3, 126, 96, 85, 62, 30, "100"),
    ("V + 3 petits + 2 as", 4, 129, 99, 91, 69, 31, "110"),
    ("V + 4 petits + 1 as", 5, 132, 99, 96, 77, 37, "110"),
    ("V A R D (belote), sans as", 4, 133, 99, 91, 72, 41, "110"),
]

NEUF = [
    ("9 + 2 petits, sans as", 3, 83, 53, 30, 14, 4, "passe"),
    ("9 + 2 petits + 1 as", 3, 95, 68, 44, 23, 8, "passe"),
    ("9 + 3 petits + 10 deuxième", 4, 99, 75, 48, 24, 7, "passe"),
    ("9 + 4 petits, sans as", 5, 106, 86, 58, 30, 10, "80"),
    ("9 + 2 petits + 2 as", 3, 106, 80, 58, 34, 15, "80 (limite)"),
    ("9 + 3 petits + 1 as", 4, 107, 85, 60, 33, 12, "80"),
    ("9 + 3 petits + 2 as", 4, 118, 94, 77, 47, 19, "90"),
    ("9 + 4 petits + 1 as", 5, 119, 97, 78, 46, 20, "90"),
]

SANS_V9 = [
    ("4 petits, sans as", 4, 82, 52, 29, 13, 3, "passe"),
    ("3 petits + 2 as", 3, 94, 66, 43, 24, 10, "passe"),
    ("4 petits + 1 as", 4, 97, 70, 45, 25, 9, "passe"),
    ("A R D 8 7 (belote), sans as", 5, 118, 92, 73, 46, 24, "90"),
]

# Mains fortes : (main, atouts, points moyens, P120, P140, P160, capot visé, palier 4 fois sur 5)
V9_FORTES = [
    ("V 9 + 3 petits, sans as", 5, 130, 73, 29, 8, 8, "110"),
    ("V 9 + 4 petits, sans as", 6, 139, 92, 49, 17, 18, "120"),
    ("V 9 + 3 petits + 1 as", 5, 141, 93, 55, 18, 19, "120"),
    ("V 9 + 4 petits + 1 as", 6, 150, 99, 81, 37, 39, "140"),
    ("V 9 + 3 petits + 2 as", 5, 151, 99, 85, 36, 39, "140"),
    ("V 9 A + 2 petits + 2 as", 5, 152, 100, 88, 39, 44, "140"),
    ("V 9 A 10 + 1 petit + 2 as", 5, 153, 100, 88, 39, 42, "140"),
    ("V 9 + 3 petits + A 10 x", 5, 155, 99, 90, 60, 67, "140"),
    ("V 9 A 10 + 1 petit + A 10 x", 5, 160, 100, 97, 76, 82, "capot"),
]
