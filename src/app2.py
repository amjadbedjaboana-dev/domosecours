from flask import Flask, render_template, Response, request, redirect, url_for
from threading import Thread, Condition, Lock
import io
import time
from picamera2 import Picamera2
from picamera2.encoders import JpegEncoder
from picamera2.outputs import FileOutput

# Importation de votre classe AlphaBot2
# Assurez-vous que alphabot2.py est dans le même répertoire ou dans votre PYTHONPATH
from alphabot2 import AlphaBot2
import RPi.GPIO as GPIO # Ajout de l'import GPIO pour le nettoyage

app = Flask(__name__)

# --- Configuration et initialisation GPIO ---
# C'est crucial de définir le mode GPIO UNE SEULE FOIS au début
try:
    # Choisissez un mode de numérotation. GPIO.BCM est généralement préféré car il utilise la numérotation
    # des broches du processeur, ce qui correspond souvent mieux aux schémas.
    # Assurez-vous que votre classe AlphaBot2 utilise le même mode.
    GPIO.setmode(GPIO.BCM) # Ou GPIO.BOARD si votre AlphaBot2 l'exige
    print("Mode GPIO défini avec succès (GPIO.BCM).")
except Exception as e:
    print(f"!!! ERREUR LORS DE LA DÉFINITION DU MODE GPIO : {e}")
    print("Le programme peut ne pas fonctionner correctement sans un mode GPIO défini.")

# --- Initialisation AlphaBot2 ---
bot = None
bot_lock = None
try:
    print("Tentative d'initialisation d'AlphaBot2...")
    bot = AlphaBot2()
    bot_lock = Lock()
    print("AlphaBot2 initialisé avec succès.")
except Exception as e:
    print(f"!!! ERREUR LORS DE L'INITIALISATION D'ALPHABOT2 : {e}")
    print("Le contrôle du robot pourrait NE PAS fonctionner.")


# --- Caméra ---
picam2 = None
output = None

class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.condition = Condition()

    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()

try:
    print("Tentative d'initialisation de Picamera2...")
    picam2 = Picamera2()
    print("Picamera2 instance créée.")
    # Configuration pour la vidéo, taille 640x480
    picam2.configure(picam2.create_video_configuration(main={"size": (640, 480)}))
    print("Picamera2 configuration appliquée.")
    output = StreamingOutput()
    print("StreamingOutput créé.")
    # Démarre l'enregistrement en JPEG et le dirige vers notre objet StreamingOutput
    picam2.start_recording(JpegEncoder(), FileOutput(output))
    print("Picamera2 enregistrement démarré avec succès.")
except Exception as e:
    print(f"!!! ERREUR CRITIQUE lors de l'initialisation de Picamera2 : {e}")
    print("Le flux vidéo ne sera PAS disponible. Vérifiez si la caméra est déjà utilisée ou mal configurée.")
    picam2 = None # S'assurer que picam2 est None si l'initialisation échoue


def generate_frames():
    # Vérifier si picam2 ou output n'ont pas été initialisés en cas d'erreur au démarrage
    if not picam2 or not output:
        print("La caméra ou l'objet de sortie n'est pas prêt. Pas de flux vidéo.")
        return # Quitter la fonction si la caméra n'est pas disponible

    while True:
        with output.condition:
            # Attend qu'une nouvelle frame soit disponible
            output.condition.wait()
            frame = output.frame

        if frame: # S'assurer que la frame n'est pas None avant de l'envoyer
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        else:
            # Optionnel: petite pause pour éviter de consommer trop de CPU si des frames vides sont fréquentes
            time.sleep(0.05) # 50 ms de pause


# --- Trame (pour la réception d'informations depuis un client externe, ex: Arduino) ---
last_trame = ""
trame_lock = Lock() # Utilisation d'un verrou pour la synchronisation des accès à last_trame

# Route pour recevoir la trame (message d'urgence) depuis un client externe (ex: Arduino)
@app.route('/receive', methods=['POST'])
def receive_trame():
    global last_trame
    # Récupère la donnée 'message' du formulaire POST
    data = request.form.get('message')
    if data:
        with trame_lock: # Protège l'accès à last_trame
            last_trame = data
        print(f"✅ Information Client Urgent : '{last_trame}'")
        return "Message reçu", 200 # Réponse HTTP 200 OK
    print("⚠️ Reçu une requête /receive sans données 'message'.")
    return "Aucun message reçu", 400 # Réponse HTTP 400 Bad Request

# Route pour fournir la dernière trame reçue à la page web
@app.route('/last_trame_data')
def last_trame_data():
    with trame_lock: # Protège l'accès à last_trame
        return last_trame

# --- Routes Flask Générales ---

