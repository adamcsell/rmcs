import pytest
from app import app, db, DeviceType, Event, Device, build_prometheus_config

@pytest.fixture
def setup_app():
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['TESTING'] = True
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


def test_build_prometheus_config(setup_app):
    with setup_app.app_context():
        dt = DeviceType(name='Camera', job_name='camera', metrics_path='/metrics', port=9100)
        db.session.add(dt)
        event = Event(name='Test Event', date='2024-01-01')
        db.session.add(event)
        db.session.commit()
        device = Device(event_id=event.id, device_type_id=dt.id, ip_address='192.168.0.10')
        db.session.add(device)
        db.session.commit()
        config = build_prometheus_config(event)
        assert config['scrape_configs'][0]['job_name'] == 'camera'
        targets = config['scrape_configs'][0]['static_configs'][0]['targets']
        assert targets == ['192.168.0.10:9100']
