import json
import os
import smtplib
from datetime import datetime

import pandas as pd
import pyodbc
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Border, Side, Font
from utils import write_log
from decimal import Decimal
from email.message import EmailMessage


def fetch_data_from_database(canevas, target, types, societe):
    result = {
        'status': 'error',
        'message': "Une erreur c'est produit !"
    }
    connection = None
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
        with connection.cursor() as cursor:
            cursor.execute(sql_query)
            rows = cursor.fetchall()
            if rows:
                rows = [tuple(row) for row in rows]
                if all(isinstance(row, tuple) for row in rows):
                    df = pd.DataFrame(rows, columns=columns)
                    df = df.apply(lambda x: float(x) if isinstance(x, Decimal) else x)
                    records = df.to_dict(orient='records')
                    result['status'] = 'success'
                    result['message'] = 'Donnée Générer avec Success !'
                    result['total'] = len(records)
                    result['records'] = records

        return result
    except FileNotFoundError:
        write_log("Fichier de configuration introuvable.")
        result['message'] = "Fichier de configuration introuvable."
    except KeyError as e:
        write_log(f"Clé manquante dans le fichier de configuration : {e}")
        result['message'] = f"Clé manquante dans le fichier de configuration : {e}"
    except pyodbc.Error as e:
        write_log(f"Erreur ODBC : {e}")
        result['message'] = "Erreur de Connexion à la base de donnée, verifier votre connexion internet !"
    except Exception as e:
        write_log(f"Erreur inattendue : {e}")
    finally:
        if connection:
            connection.close()
    return result


def export_data_in_config(societe, champs, target):
    file_path = None
    connection = None
    try:
        with open('config.json', 'r') as file:
            config_data = json.load(file)

        val = f"Driver={{ODBC Driver 17 for SQL Server}};Server={societe.connexion.server};" \
              f"Database={societe.base};UID={societe.connexion.login};PWD={societe.connexion.password}"

        connection = pyodbc.connect(val)
        with connection.cursor() as cursor:
            wb = Workbook()
            for champ in champs:
                try:
                    champ_id = str(champ['id'])
                    champ_text = champ['text']
                    columns = config_data['HEADER'][champ_id]
                    sql_query = (
                        str(config_data['SQL'][societe.type][champ_id])
                        .replace('{target}', target)
                        .replace('{value}', societe.value)
                        .replace('{base}', societe.base)
                        .replace('{table}', societe.table)
                    )
                    cursor.execute(sql_query)
                    rows = cursor.fetchall()

                    if rows:
                        rows = [tuple(row) for row in rows]
                        if all(isinstance(row, tuple) for row in rows):
                            df = pd.DataFrame(rows, columns=columns)
                            ws = wb.create_sheet(title=champ_text)
                            ws.append(columns)  # Add column headers
                            # Définir le style de l'entête
                            header_fill = PatternFill(start_color='0072BC', end_color='0072BC',
                                                      fill_type='solid')  # Bleu
                            header_font = Font(color='FFFFFF', bold=True)  # Blanc et gras
                            header_border = Border(left=Side(border_style='thin'), right=Side(border_style='thin'),
                                                   top=Side(border_style='thin'), bottom=Side(border_style='thin'))

                            for cell in ws[1]:  # Parcourir la première ligne (les entêtes)
                                cell.value = cell.value.replace('_', ' ')  # Remplacer '_' par un espace
                                cell.fill = header_fill  # Fond bleu
                                cell.font = header_font  # Texte blanc et gras
                                cell.border = header_border  # Bordure fine

                            for index, row in df.iterrows():
                                ws.append(row.tolist())

                            # Add "Total Général" row
                            total_row = [
                                sum(df[col].apply(lambda x: x if isinstance(x, (int, float, Decimal)) else 0))
                                for col in df.columns
                            ]
                            ws.append(['Total Général'] + [''] * (len(df.columns) - 1))  # Empty cells for other columns
                            for col, value in enumerate(total_row, start=1):
                                ws.cell(row=ws.max_row, column=col).value = value

                            ws.cell(row=ws.max_row, column=1).value = 'Total Général'

                            # Add "TOTAUX" row
                            total_fill = PatternFill(start_color='FFCCCB', end_color='FFCCCB',
                                                     fill_type='solid')  # Light red
                            total_font = Font(color='000000', bold=True)  # Black and bold
                            total_border = Border(left=Side(border_style='thin'), right=Side(border_style='thin'),
                                                  top=Side(border_style='thin'), bottom=Side(border_style='thin'))

                            for cell in ws[ws.max_row]:  # Last row (Total Général)
                                cell.fill = total_fill
                                cell.font = total_font
                                cell.border = total_border
                            for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=2, max_col=ws.max_column):
                                for cell in row:
                                    try:
                                        cell.number_format = '#,##0.00'
                                    except:
                                        pass

                            # Espacer les colonnes en fonction des données
                            for col in ws.columns:
                                max_length = 0
                                for cell in col:
                                    try:
                                        if len(str(cell.value)) > max_length:
                                            max_length = len(cell.value)
                                    except:
                                        pass
                                adjusted_width = (max_length + 2) * 1.2
                                ws.column_dimensions[col[0].column_letter].width = adjusted_width
                except:
                    pass

            # Create storage directory if it doesn't exist
            storage_dir = f'storage/{target}'
            if not os.path.exists(storage_dir):
                os.makedirs(storage_dir)

            file_path = f"{storage_dir}/{societe.name}.xlsx"
            wb.remove(wb['Sheet'])
            wb.save(file_path)
    except Exception as e:
        write_log(str(e))
        print("Une erreur c'est produite !")
    finally:
        if connection:
            connection.close()  # Fermer la connexion dans tous les cas (même en cas d'erreur)

    return file_path


def custom_send_email(target, recipient_email, copie_email, attachment_filename, message_text):
    result = {
        'status': 'error',
        'message': "Erreur de récupération du serveur du fichier !"
    }
    if attachment_filename:
        try:
            with open('config.json', 'r') as file:
                json_file = json.load(file)

            objet_text = json_file['CONFIGURATION']['OBJET']
            message_text = message_text + f"""\n\n
============= Mail Automatique ====================               
            www.inviso-group.com          
============= Sage X3 - {datetime.today().strftime('%d/%m/%Y %H:%M:%S')} ===================
"""

            message = EmailMessage()
            message["Subject"] = objet_text.replace("{target}", target)
            message["From"] = json_file['CONFIGURATION']['FROM']
            message["To"] = recipient_email
            message["Cc"] = copie_email
            message.set_content(message_text)

            if os.access(attachment_filename, os.R_OK):
                with open(attachment_filename, "rb") as file:
                    content = file.read()
                    attached_filename = os.path.basename(attachment_filename)
                    message.add_attachment(content, maintype="application", subtype="octet-stream",
                                           filename=attached_filename)
                smtp_conf = json_file['CONFIGURATION']
                with smtplib.SMTP(smtp_conf['HOST'], smtp_conf['PORT']) as server:
                    server.starttls()
                    server.login(smtp_conf['LOGIN'], smtp_conf['PASSWORD'])
                    server.send_message(message)
                    result['status'] = 'success'
                    result['message'] = "Email envoyé avec succès !"
            else:
                result['message'] = "Permission refusée pour accéder au fichier joint."

        except smtplib.SMTPException as e:
            write_log(str(e))
            result['message'] = "Erreur d'envoi de mail"
        except Exception as e:
            write_log(str(e))
            result['message'] = f"Une erreur d'envoi de mail : {str(e)}"
    return result
