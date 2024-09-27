from asammdf import MDF
import csv

def extract_groups_and_signals_to_csv(mf4_file, csv_file):
    # Öffne die MF4-Datei
    mdf = MDF(mf4_file)
    
    # Liste aller Gruppen und Kanäle
    groups_and_signals = []

    # Iteriere durch alle Kanäle
    for channel in mdf.iter_channels():
        # Versuche, den Gruppennamen und den Kanalnamen zu extrahieren
        try:
            group_name = channel.source.name  # Holen des Gruppennamens (oft als Source bezeichnet)
            signal_name = channel.name        # Kanalname
            groups_and_signals.append([group_name, signal_name])
        except AttributeError as e:
            print(f"Error processing channel: {e}")

    # Schreibe die Daten in eine CSV-Datei
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Group Name", "Channel Name"])  # Kopfzeile
        writer.writerows(groups_and_signals)

    print(f"Groups and signals successfully extracted to {csv_file}")

# Beispielnutzung
mf4_file = 'TCP0014_Run1_01.mf4'  # Pfad zur MF4-Datei
csv_file = 'output_groups_signals.csv'  # Pfad zur CSV-Datei, die gespeichert wird
extract_groups_and_signals_to_csv(mf4_file, csv_file)