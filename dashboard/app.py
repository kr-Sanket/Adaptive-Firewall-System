import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
import time
from flask import Flask, render_template, Response, jsonify
from simulation import SimulationEngine

# Fix paths
DASHBOARD_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(DASHBOARD_DIR)

app = Flask(__name__,
            template_folder=os.path.join(ROOT_DIR, 'templates'),
            static_folder=os.path.join(DASHBOARD_DIR, 'static'))

sim = SimulationEngine()
simulation_speed = 0.8


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/stream')
def stream():
    def event_stream():
        global simulation_speed
        while True:
            data = sim.step_simulation()
            yield f"data: {json.dumps(data)}\n\n"
            time.sleep(simulation_speed)

    return Response(event_stream(), mimetype='text/event-stream')


@app.route('/reset', methods=['POST'])
def reset():
    global sim
    sim = SimulationEngine()
    return jsonify({"status": "reset"})


@app.route('/speed/<float:val>', methods=['POST'])
def set_speed(val):
    global simulation_speed
    simulation_speed = max(0.1, min(2.0, val))
    return jsonify({"speed": simulation_speed})


@app.route('/inject/<attacker_id>/<attack_type>', methods=['POST'])
def inject_attack(attacker_id, attack_type):
    result = sim.inject_attack(attacker_id, attack_type)
    return jsonify(result)

@app.route('/pause', methods=['POST'])
def pause():
    global simulation_speed
    simulation_speed = 999  # effectively paused
    return jsonify({"status": "paused"})

@app.route('/resume', methods=['POST'])
def resume():
    global simulation_speed
    simulation_speed = 0.8
    return jsonify({"status": "resumed"})

if __name__ == '__main__':
    app.run(debug=False, threaded=True)