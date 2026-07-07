# domosecours
Système domotique robotisé d'assistance et de détection de chutes pour personnes âgées.

# Domo-Secours 🚑🤖

**Domo-Secours** est un système domotique connecté et robotisé d'assistance, conçu pour détecter les chutes des personnes âgées à leur domicile et alerter les secours ou les proches en temps réel.

Projet réalisé en équipe dans le cadre du BTS CIEL.

---

## 📋 Contexte et Problématique
Chaque année, on recense plus de 2 millions de chutes chez les personnes de plus de 65 ans. **Domo-Secours** automatise la chaîne d'alerte et permet une levée de doute visuelle immédiate par un téléopérateur grâce à un robot mobile télécommandé.

---

## 🛠️ Architecture Technologique
Le projet combine de l'informatique embarquée, du réseau et du développement web :
* **Matériel :** Raspberry Pi 4, Robot AlphaBot2, Caméra RPi (B), Arduino + Shield 4G, Accéléromètre portable.
* **Backend :** Serveur web applicatif sous **Flask (Python 3)**.
* **Base de données :** MariaDB / PhpMyAdmin pour la gestion des utilisateurs et l'historique des alertes.

---

## 💻 Ma Réalisation : Serveur Central & Téléprésence (Amjad)
J'ai conçu et développé l'intégralité de la logique serveur et l'IHM de contrôle du robot :

### 1. Serveur Web Applicatif (`app.py`)
* Implémentation d'un serveur **Flask** durci avec désactivation du recharger automatique (`use_reloader=False`) pour éviter les conflits d'accès aux broches matérielles.
* Gestion d'un système d'authentification sécurisé (Page de Login) pour les téléopérateurs.
* Création d'une API de routage pour intercepter les requêtes de contrôle en méthode `POST` (`/control/<command>`).

### 2. Vidéo Streaming Temps Réel & Multithreading
* Capture et encodage dynamique du flux vidéo de la caméra via la bibliothèque **Picamera2**.
* Utilisation d'un mécanisme de synchronisation par verrous (`threading.Lock` et `Condition`) pour diffuser le flux vidéo au format **MJPEG** via une réponse HTTP `multipart/x-mixed-replace`.
* Optimisation des performances pour permettre une visualisation fluide à distance sans recharger l'IHM.

### 3. Pilotage Robotique & Intégration Manette (Gamepad API)
* Développement de la classe de commande des moteurs (`alphabot2.py`) via la gestion des broches GPIO de la Raspberry Pi en mode BCM.
* Intégration de la **Gamepad API** en JavaScript (`controle.html`) : lecture des axes du stick de la manette, gestion d'un seuil de tolérance (`threshold = 0.4`) et filtrage des commandes pour piloter le robot à distance sans saturer le réseau.

---

## 📈 Compétences Techniques Validées
* **Langages :** Python 3, JavaScript (ES6), HTML5 / CSS3, SQL.
* **Réseau & Web :** Architecture REST, Protocoles HTTP (POST/GET), Streaming MJPEG, Sockets.
* **Système :** Gestion des broches GPIO, Multithreading et verrous de synchronisation.
* **Modélisation :** Diagrammes de séquence UML, Diagrammes de déploiement et Modèle Conceptuel de Données (MCD).
