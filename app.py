from flask import Flask
from models import db
from config import Config, DockerConfig
from routes import bp
import os

app = Flask(__name__)

# Configuration selon l'environnement
if os.environ.get('DOCKER_ENV') == 'true':
    app.config.from_object(DockerConfig)
else:
    app.config.from_object(Config)

# Initialiser la base de données
db.init_app(app)

# Enregistrer le blueprint des routes
app.register_blueprint(bp)

# Créer les tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    debug = os.environ.get('FLASK_DEBUG', '1') in ('1', 'true', 'True')
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=debug)