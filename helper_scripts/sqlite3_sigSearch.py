import sqlite3

# Verbindung zur SQLite-Datenbank herstellen
db_path = 'mf4_data.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Hole alle Tabellennamen aus der Datenbank
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

# Variablenname des gesuchten Kanals
target_column = 'VCU_AI_ClntFlow_Mean'

# Iteriere durch alle Tabellen und suche nach der Spalte
found = False
for table in tables:
    table_name = table[0]
    
    # Hole alle Spaltennamen der aktuellen Tabelle
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = cursor.fetchall()
    
    # Überprüfe, ob die gesuchte Spalte in der aktuellen Tabelle existiert
    for column in columns:
        column_name = column[1]
        if target_column.lower() == column_name.lower():  # Vergleiche ohne Groß-/Kleinschreibung
            print(f"Spalte '{target_column}' gefunden in Tabelle '{table_name}'")
            found = False
            break
    
    if found:
        break

if not found:
    print(f"Spalte '{target_column}' wurde in keiner Tabelle gefunden.")

# Verbindung schließen
conn.close()