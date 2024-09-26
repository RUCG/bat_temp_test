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
pattern = re.compile(r'^moduleTemperature(\d+)_BMS01$', re.IGNORECASE)

# Zusätzliche Spaltennamen für Inlet- und Outlettemperaturen
inlet_outlet_columns = ['coolantInletTemperature_BMS05', 'coolantOutletTemperature_BMS05',
                        'coolantInletTemperature_BMS01', 'coolantOutletTemperature_BMS01']

# Name des Flusssignals
flow_signal_name = 'VCU_AI_ClntFlow_Mean'

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
    
    # Überprüfe jede Spalte, ob sie dem Muster entspricht
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
                    # Prüfen, ob der Wert in der Spalte nicht NULL ist
                    cursor.execute(f"SELECT 1 FROM {table_name} WHERE {column_name} IS NOT NULL AND file_id = ? LIMIT 1", (file_id[0],))
                    if cursor.fetchone():
                        found_columns.append((column_name, table_name, sensor_number, file_id[0]))
            else:
                # Prüfen, ob der Wert in der Spalte nicht NULL ist
                cursor.execute(f"SELECT 1 FROM {table_name} WHERE {column_name} IS NOT NULL LIMIT 1")
                if cursor.fetchone():
                    found_columns.append((column_name, table_name, sensor_number, None))

        # Prüfen auf Inlet- und Outlettemperaturspalten
        if column_name in inlet_outlet_columns:
            # Füge sie mit einem speziellen Sensornummer-Code hinzu, z. B. 101 für Inlet und 102 für Outlet
            sensor_number = 101 if 'Inlet' in column_name else 102
            if file_id_column:
                cursor.execute(f"SELECT DISTINCT file_id FROM {table_name}")
                file_ids = cursor.fetchall()
                for file_id in file_ids:
                    # Prüfen, ob der Wert in der Spalte nicht NULL ist
                    cursor.execute(f"SELECT 1 FROM {table_name} WHERE {column_name} IS NOT NULL AND file_id = ? LIMIT 1", (file_id[0],))
                    if cursor.fetchone():
                        found_columns.append((column_name, table_name, sensor_number, file_id[0]))
            else:
                # Prüfen, ob der Wert in der Spalte nicht NULL ist
                cursor.execute(f"SELECT 1 FROM {table_name} WHERE {column_name} IS NOT NULL LIMIT 1")
                if cursor.fetchone():
                    found_columns.append((column_name, table_name, sensor_number, None))
        
        # Prüfen auf das spezifische Flusssignal
        if column_name == flow_signal_name:
            sensor_number = 103  # Verwende die Sensornummer 103 für das Flusssignal
            print(f"Found coolant flow signal '{flow_signal_name}' in table '{table_name}'")
            
            if file_id_column:
                cursor.execute(f"SELECT DISTINCT file_id FROM {table_name}")
                file_ids = cursor.fetchall()
                for file_id in file_ids:
                    # Prüfen, ob der Wert in der Flusssignalspalte nicht NULL ist
                    cursor.execute(f"SELECT 1 FROM {table_name} WHERE {column_name} IS NOT NULL AND file_id = ? LIMIT 1", (file_id[0],))
                    if cursor.fetchone():
                        found_columns.append((column_name, table_name, sensor_number, file_id[0]))
            else:
                # Prüfen, ob der Wert in der Flusssignalspalte nicht NULL ist
                cursor.execute(f"SELECT 1 FROM {table_name} WHERE {column_name} IS NOT NULL LIMIT 1")
                if cursor.fetchone():
                    found_columns.append((column_name, table_name, sensor_number, None))

# Ergebnisse in ein DataFrame konvertieren
df = pd.DataFrame(found_columns, columns=['Channel.Name', 'Table.Name', 'SensorNumber', 'File.ID'])

# Sortiere das DataFrame nach der Sensornummer
df = df.sort_values(by='SensorNumber').reset_index(drop=True)

# Speichere das DataFrame als CSV-Datei
output_csv = '/Users/gian/Documents/bat_temp_test/db_lookup_table.csv'
df.to_csv(output_csv, index=False)

print(f"Gefundene Signale wurden in '{output_csv}' gespeichert.")

# Verbindung schließen
conn.close()