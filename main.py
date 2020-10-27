from outils import *
import tkinter as tk
from tkinter import filedialog
from ClassRubrique import *
from ClassTable import *
import ctypes
from tqdm import tqdm


root = tk.Tk()
root.withdraw()

file_path = filedialog.askopenfilename()
length_list = len(file_path.split("/"))
file = file_path.split("/")[length_list-1].split(".")[0]  # nom du fichier à traiter
prefixTable = prefixTable(file)
ctypes.windll.kernel32.SetConsoleTitleW(file)

f = open(file_path)
nbTables = getNbTables(f)
last_pos_test_createTable = f.tell()
ligneLue = f.readline()
print("  Création de la Base de Données \"" + file + "\" avec " + str(nbTables) + " tables")
print()
print()

pbar = tqdm(total=nbTables)

# connexion mysql
cn = connection()
mycursor = cn.cursor()

# création de BD
mycursor.execute("DROP DATABASE IF EXISTS " + file)
mycursor.execute("CREATE DATABASE " + file)

# connexion à la BD
cn = connection(file)
mycursor = cn.cursor()

# initialisation de variables
tabTables = []      # tableau avec tous les tables de la BD
tableCreated = 0    # variable qui passe à 1 chaque fois qu'une table est créée
premiereTable = 0   # variable qui passe à 1 quand une premiere table a été créée
nomTable = ""
tabRubriques = []


