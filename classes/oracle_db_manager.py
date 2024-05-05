import cx_Oracle
from classes.settings_manager import SettingsManager

class OracleDBManager:
    
    def __init__(self, hostname=None, port=None, service_name=None, username=None, password=None):
        # Utilizza i valori predefiniti dalle impostazioni se non vengono specificati esplicitamente
        self.hostname = hostname or SettingsManager.load_option('ORACLE_HOSTNAME')
        self.port = port or SettingsManager.load_option('ORACLE_PORT')
        self.service_name = service_name or SettingsManager.load_option('ORACLE_SERVICENAME')
        self.username = username or SettingsManager.load_option('ORACLE_USERNAME')
        self.password = password or SettingsManager.load_option('ORACLE_PASSWORD')
        self.connection = None
        self.cursor = None

    def add_or_update_f2a_record(self, email, secret_key, number):
        try:
            # Esegui una query per inserire o aggiornare un record nella tabella f2a
            query = f"MERGE INTO f2a USING DUAL ON (email = '{email}') \
                      WHEN MATCHED THEN UPDATE SET secret_key = '{secret_key}', number = '{number}' \
                      WHEN NOT MATCHED THEN INSERT (email, secret_key, number) VALUES ('{email}', '{secret_key}', '{number}')"
            
            self.cursor.execute(query)
            self.connection.commit()  # Committa le modifiche al database
            print("Record aggiunto o aggiornato con successo nella tabella f2a.")
        except cx_Oracle.DatabaseError as e:
            print("Errore durante l'aggiunta o l'aggiornamento del record nella tabella f2a:", e)

    def remove_f2a_record(self, email):
        try:
            # Esegui una query per rimuovere il record dalla tabella f2a
            query = f"DELETE FROM f2a WHERE email = '{email}'"
            self.cursor.execute(query)
            self.connection.commit()  # Committa le modifiche al database
            print("Record rimosso con successo dalla tabella f2a.")
        except cx_Oracle.DatabaseError as e:
            print("Errore durante la rimozione del record dalla tabella f2a:", e)

    def connect(self):
        try:
            # Creazione del DSN
            dsn_tns = cx_Oracle.makedsn(self.hostname, self.port, service_name=self.service_name)
            
            # Connessione al database
            self.connection = cx_Oracle.connect(user=self.username, password=self.password, dsn=dsn_tns)
            
            # Creazione del cursore
            self.cursor = self.connection.cursor()
            
            print("Connessione al database Oracle stabilita.")
        except cx_Oracle.DatabaseError as e:
            print("Errore durante la connessione al database Oracle:", e)

    def disconnect(self):
        try:
            # Chiusura del cursore e della connessione
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()
            
            print("Connessione al database Oracle chiusa.")
        except cx_Oracle.DatabaseError as e:
            print("Errore durante la disconnessione dal database Oracle:", e)

    def execute_query(self, query):
        try:
            # Esecuzione della query
            self.cursor.execute(query)
            
            # Recupero dei risultati
            rows = self.cursor.fetchall()
            
            return rows
        except cx_Oracle.DatabaseError as e:
            print("Errore durante l'esecuzione della query:", e)
            return None