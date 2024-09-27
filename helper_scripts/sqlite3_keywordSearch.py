import sqlite3

# Verbinden Sie sich mit Ihrer SQLite-Datenbank
conn = sqlite3.connect('mf4_data.db')
cursor = conn.cursor()

# Abrufen aller Tabellen aus der Datenbank
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

# Suchen Sie nach "coolant" in allen Tabellen
for table_name in tables:
    table_name = table_name[0]
    try:
        # Prüfen, ob die Tabelle eine Spalte mit "coolant" im Namen hat
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        for column in columns:
            column_name = column[1]
            if 'vcu' in column_name.lower():
                print(f'Column with "VOC" found in table {table_name}: {column_name}')
                
        # Prüfen, ob in den Daten selbst das Wort "coolant" vorkommt
        cursor.execute(f"SELECT * FROM {table_name} WHERE CAST({column_name} AS TEXT) LIKE '%vcu%'")
        results = cursor.fetchall()
        if results:
            print(f'Found coolant data in table {table_name}:')
            for result in results:
                print(result)
                
    except Exception as e:
        print(f"Could not process table {table_name}: {e}")

# Schließen der Verbindung zur Datenbank
conn.close()