# "" = end of file
while ligneLue != "":

    # ajout TABLE
    if ligneLue.startswith("ADD TABLE"):
        # on test si le TABLE d'avant a bien été créé, sinon on le crée
        if testTableSansIndex(tableCreated, premiereTable):
            f.seek(last_pos_test_createTable-7)
            test = f.readline()
            f.seek(last_pos_test_createTable)
            f.readline()
            if not test.startswith("ING"):
                createTableString(nomTable, tabRubriques, mycursor)
                premiereTable = 1
                tableCreated = 1

        # on vide le tableau des rubriques
        tabRubriques = []
        tableCreated = 0

        nomTable = prefixTable + ligneLue.split('"')[1].lower()
        # os.system("cls")
        # print()
        # print("TABLE - " + nomTable, end="\r")

        # "\n" = ligne vide
        while ligneLue != "\n":
            if ligneLue.startswith("  DESCRIPTION"):
                desFichier = ligneLue.split('"')[1]
                # print("Description - " + desFichier)
            if ligneLue.startswith("  LABEL"):
                libFichier = ligneLue.split('"')[1]
                # print("Libellé - " + libFichier)
            ligneLue = f.readline()
        # print()

        while not ligneLue.startswith("ADD TABLE") and not ligneLue.startswith("PSC"):
            # ajout FIELD
            if ligneLue.startswith("ADD FIELD"):
                nomRubrique = ligneLue.split('"')[1]
                nomRubrique = nomRubrique.replace("-", "_")
                typeRubrique = ligneLue.split("AS ")[1].split("\n")[0].split(" ")[0]
                typeRubrique = getType(typeRubrique)
                desRubrique = ""
                libelleRubrique = ""
                formatRubrique = ""
                initialRubrique = ""
                tailleTexte = ""
                while ligneLue != "\n":
                    if ligneLue.startswith("  DESCRIPTION"):
                        desRubrique = ligneLue.split('"')[1]
                    if ligneLue.startswith("  FORMAT"):
                        formatRubrique = ligneLue.split('"')[1]
                        if typeRubrique == "VARCHAR(255)" and formatRubrique.upper().startswith("X"):
                            tailleTexte = getTailleTexte(formatRubrique)
                    if ligneLue.startswith("  LABEL"):
                        libelleRubrique = ligneLue.split('"')[1]
                    if ligneLue.startswith("  INITIAL"):
                        try:
                            initialRubrique = ligneLue.split('"')[1]
                            initialRubrique = getType(initialRubrique)
                            if typeRubrique == "VARCHAR(255)" and initialRubrique != "":
                                initialRubrique = "\"" + initialRubrique + "\""
                        except IndexError:
                            initialRubrique = ""
                    ligneLue = f.readline()
                if typeRubrique == "VARCHAR(255)" and formatRubrique.upper().startswith("X"):
                    typeRubrique = "VARCHAR(" + tailleTexte + ")"
                r = Rubrique(nomRubrique, typeRubrique, desRubrique, formatRubrique, initialRubrique, libelleRubrique)
                tabRubriques.append(r)

                # print("Rubrique - " + r.nom + "  Type - " + r.type)
                # print("  Description - " + r.description)
                # print("  Format - " + r.format)
                # print("  Libellé - " + r.libelle)
                # print("  Initial - " + r.initial)

            # créer la table
            if ligneLue.startswith("ADD INDEX") and tableCreated == 0:
                createTableString(nomTable, tabRubriques, mycursor)
                premiereTable = 1
                tableCreated = 1

            # ajout INDEX
            if ligneLue.startswith("ADD INDEX"):
                nomIndex = ligneLue.split('"')[1]
                # print("       Index : " + nomIndex)

                # avance de 2 lignes
                ligneLue = f.readline()
                ligneLue = f.readline()
                last_pos = f.tell()
                # clé primaire
                if ligneLue.startswith("  PRIMARY") or (ligneLue.startswith("  UNIQUE") and f.readline().startswith("  PRIMARY")):
                    f.seek(last_pos)
                    while not ligneLue.startswith("  INDEX-FIELD"):
                        ligneLue = f.readline()
                    nomClePrimaire = ligneLue.split('"')[1]

                    # test si clé primaire composée
                    ligneLue = f.readline()
                    if ligneLue.startswith("  INDEX-FIELD"):
                        # clé composée
                        nomClePrimaireComposee = nomClePrimaire
                        while ligneLue.startswith("  INDEX-FIELD"):
                            nomClePrimaireComposee = nomClePrimaireComposee + "+" + ligneLue.split('"')[1]
                            ligneLue = f.readline()
                        if ligneLue == "\n":
                            # print("Clé primaire composée : " + nomClePrimaireComposee)
                            mycursor.execute("ALTER TABLE " + nomTable +
                                             " ADD CONSTRAINT pk_" + nomClePrimaire +
                                             " PRIMARY KEY (" + nomClePrimaireComposee.split("+")[0] +
                                             "," + nomClePrimaireComposee.split("+")[1] + ")")
                    else:
                        # print("Clé primaire : " + nomClePrimaire)
                        typeRubrique = ""
                        for r in tabRubriques:
                            if r.nom == nomClePrimaire:
                                r.primaire = 1
                                typeRubrique = r.type
                        mycursor.execute("ALTER TABLE " + nomTable + " MODIFY "
                                         + nomClePrimaire + " " + typeRubrique + " PRIMARY KEY")
                # clé non primaire
                else:
                    f.seek(last_pos)
                    unique = 0
                    if ligneLue.startswith("  UNIQUE"):
                        unique = 1
                        ligneLue = f.readline()
                    if ligneLue.startswith("  INDEX-FIELD"):
                        nomCle = ligneLue.split('"')[1]
                        ligneLue = f.readline()

                        if ligneLue == "\n":
                            # print("Clé : " + nomCle)
                            # When you create a UNIQUE constraint, MySQL creates a UNIQUE index behind the scenes. à savoir
                            if unique:
                                mycursor.execute("ALTER TABLE " + nomTable + " ADD CONSTRAINT " + nomIndex + " UNIQUE KEY(" +
                                                 nomCle + ")")
                            else:
                                mycursor.execute(
                                    "ALTER TABLE " + nomTable + " ADD INDEX " + nomIndex + " (" + nomCle + ")")
                        else:
                            nomCleComposee = nomCle
                            stringToExecute = "ALTER TABLE " + nomTable + " ADD INDEX " + nomIndex + " (" + nomCleComposee
                            while ligneLue.startswith("  INDEX-FIELD"):
                                nomCleComposee = nomCleComposee + "+" + ligneLue.split('"')[1]
                                stringToExecute = stringToExecute + "," + ligneLue.split('"')[1]
                                ligneLue = f.readline()
                            if ligneLue == "\n":
                                # print("Clé composée : " + nomCleComposee)
                                if unique:
                                    split = nomCleComposee.split("+")
                                    stringToExecute = "ALTER TABLE " + nomTable + " ADD CONSTRAINT " + nomIndex + " UNIQUE KEY("
                                    for x in split:
                                        stringToExecute = stringToExecute + x + ","
                                    stringToExecute = stringToExecute.rstrip(',')
                                stringToExecute = stringToExecute + ")"
                                mycursor.execute(stringToExecute)
                # fin de PRIMARY OR UNIQUE
                while ligneLue != "\n":
                    last_pos_test_createTable = f.tell()
                    ligneLue = f.readline()
            # fin de ADD INDEX
            last_pos_test_createTable = f.tell()
            ligneLue = f.readline()
        # fin de ADD TABLE et PSC

        # on crée un objet Table
        t = Table(nomTable, tabRubriques)
        tabTables.append(t)
        pbar.update(1)
        # printFichierCree()

    if not ligneLue.startswith("ADD TABLE"):
        last_pos_test_createTable = f.tell()
        ligneLue = f.readline()
    # fin de ADD TABLE

# End of file, on ferme le fichier
f.close()
pbar.close()

# traitement clés étrangères
generateFK(tabTables, mycursor)
print()
input("  Base de données créée. Appuyez sur Entrée pour fermer cette fenêtre.")
