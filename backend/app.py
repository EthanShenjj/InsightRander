import os
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from models import db, ProductUpdate, CompetitiveLandscape, DataSourceHealth, TaskExecutionLog
from routes.api import api_bp
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Fix: Default to a local SQLite database if DATABASE_URL is not set
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL or DATABASE_URL.startswith('postgresql://user:password'):
    DATABASE_URL = 'sqlite:///insightradar_local.db'
    print(f"Warning: Falling back to local SQLite DB: {DATABASE_URL}")

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-insightradar')

db.init_app(app)

with app.app_context():
    try:
        db.create_all()
        # Seed initial competitors if table is empty
        if not CompetitiveLandscape.query.first():
            db.session.add_all([
                CompetitiveLandscape(name='PostHog', github_repo='PostHog/posthog', rss_url='https://posthog.com/rss.xml', changelog_url='https://posthog.com/changelog'),
                CompetitiveLandscape(name='Mixpanel', rss_url='https://mixpanel.com/blog/rss/', changelog_url='https://mixpanel.com/changelog/'),
                CompetitiveLandscape(name='Amplitude', rss_url='https://amplitude.com/blog/rss/', changelog_url='https://amplitude.com/changelog/')
            ])
            db.session.commit()
    except Exception as e:
        print(f"Error initializing database: {e}")

app.register_blueprint(api_bp, url_prefix='/api')

@app.route('/')
def serve_index():
    return send_from_directory('static', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    app.run(debug=True, port=5001)
