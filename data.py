import json
import pandas as pd
import pyodbc

from utils import write_log
from decimal import Decimal


def fetch_data_from_database(canevas, target, types, societe):
    try:
        # Charger le fichier de configuration JSON
        with open('config.json', 'r') as file:
            config_data = json.load(file)

        # Convertir la chaîne JSON en objet Python
        columns = config_data['HEADER'][canevas]

        sql_query = (str(config_data['SQL'][types][canevas])
                     .replace('{target}', target)
                     .replace('{value}', societe.value)
                     .replace('{base}', societe.base)
                     .replace('{table}', societe.table)
                     )

        val = f"Driver={{ODBC Driver 17 for SQL Server}};Server={societe.connexion.server};" \
              f"Database={societe.base};UID={societe.connexion.login};PWD={societe.connexion.password}"
        connection = pyodbc.connect(val)
        result = []
        with connection.cursor() as cursor:
            cursor.execute(sql_query)
            rows = cursor.fetchall()
            if rows:
                rows = [tuple(row) for row in rows]
                if all(isinstance(row, tuple) for row in rows):
                    df = pd.DataFrame(rows, columns=columns)
                    df = df.applymap(lambda x: float(x) if isinstance(x, Decimal) else x)
                    result = df.to_dict(orient='records')
        return result
    except FileNotFoundError:
        write_log("Fichier de configuration introuvable.")
        return []
    except KeyError as e:
        write_log(f"Clé manquante dans le fichier de configuration : {e}")
        return []
    except pyodbc.Error as e:
        write_log(f"Erreur ODBC : {e}")
        return []
    except Exception as e:
        write_log(f"Erreur inattendue : {e}")
        return []
