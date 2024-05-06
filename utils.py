import uuid

import pyodbc
import os
import ldap3
import logging

from django.conf import settings
from ldap3.core.exceptions import LDAPException
from ldap3 import Server, Connection
from datetime import datetime

today = datetime.today().strftime('%d-%m-%Y')


def check_base(server, name, value, username, password):
    conn = None
    try:
        value_input = f"Driver={{ODBC Driver 17 for SQL Server}};Server={server};Database={value};UID={username};" \
                      f"PWD={password}"
        conn = pyodbc.connect(value_input)
    except pyodbc.Error as e:
        # Si une erreur se produit lors de la connexion, ajoutez le serveur à la liste des bases sans accès
        print("===============================")
        print(f"Erreur de Connexion pour {name} ")
        print("===============================")
        write_log(f"Erreur de connexion : {str(e)}")
    except Exception as e:
        write_log(f"Erreur Exception : {str(e)}")
    return conn


# Définition de la fonction pour rechercher les attributs LDAP d'un utilisateur
def ldap_search_attributes(conn, username):
    # Spécification de la base de recherche LDAP et du filtre de recherche
    search_base = settings.DN_LDAP
    # search_filter = f"(&(sAMAccountName={username}))"
    search_filter = f"(&(sAMAccountName={username}))"
    try:
        # Recherche des attributs spécifiés pour l'utilisateur donné
        conn.search(search_base, search_filter, attributes=['mail', 'sn', 'givenName'])

        # Vérification si des résultats ont été trouvés
        if len(conn.entries) > 0:
            entry = conn.entries[0]
            # write_log(f"Utilisateur Trouver : {entry}", level=logging.INFO)

            # Extraction des attributs si présents dans l'entrée LDAP
            email = entry.mail[0] if 'mail' in entry else None
            lastname = entry.sn[0] if 'sn' in entry else None
            firstname = entry.givenname[0] if 'givenName' in entry else None

            # Retourne un dictionnaire avec les attributs trouvés
            return {
                'email': email,
                'lastname': lastname,
                'firstname': firstname
            }
    except LDAPException as e:
        # Utilisation d'un système de journalisation pour enregistrer les erreurs
        write_log(f"Erreur de recherche LDAP : {str(e)}")
        return False


# Définition de la fonction pour la connexion LDAP
def ldap_login_connection(username, password):
    # Construction du DN de l'utilisateur
    user = f"SMTP-GROUP\\{username}".strip()
    # write_log(f"DN: {user}", level=logging.INFO)
    try:
        # Création de l'objet de serveur LDAP
        server = Server(settings.SERVER_LDAP, get_info=ldap3.ALL)

        # Connexion au serveur LDAP avec l'utilisateur et le mot de passe fournis
        with Connection(
                server=server,
                user=user,
                password=password,
                authentication=ldap3.SIMPLE,
                client_strategy=ldap3.SYNC) as conn:

            # Vérification de la liaison réussie (authentification)
            if not conn.bind():
                write_log("Bind Error !", level=logging.ERROR)
                return False
            write_log("Bind Successfully !", level=logging.INFO)
            # Appel de la fonction de recherche d'attributs LDAP pour l'utilisateur
            return ldap_search_attributes(conn, username)

    except LDAPException as e:
        # Utilisation d'un système de journalisation pour enregistrer les erreurs
        write_log(f"Erreur de connexion LDAP : {str(e)}")
        return False


def format_number(number):
    try:
        return '{:,.2f}'.format(float(number))
    except ValueError:
        return number  # Handle non-numeric values gracefully


def write_log(logs, level=None):
    log_file = os.path.join('logs', f'{today}.log')

    logging.basicConfig(filename=log_file, encoding='utf-8', level=level,
                        format='%(asctime)s - %(name)s - %(levelname)s : %(message)s')

    logger = logging.getLogger(__name__)

    if level == logging.ERROR:
        logger.error(logs)
    elif level == logging.INFO:
        logger.info(logs)
    elif level == logging.CRITICAL:
        logger.critical(logs)
    else:
        logger.exception(logs)


def are_valid_uuids(values):
    if values is not None:
        if isinstance(values, list):
            uuids = []

            for value in values:
                try:
                    uid = uuid.UUID(value)
                    uuids.append(uid)
                except ValueError:
                    return None

            return uuids
        else:
            try:
                uid = uuid.UUID(values)
                return uid
            except ValueError:
                return None
    return None
