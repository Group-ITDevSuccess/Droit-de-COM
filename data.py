import json
import pandas as pd

import pyodbc

from utils import write_log


def fetch_data_from_database(canevas, target, server, base, username, password):
    try:
        # Charger le fichier de configuration JSON
        with open('config.json', 'r') as file:
            config_data = json.load(file)

        # Vérifier si l'item existe dans le fichier de configuration
        if canevas not in config_data:
            return {'error': 'Item not found in config file'}

        # Convertir la chaîne JSON en objet Python
        columns = config_data[canevas]['HEADER']
        print("COLUMNS", columns)

        sql_query = str(config_data[canevas]['SQL']).replace('{target}', target).replace('{base}', base)

        val = f"Driver={{ODBC Driver 17 for SQL Server}};Server={server};Database={base};UID={username};" \
              f"PWD={password}"
        connection = pyodbc.connect(val)
        result = []
        with connection.cursor() as cursor:
            cursor.execute(sql_query)
            rows = cursor.fetchall()
            if rows:
                rows = [tuple(row) for row in rows]
                if all(isinstance(row, tuple) for row in rows):
                    df = pd.DataFrame(rows, columns=columns)
                    result = df.to_dict(orient='records')

        return result
    except Exception as e:
        write_log(str(e))
        return []
