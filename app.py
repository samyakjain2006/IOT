from flask import Flask, request, jsonify, render_template_string,render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
from pyngrok import ngrok
from threading import Thread
import os
import smtplib 
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL',"sqlite:///site.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)
app.config['secret_key'] = 'niggaballs'

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

class IOT(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    thing_id = db.Column(db.Integer, nullable=False)
    property_name = db.Column(db.String(100), nullable=False)
    value = db.Column(db.Integer, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)


@app.route("/")
def home():
    return render_template("index.html")
    
@app.route('/logs-data')
def logs_data():
    """API endpoint for radar to get latest logs as JSON"""
    all_logs = IOT.query.order_by(IOT.id.desc()).limit(10).all()
    logs_list = []
    for log in all_logs:
        logs_list.append({
            'id': log.id,
            'thing_id': log.thing_id,
            'property_name': log.property_name,
            'value': log.value,
            'updated_at': log.updated_at.isoformat() if log.updated_at else None
        })
    return jsonify(logs_list)

@app.route('/arduino-webhook', methods=['POST'])
def arduino_webhook():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON received"}), 400
    try:
        new_log = IOT(
            thing_id=int(data.get('thing_id', 0)),
            property_name=data.get('property_name', 'ultrasonic'),
            value=int(data.get('value', 0))
        )
        db.session.add(new_log)
        db.session.commit()
        
        return jsonify({"status": "success"}), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/deletelogs/<int:id>")
def deletelogs(id):
    log = IOT.query.filter_by(id=id).first()
    db.session.delete(log)
    db.session.commit()


@app.route("/logs")
def logs():
    all_logs = IOT.query.order_by(IOT.id.desc()).all()
    return render_template("logs.html",logs=all_logs)
 

def start_ngrok():
    public_url = ngrok.connect(5000)
    print(f"\n\nPublic URL (give this to your friend): {public_url}/arduino-webhook\n\n")

if __name__ == "__main__":
    Thread(target=start_ngrok, daemon=True).start()
    app.run(port=5000)
