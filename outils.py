import mysql.connector
from tqdm import tqdm

def getType(type):
    if type == "character":
        return "VARCHAR(255)"
    if type == "logical":
        return "BOOLEAN"
    if type == "no" or type == "Non":
        return str(0)
    if type == "yes" or type == "Oui":
        return str(1)
    if type == "raw":
        return "TINYBLOB"
    if type == "clob":
        return "LONGTEXT"
    return type


def getTailleTexte(format):
    return format.partition("(")[2].partition(")")[0]


def createTableString(nomTable, tabRubriques, mycursor):
    createTableString = "CREATE TABLE IF NOT EXISTS " + nomTable + "("
    for rub in tabRubriques:
        if rub.initial != "":
            createTableString = createTableString + rub.nom + " " + rub.type + " DEFAULT " + rub.initial + ","
        else:
            createTableString = createTableString + rub.nom + " " + rub.type + ","

    createTableString = createTableString[:-1] + ")"
    mycursor.execute(createTableString)


def connection(db = ""):

    config = {
        "user": "root",
        "password": "",
        "host": "localhost",
        "database": db
    }
    try:
        c = mysql.connector.connect(**config)
        return c
    except:
        print("Connection error")
        exit(1)


def testTableSansIndex(tableCreated, premiereTable):
    if tableCreated == 0 and premiereTable == 1:
        return True
    else:
        return False

def countFK(tabTables):
    cpt = 0
    for t1 in tabTables:
        for r1 in t1.tabRub:
            if r1.primaire:
                for t2 in tabTables:
                    if t1.nom != t2.nom:
                        for r2 in t2.tabRub:
                            if r1.nom == r2.nom:
                                cpt = cpt + 1
    return cpt


def generateFK(tabTables, mycursor):
    nbCles = countFK(tabTables)

    print("\n  Ajout des clés étrangères (" + str(nbCles) + " clés) :\n")
    pbar = tqdm(total=nbCles)
    for t1 in tabTables:
        #print(t1.nom)
        for r1 in t1.tabRub:
            if r1.primaire:
                for t2 in tabTables:
                    if t1.nom != t2.nom:
                        for r2 in t2.tabRub:
                            if r1.nom == r2.nom:
                                #print("Relier fichier source \"" + t1.nom +
                                #      "\" avec fichier \"" + t2.nom + "\" avec la clé \"" + r1.nom + "\"")
                                pbar.update(1)
                                mycursor.execute(
                                    "ALTER TABLE " + t2.nom + " ADD FOREIGN KEY (" + r1.nom + ") REFERENCES " +
                                    t1.nom + "(" + r1.nom + ")")
    pbar.close()


def printFichierCree():
    print("")
    print("*************************************************************************")
    print("                            Fichier créé !")
    print("*************************************************************************")
    print("")


def prefixTable(file):
    if file == "commun":
        return "com_"
    if file == "intranet":
        return "int_"
    if file == "pegaze":
        return "peg_"
    if file == "pegaze_mobile":
        return "pem_"
    if file == "someci_ida":
        return "soi_"
    if file == "someci_ida_mobile":
        return "sim__"
    if file == "someci_lyon":
        return "sol_"
    if file == "someci_lyon_mobile":
        return "slm__"
    return ""

def getNbTables(f):
    ligneLue = f.readline()
    nbTables = 0

    while ligneLue != "":
        if ligneLue.startswith("ADD TABLE"):
            nbTables = nbTables + 1
        ligneLue = f.readline()
    f.seek(0, 0)
    return nbTables
