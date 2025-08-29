# rmcs

Remote Monitoring Control Server for temporary events. This tool provides a simple web UI to register events and the devices used at each event. Device types contain Prometheus job configuration which is used to generate scrape configuration automatically.

## Running

```bash
pip install flask flask_sqlalchemy pyyaml
python app.py
```

Visit `http://localhost:5000` to create device types and events. Each event page contains a link to the generated Prometheus configuration.

## Tests

```bash
pip install pytest
pytest
```
