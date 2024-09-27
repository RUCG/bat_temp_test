import sqlite3

# Connect to the SQLite database
db_path = "mf4_data.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# The file_id you want to delete
file_id_to_delete = 'TCP0014_Run11_01.MF4'

# Retrieve all table names from the database
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

# Iterate over each table and delete entries with the specified file_id
for table in tables:
    table_name = table[0]
    cursor.execute(f"DELETE FROM {table_name} WHERE file_id = ?", (file_id_to_delete,))
    print(f"Deleted entries with file_id '{file_id_to_delete}' from table '{table_name}'")

# Commit the changes and close the connection
conn.commit()
conn.close()

print(f"All entries with file_id '{file_id_to_delete}' have been deleted from the database.")