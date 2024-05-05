from flask import Flask, request, jsonify
from twilio.rest import Client
import os
import json
import pyotp

from classes.settings_manager import SettingsManager
from classes.oracle_db_manager import OracleDBManager


'''
DA AGGIUNGERE:
- INVIO VIA MAIL DELL'OTP
- CONNESSIONE A DATABASE ORACLE

Esempio di utilizzo della classe OracleDBManager

    # Creazione di un'istanza del gestore del database Oracle
    db_manager = OracleDBManager()

    # Connessione al database
    db_manager.connect()

    # Esempio di esecuzione di una query
    query = "SELECT * FROM your_table"
    rows = db_manager.execute_query(query)
    if rows:
        for row in rows:
            print(row)

    # Disconnessione dal database
    db_manager.disconnect()    

'''


app = Flask(__name__)

# Funzione per caricare i secret key degli utenti dal file
def load_users_secret():
    USERS_SECRET_FILE = SettingsManager.load_option('USERS_SECRET_FILE')
    if os.path.exists(USERS_SECRET_FILE):
        with open(USERS_SECRET_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.decoder.JSONDecodeError:
                # Se il file è vuoto o non è JSON valido, restituisci un dizionario vuoto
                return {}
    else:
        return {}
    
# Funzione per salvare i secret key degli utenti nel file
def save_users_secret(users_secret):
    USERS_SECRET_FILE = SettingsManager.load_option('USERS_SECRET_FILE')
    with open(USERS_SECRET_FILE, 'w') as f:
        json.dump(users_secret, f)

# Funzione per generare un secret key per l'autenticazione con Google Authenticator
def generate_secret_key():
    return pyotp.random_base32()

''' ROUTES '''
# Endpoint per la registrazione dell'utente
@app.route('/register', methods=['POST'])
def register():
    # Ottieni i dati dal body della richiesta
    data = request.get_json()
    email = data.get('email')
    number = data.get('number')

    if not email:
        return jsonify({'error': 'Il parametro "email" è mancante nella richiesta'}), 400
    
    if not number:
        return jsonify({'error': 'Il parametro "number" è mancante nella richiesta'}), 400
    

    # Carica i secret key degli utenti dal file
    users_secret = load_users_secret()

    # Genera un secret key per l'utente
    secret_key = generate_secret_key()

    # Salva il secret key dell'utente nel file
    users_secret[email] = {'secret_key': secret_key, 'number': number}
    save_users_secret(users_secret)

    # Crea un'istanza di GoogleAuthenticator per generare l'URL
    ga = pyotp.totp.TOTP(secret_key)

    # Genera l'URL per l'autenticazione con Google Authenticator
    auth_url = ga.provisioning_uri(email, issuer_name='2FA Auth')

    # Costruisci l'URL del codice QR
    qr_code_url = f'https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={auth_url}'

    # Costruisci la risposta JSON
    response_data = {
        'email': email,
        'number': number,
        'secret_key': secret_key,
        'auth_url': auth_url,
        'qrcode_url': qr_code_url
    }

    # Ritorna la risposta JSON
    return jsonify(response_data), 200

# Endpoint per la registrazione dell'utente
@app.route('/unregister', methods=['POST'])
def unregister():
    # Ottieni i dati dal body della richiesta
    data = request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({'error': 'Il parametro "email" è mancante nella richiesta'}), 400    

    # Carica i secret key degli utenti dal file
    users_secret = load_users_secret()

    if email not in users_secret:
        return jsonify({'error': 'Questa mail non è registrata per 2FA'}), 400

    # Rimuovi l'email dal dizionario
    del users_secret[email]
    save_users_secret(users_secret)

    # Ritorna la risposta JSON
    return jsonify({'message': 'Email rimossa da F2A'}), 200

# Endpoint per il login dell'utente
@app.route('/login', methods=['POST'])
def login():
    # Ottieni i dati dal body della richiesta
    data = request.get_json()
    email = data.get('email')
    otp_code = data.get('otp_code')

    if not email:
        return jsonify({'error': 'Il parametro "email" è mancante nella richiesta'}), 400

    users_secret = load_users_secret()
    if email not in users_secret:
        return jsonify({'error': 'Questa mail non è registrata per 2FA'}), 400
    
    # Carica i secret key degli utenti dal file        
    secret_key = users_secret[email]['secret_key']

    current_otp = pyotp.totp.TOTP(secret_key)

    # Verifica il codice OTP inserito dall'utente
    if current_otp.verify(otp_code):
        # Autenticazione riuscita
        return jsonify({'message': 'Autenticazione riuscita!'}), 200
    else:
        # Autenticazione fallita
        return jsonify({'message': 'Autenticazione fallita. Codice OTP non più valido.'}), 401

# Endpoint per invio sms
@app.route('/sms', methods=['POST'])
def sms():
    # Ottieni i dati dal body della richiesta
    data = request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({'error': 'Il parametro "email" è mancante nella richiesta'}), 400

    users_secret = load_users_secret()
    if email not in users_secret:
        return jsonify({'error': 'Questa mail non è registrata per 2FA'}), 400
    
    # Carica i secret key degli utenti dal file        
    secret_key = users_secret[email]['secret_key']
    user_number = users_secret[email]['number']

    # Twilio settings    
    client = Client(SettingsManager.load_option('TWILIO_ACCOUNT_SID'), SettingsManager.load_option('TWILIO_AUTH_TOKEN'))

    totp = pyotp.TOTP(secret_key)

    message = client.messages.create(
        from_ = SettingsManager.load_option('TWILIO_NUMBER'),
        to=user_number,
        body=f'Il tuo codice OTP è {totp.now()}'
    )
    
    return jsonify({'message': 'Sms inviato correttamente'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)