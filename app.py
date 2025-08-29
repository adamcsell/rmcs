from flask import Flask, render_template, request, redirect, url_for, Response
from flask_sqlalchemy import SQLAlchemy
import yaml

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///rmcs.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class DeviceType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    job_name = db.Column(db.String(64), nullable=False)
    metrics_path = db.Column(db.String(128), default='/metrics')
    port = db.Column(db.Integer, default=9100)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    date = db.Column(db.String(64))

class Device(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    device_type_id = db.Column(db.Integer, db.ForeignKey('device_type.id'), nullable=False)
    ip_address = db.Column(db.String(64), nullable=False)

    event = db.relationship('Event', backref=db.backref('devices', lazy=True))
    device_type = db.relationship('DeviceType')

def build_prometheus_config(event):
    jobs = []
    for dt in DeviceType.query.all():
        devices = [d for d in event.devices if d.device_type_id == dt.id]
        if not devices:
            continue
        targets = [f"{d.ip_address}:{dt.port}" for d in devices]
        job = {
            'job_name': dt.job_name,
            'metrics_path': dt.metrics_path,
            'static_configs': [
                {'targets': targets}
            ]
        }
        jobs.append(job)
    return {'scrape_configs': jobs}

@app.route('/')
def index():
    events = Event.query.all()
    return render_template('index.html', events=events)

@app.route('/device-types')
def list_device_types():
    types = DeviceType.query.all()
    return render_template('device_types.html', types=types)

@app.route('/device-types/new', methods=['GET', 'POST'])
def new_device_type():
    if request.method == 'POST':
        name = request.form['name']
        job_name = request.form['job_name']
        metrics_path = request.form.get('metrics_path') or '/metrics'
        port = int(request.form.get('port') or 9100)
        dt = DeviceType(name=name, job_name=job_name, metrics_path=metrics_path, port=port)
        db.session.add(dt)
        db.session.commit()
        return redirect(url_for('list_device_types'))
    return render_template('device_type_form.html')

@app.route('/device-types/<int:type_id>/edit', methods=['GET', 'POST'])
def edit_device_type(type_id):
    dt = DeviceType.query.get_or_404(type_id)
    if request.method == 'POST':
        dt.name = request.form['name']
        dt.job_name = request.form['job_name']
        dt.metrics_path = request.form.get('metrics_path') or '/metrics'
        dt.port = int(request.form.get('port') or 9100)
        db.session.commit()
        return redirect(url_for('list_device_types'))
    return render_template('device_type_form.html', device_type=dt)

@app.route('/events/new', methods=['GET', 'POST'])
def new_event():
    if request.method == 'POST':
        name = request.form['name']
        date = request.form['date']
        event = Event(name=name, date=date)
        db.session.add(event)
        db.session.commit()
        return redirect(url_for('event_detail', event_id=event.id))
    return render_template('event_form.html')

@app.route('/events/<int:event_id>')
def event_detail(event_id):
    event = Event.query.get_or_404(event_id)
    types = DeviceType.query.all()
    return render_template('event_detail.html', event=event, types=types)

@app.route('/events/<int:event_id>/add_device', methods=['POST'])
def add_device(event_id):
    event = Event.query.get_or_404(event_id)
    ip = request.form['ip_address']
    device_type_id = int(request.form['device_type_id'])
    device = Device(event=event, ip_address=ip, device_type_id=device_type_id)
    db.session.add(device)
    db.session.commit()
    return redirect(url_for('event_detail', event_id=event.id))

@app.route('/events/<int:event_id>/prometheus_config')
def prometheus_config(event_id):
    event = Event.query.get_or_404(event_id)
    config = build_prometheus_config(event)
    yaml_str = yaml.dump(config)
    return Response(yaml_str, mimetype='text/plain')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
