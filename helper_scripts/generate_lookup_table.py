import sqlite3
import re
import pandas as pd

# Verbindung zur SQLite-Datenbank herstellen
db_path = '/Users/gian/Documents/bat_temp_test/mf4_data.db'  # Pfad zu deiner SQLite-Datenbank
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Hole alle Tabellennamen aus der Datenbank
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

# Regulärer Ausdruck zum Filtern der gewünschten Signale
pattern = re.compile(r'^moduleTemperature(\d+)_BMS(01|05)$', re.IGNORECASE)

# Zusätzliche Spaltennamen für Inlet-, Outlet-Temperaturen und Coolant Flow
inlet_outlet_columns = ['VCU_AI_BatTempIn_Mean', 'VCU_AI_BatTempOut_Mean']
coolant_flow_signal = 'VCU_AI_ClntFlow_Mean'  # Signalname für den Kühlmittelfluss

# Liste zum Speichern der gefundenen Signale
found_columns = []

# Iteriere durch alle Tabellen und suche nach den passenden Spalten
for table in tables:
    table_name = table[0]
    
    # Hole alle Spaltennamen der aktuellen Tabelle
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = cursor.fetchall()
    
    # Überprüfe, ob die Tabelle eine 'file_id'-Spalte hat (Annahme, dass es eine 'file_id' gibt)
    file_id_column = any('file_id' in column[1].lower() for column in columns)
    
    # Überprüfe jede Spalte, ob sie dem Muster entspricht oder ein spezielles Signal ist
    for column in columns:
        column_name = column[1]
        match = pattern.match(column_name)
        
        if match:  # Prüfe, ob der Spaltenname dem Muster entspricht
            sensor_number = int(match.group(1))  # Extrahiere die Sensornummer aus dem Namen
            
            # Wenn es eine 'file_id' gibt, diese hinzufügen
            if file_id_column:
                # Hole distinct 'file_id'-Werte für die aktuelle Tabelle
                cursor.execute(f"SELECT DISTINCT file_id FROM {table_name}")
                file_ids = cursor.fetchall()
                
                for file_id in file_ids:
                    found_columns.append((column_name, table_name, sensor_number, file_id[0]))
            else:
                found_columns.append((column_name, table_name, sensor_number, None))

        # Prüfen auf Inlet- und Outlettemperaturspalten
        if column_name in inlet_outlet_columns:
            # Füge sie mit einem speziellen Sensornummer-Code hinzu, z. B. 101 für Inlet und 102 für Outlet
            sensor_number = 101 if 'In_Mean' in column_name else 102
            if file_id_column:
                cursor.execute(f"SELECT DISTINCT file_id FROM {table_name}")
                file_ids = cursor.fetchall()
                for file_id in file_ids:
                    # Prüfe, ob es gültige (nicht NULL) Einträge gibt
                    cursor.execute(f"SELECT 1 FROM {table_name} WHERE {column_name} IS NOT NULL AND file_id = ? LIMIT 1", (file_id[0],))
                    if cursor.fetchone():
                        found_columns.append((column_name, table_name, sensor_number, file_id[0]))
            else:
                # Prüfe, ob es gültige (nicht NULL) Einträge gibt
                cursor.execute(f"SELECT 1 FROM {table_name} WHERE {column_name} IS NOT NULL LIMIT 1")
                if cursor.fetchone():
                    found_columns.append((column_name, table_name, sensor_number, None))

        # Prüfen auf das Kühlmittelflusssignal
        if column_name == coolant_flow_signal:
            sensor_number = 103  # Verwende die Sensornummer 103 für das Kühlmittelflusssignal
            print(f"Found coolant flow signal '{coolant_flow_signal}' in table '{table_name}'")
            
            if file_id_column:
                cursor.execute(f"SELECT DISTINCT file_id FROM {table_name}")
                file_ids = cursor.fetchall()
                for file_id in file_ids:
                    # Prüfe, ob es gültige (nicht NULL) Einträge für den Kühlmittelfluss gibt
                    cursor.execute(f"SELECT 1 FROM {table_name} WHERE {column_name} IS NOT NULL AND file_id = ? LIMIT 1", (file_id[0],))
                    if cursor.fetchone():  # Nur hinzufügen, wenn es nicht NULL Werte gibt
                        found_columns.append((column_name, table_name, sensor_number, file_id[0]))
            else:
                # Prüfe, ob es gültige (nicht NULL) Einträge für den Kühlmittelfluss gibt
                cursor.execute(f"SELECT 1 FROM {table_name} WHERE {column_name} IS NOT NULL LIMIT 1")
                if cursor.fetchone():
                    found_columns.append((column_name, table_name, sensor_number, None))

# Ergebnisse in ein DataFrame konvertieren
df = pd.DataFrame(found_columns, columns=['Channel.Name', 'Table.Name', 'SensorNumber', 'File.ID'])

# Sortiere das DataFrame nach der Sensornummer (negative Nummern für Inlet/Outlet/Coolant Flow kommen zuerst)
df = df.sort_values(by='SensorNumber').reset_index(drop=True)

# Speichere das DataFrame als Parquet-Datei
output_parquet = '/Users/gian/Documents/GitHub/bat_temp_test/db_lookup_table.parquet'
df.to_parquet(output_parquet, index=False)

print(f"Gefundene Signale wurden in '{output_parquet}' gespeichert.")

# Verbindung schließen
conn.close()