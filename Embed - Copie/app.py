from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import requests
from datetime import datetime
import os
import uuid
import logging

app = Flask(__name__)
app.config['SECRET_KEY'] = 'azertyuiopqsdfghjklmwxcvbn0123456789'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limite de 16 Mo pour les fichiers

db = SQLAlchemy(app)

# Configuration des journaux
logging.basicConfig(level=logging.DEBUG)

# Création du dossier de téléversement si nécessaire
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Définir les URLs de webhook Discord distinctes
ARRESTATION_WEBHOOK_URL = 'https://discord.com/api/webhooks/1263167971480698950/zV7CeugOQsCbOMHjtc-YEc3z83MOLKMI76b8FDIw1LxyQ8WYGOfoCosqoXnRXhQtMaG8'
RECENSEMENT_WEBHOOK_URL = 'https://discord.com/api/webhooks/1263549648878960751/dHas08qEcL_6NNgFp7p7Dz2DNRzT5YtGg4lhHxQ7iYfZ92CG59Q_NJMxhSDVY5Atppcd'

# Modèle de l'utilisateur
class Census(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prenom = db.Column(db.String(100))
    nom = db.Column(db.String(100))
    dob = db.Column(db.String(100))
    telephone = db.Column(db.String(100))
    type_ = db.Column(db.String(100))
    gender = db.Column(db.String(100))
    id_unique = db.Column(db.String(100))
    profession = db.Column(db.String(100))
    criminal_affiliation = db.Column(db.String(100))
    id_card_path = db.Column(db.String(200))
    driver_license_path = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Arrest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    suspect = db.Column(db.String(100))
    agents = db.Column(db.String(200))
    facts = db.Column(db.String(500))
    arrest_date = db.Column(db.String(100))
    gav = db.Column(db.String(10))
    seizures = db.Column(db.String(10))
    observations = db.Column(db.String(500))
    arrest_photo_path = db.Column(db.String(200))
    unique_url = db.Column(db.String(200), unique=True)  # Ajout de l'URL unique
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

def send_discord_notification(webhook_url, data, files=None):
    logging.debug(f"Envoi de la notification Discord : {data}")
    response = requests.post(webhook_url, json=data, files=files)
    logging.debug(f"Statut de la réponse Discord : {response.status_code}, Contenu : {response.content}")
    return response

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/arrestation')
def arrestation():
    return render_template('arrestation.html')

@app.route('/recensement')
def recensement():
    return render_template('recensement.html')

@app.route('/casier')
def casier():
    # Exemple de données pour le casier judiciaire
    civil_info = {
        'prenom': 'alvaro',
        'nom': 'mendoza',
        'age': 24,
        'telephone': '(000) 000-0000',
        'type': 'Afro Américain',
        'genre': 'Homme',
        'id_unique': 96
    }
    justice_info = {
        'date_effet': '25/05/2024 00:06',
        'decision': 'Délit de fuite - Excès de vitesse > 30 km/h - Conduite sans permis - Vente de drogue (flagrant délit) / 3800$ plus 15 min de GAV',
        'magistrats': '[procureur] Marcel DELADEVANTURE',
        'total_amendes': 3800,
        'total_gav': 35
    }
    arrestations = [
        {'date': '24/05/2024 23:47', 'agents': '[93] Andrew Walker', 'faits': 4, 'amendes': 3800}
    ]
    return render_template('casier.html', civil_info=civil_info, justice_info=justice_info, arrestations=arrestations)

@app.route('/annuaire')
def annuaire():
    users = Census.query.all()
    return render_template('annuaire.html', users=users)

@app.route('/submit_arrestation', methods=['POST'])
def submit_arrestation():
    try:
        suspect = request.form['suspect']
        agents = request.form['agents']
        facts = request.form['facts']
        arrest_date = request.form['arrest_date']
        gav = 'Oui' if 'gav' in request.form else 'Non'
        seizures = 'Oui' if 'seizures' in request.form else 'Non'
        observations = request.form['observations']

        # Gérer le fichier téléversé
        arrest_photo_file = request.files['arrest_photo']
        arrest_photo_path = None

        if arrest_photo_file:
            arrest_photo_path = os.path.join(app.config['UPLOAD_FOLDER'], arrest_photo_file.filename)
            arrest_photo_file.save(arrest_photo_path)

        # Générer un identifiant unique pour l'arrestation
        unique_url = str(uuid.uuid4())

        # Sauvegarder l'arrestation dans la base de données
        new_arrest = Arrest(
            suspect=suspect,
            agents=agents,
            facts=facts,
            arrest_date=arrest_date,
            gav=gav,
            seizures=seizures,
            observations=observations,
            arrest_photo_path=arrest_photo_path,
            unique_url=unique_url
        )
        db.session.add(new_arrest)
        db.session.commit()

        arrest_link = url_for('view_arrest', unique_url=unique_url, _external=True)

        data = {
            "embeds": [
                {
                    "title": "Nouvelle Demande d'Arrestation",
                    "fields": [
                        {"name": "Suspect", "value": suspect, "inline": False},
                        {"name": "Agents présents", "value": agents, "inline": False},
                        {"name": "Faits reprochés", "value": facts, "inline": False},
                        {"name": "Date de l'arrestation", "value": arrest_date, "inline": False},
                        {"name": "GAV", "value": gav, "inline": False},
                        {"name": "Saisies", "value": seizures, "inline": False},
                        {"name": "Observations", "value": observations, "inline": False},
                        {"name": "Lien vers l'arrestation", "value": arrest_link, "inline": False}
                    ],
                    "image": {
                        "url": f"attachment://{os.path.basename(arrest_photo_path)}" if arrest_photo_path else None
                    }
                }
            ]
        }

        files = {
            'file': (os.path.basename(arrest_photo_path), open(arrest_photo_path, 'rb'))
        } if arrest_photo_path else None

        response = send_discord_notification(ARRESTATION_WEBHOOK_URL, data, files)
        
        if response.status_code == 204:
            flash('Succès de l\'envoi!')
        else:
            flash('Échec de l\'envoi. Erreur: {}'.format(response.content))
    except Exception as e:
        flash(str(e))
    return redirect(url_for('arrestation'))

@app.route('/view_arrest/<unique_url>')
def view_arrest(unique_url):
    arrest = Arrest.query.filter_by(unique_url=unique_url).first_or_404()
    return render_template('view_arrest.html', arrest=arrest)

@app.route('/submit_rp', methods=['POST'])
def submit_rp():
    try:
        prenom = request.form['prenom']
        nom = request.form['nom']
        dob = request.form['dob']
        telephone = request.form['telephone']
        type_ = request.form['type']
        gender = request.form['gender']
        id_unique = request.form['id_unique']
        profession = request.form['profession']
        criminal_affiliation = request.form['criminal_affiliation']

        # Vérifier si une personne avec le même prénom et nom existe déjà
        existing_census = Census.query.filter_by(prenom=prenom, nom=nom).first()
        if existing_census:
            flash('Un recensement existe déjà pour cette personne.')
            return redirect(url_for('recensement'))

        # Gérer les fichiers téléversés
        id_card_file = request.files['id_card']
        driver_license_file = request.files['driver_license']

        id_card_path = None
        driver_license_path = None

        if id_card_file:
            id_card_path = os.path.join(app.config['UPLOAD_FOLDER'], id_card_file.filename)
            id_card_file.save(id_card_path)

        if driver_license_file:
            driver_license_path = os.path.join(app.config['UPLOAD_FOLDER'], driver_license_file.filename)
            driver_license_file.save(driver_license_path)

        # Créer une nouvelle entrée de recensement
        new_census = Census(
            prenom=prenom,
            nom=nom,
            dob=dob,
            telephone=telephone,
            type_=type_,
            gender=gender,
            id_unique=id_unique,
            profession=profession,
            criminal_affiliation=criminal_affiliation,
            id_card_path=id_card_path,
            driver_license_path=driver_license_path
        )
        db.session.add(new_census)
        db.session.commit()

        data = {
            "embeds": [
                {
                    "title": "Nouveau recensement!",
                    "fields": [
                        {"name": "Prénom RP", "value": prenom, "inline": False},
                        {"name": "Nom RP", "value": nom, "inline": False},
                        {"name": "Date de naissance", "value": dob, "inline": False},
                        {"name": "Numéro de téléphone RP", "value": telephone, "inline": False},
                        {"name": "Type", "value": type_, "inline": False},
                        {"name": "Genre", "value": gender, "inline": False},
                        {"name": "ID Unique", "value": id_unique, "inline": False},
                        {"name": "Profession", "value": profession, "inline": False},
                        {"name": "Appartenance criminelle", "value": criminal_affiliation, "inline": False},
                    ]
                }
            ]
        }

        response = send_discord_notification(RECENSEMENT_WEBHOOK_URL, data)

        if response.status_code == 204:
            flash('Inscription réussie!')
        else:
            flash('Échec de l\'inscription. Erreur: {}'.format(response.content))
    except Exception as e:
        flash(str(e))
    return redirect(url_for('recensement'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Créer les tables si elles n'existent pas
    app.run(debug=True)