# Page de Login (page d'accueil par défaut)
@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Correction ici: Les noms des champs doivent correspondre aux attributs 'name' dans le HTML
        username = request.form.get('username') # Utiliser .get() pour éviter KeyError si le champ est absent
        password = request.form.get('password')

        print(f"Tentative de login pour utilisateur: '{username}'")
        # Vérification des identifiants (simulé ici)
        if username == "admin" and password == "password":
            print("Login réussi ! Redirection vers la page de la trame.")
            return redirect(url_for('trame_page'))
        else:
            print("Login échoué. Nom d'utilisateur ou mot de passe incorrect.")
            return render_template('login.html', error="Nom d'utilisateur ou mot de passe incorrect.")
    print("Affichage de la page de login.")
    return render_template('login.html')

# Page de la Trame (où les messages d'urgence sont affichés)
@app.route('/trame')
def trame_page():
    print("Accès à la page de la trame.")
    return render_template('trame.html') # trame.html doit avoir du JS pour récupérer /last_trame_data

# Page de Contrôle du Robot et du Flux Vidéo
@app.route('/controle')
def controle_page():
    print("Accès à la page de contrôle du robot.")
    # Passe une variable au template pour indiquer si la caméra est disponible
    if not picam2:
        print("La caméra n'est PAS disponible pour la page de contrôle.")
        return render_template('controle.html', camera_error="La caméra n'est pas disponible.")
    print("La caméra est disponible pour la page de contrôle.")
    return render_template('controle.html', camera_error=None)

# Route pour le flux vidéo (utilise les frames générées)
@app.route('/video_feed')
def video_feed():
    if not picam2:
        print("Requête /video_feed reçue, mais picam2 n'est pas initialisée.")
        # Retourne une réponse d'erreur si la caméra n'est pas prête
        return Response("La caméra n'est pas initialisée ou disponible.", status=503, mimetype='text/plain')
    print("Début du streaming vidéo...")
    # Retourne les frames en utilisant le format multipart/x-mixed-replace pour le streaming
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Contrôle du Robot (reçoit les commandes du front-end)
@app.route('/control/<command>', methods=['POST'])
def control_robot(command):
    print(f"Commande de robot reçue: '{command}'")
    if not bot:
        print("Le robot n'est PAS initialisé. Impossible d'exécuter la commande.")
        return "Robot non initialisé.", 503 # Service Unavailable

    with bot_lock: # Protège les appels au robot pour éviter les conflits
        if command == 'forward':
            bot.forward()
        elif command == 'backward':
            bot.backward()
        elif command == 'left':
            bot.left()
        elif command == 'right':
            bot.right()
        elif command == 'stop':
            bot.stop()
        else:
            print(f"Commande inconnue: '{command}'")
            return "Commande inconnue", 400 # Bad Request
    print(f"Commande '{command}' exécutée sur le robot.")
    return '', 204 # No Content (réponse sans contenu, succès)


# --- Lancement de l'application Flask et Nettoyage ---
if __name__ == '__main__':
    # Fonction de nettoyage pour s'assurer que les ressources sont libérées correctement
    def cleanup():
        print("\n--- Début du nettoyage de l'application ---")
        
        # Arrêt et fermeture de Picamera2
        if picam2:
            try:
                print("Arrêt de l'enregistrement Picamera2...")
                picam2.stop_recording()
                print("Fermeture de Picamera2...")
                picam2.close()
                print("Picamera2 arrêtée et fermée.")
            except Exception as e:
                print(f"Erreur lors de l'arrêt de Picamera2 : {e}")

        # Arrêt du robot AlphaBot2
        # Vérifie si 'bot' existe et s'il a une méthode 'stop' callable
        if bot and hasattr(bot, 'stop') and callable(getattr(bot, 'stop')):
            try:
                print("Arrêt du robot AlphaBot2...")
                bot.stop()
                print("Robot AlphaBot2 arrêté.")
            except Exception as e:
                print(f"Erreur lors de l'arrêt du robot : {e}")
        
        # Nettoyage des broches GPIO
        # C'est la dernière étape du nettoyage des GPIO car d'autres composants peuvent les utiliser
        if hasattr(GPIO, 'cleanup') and callable(getattr(GPIO, 'cleanup')):
            try:
                print("Nettoyage des broches GPIO...")
                GPIO.cleanup()
                print("GPIO nettoyés.")
            except Exception as e:
                print(f"Erreur lors du nettoyage des GPIO : {e}")
        print("--- Nettoyage terminé ---")

    # Utilisation d'un seul bloc try-finally pour s'assurer que cleanup() est toujours appelé
    try:
        # debug=True est utile pour le développement, mais use_reloader=False
        # est CRUCIAL ici pour éviter les appels multiples de cleanup()
        # et les conflits GPIO lors de l'arrêt ou du rechargement automatique.
        app.run(host='0.0.0.0', port=7123, debug=True, use_reloader=False)
    finally:
        # Ce bloc sera exécuté quand l'application Flask s'arrête (ex: CTRL+C)
        cleanup()