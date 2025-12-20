To implement a multi-player system, we need to add a secret_key so Flask can sign the cookies, and then use a uuid to create a unique prefix for each user's data in Redis.

Here is the updated code with the session system and English comments:

Python

import os
import uuid
import redis
from flask import Flask, render_template_string, request, redirect, url_for, session

app = Flask(__name__)

# --- CONFIGURATION ---
# SECRET_KEY is required to use sessions (cookies) in Flask.
# On Render, it's better to set this as an Environment Variable.
app.secret_key = os.environ.get("SECRET_KEY", "dev-key-for-local-testing")

# Redis connection
redis_url = os.environ.get("REDIS_URL")
# decode_responses=True ensures we get strings back from Redis instead of bytes
redis_client = redis.from_url(redis_url, decode_responses=True)

# --- RPG LEVELS CONFIGURATION ---
LEVELS = {
    0: {'multiplier': 1,  'cost': 200},
    1: {'multiplier': 5,  'cost': 500},
    2: {'multiplier': 10, 'cost': 1000},
    3: {'multiplier': 20, 'cost': None} # Max level reached
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>MegaClicker RPG</title>
    <style>
        body { font-family: 'Arial', sans-serif; text-align: center; margin: 0; padding: 0; background-color: #f4f4f9; }
        .main-container { display: flex; flex-direction: column; justify-content: center; align-items: center; height: 100vh; }
        h1 { font-size: 3rem; color: #333; }
        .score { font-size: 5rem; font-weight: bold; color: #007bff; margin: 20px 0; }
        .btn-click { padding: 20px 50px; font-size: 2rem; background-color: #28a745; color: white; border: none; border-radius: 10px; cursor: pointer; box-shadow: 0 5px #1e7e34; }
        .btn-click:active { box-shadow: 0 2px #1e7e34; transform: translateY(3px); }
        .upgrade-panel { position: absolute; top: 20px; right: 20px; background: white; padding: 20px; border: 2px solid #ccc; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); width: 250px; text-align: left; }
        .upgrade-info { margin-bottom: 10px; font-size: 0.9rem; color: #555; }
        .btn-upgrade { width: 100%; padding: 10px; background-color: #ffc107; border: none; border-radius: 5px; font-weight: bold; cursor: pointer; color: #333; }
        .btn-upgrade:disabled { background-color: #ddd; color: #999; cursor: not-allowed; }
        .user-id { position: absolute; bottom: 10px; left: 10px; font-size: 0.7rem; color: #aaa; }
    </style>
</head>
<body>
    <div class="user-id">Session ID: {{ user_id }}</div>

    <div class="upgrade-panel">
        <h3>RPG Shop</h3>
        <div class="upgrade-info">
            <strong>Current Level:</strong> {{ level }}<br>
            <strong>Multiplier:</strong> x{{ multiplier }}<br>
            {% if next_cost %}
                <strong>Next Upgrade:</strong> {{ next_cost }} clicks
            {% else %}
                <strong>Max Level Reached!</strong>
            {% endif %}
        </div>

        <form method="POST">
            {% if next_cost %}
                {% if count >= next_cost %}
                    <button class="btn-upgrade" name="upgrade">BUY UPGRADE ( -{{ next_cost }} )</button>
                {% else %}
                    <button class="btn-upgrade" disabled>Need {{ next_cost }} clicks</button>
                {% endif %}
            {% else %}
                <button class="btn-upgrade" disabled>MAX LEVEL</button>
            {% endif %}
        </form>
    </div>

    <div class="main-container">
        <h1>MegaClicker</h1>
        <div class="score">{{ count }}</div>
        <form method="POST">
            <button class="btn-click" name="click">CLICK!</button>
        </form>
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def home():
    # 1. Identify the user. If they don't have a session ID, generate a unique one.
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
    
    user_id = session['user_id']
    
    # 2. Define unique Redis keys for this specific user
    user_click_key = f"user:{user_id}:clicks"
    user_level_key = f"user:{user_id}:level"

    # 3. Fetch user data from Redis (defaulting to 0 if not found)
    current_count = int(redis_client.get(user_click_key) or 0)
    current_level = int(redis_client.get(user_level_key) or 0)

    # Calculate current level stats
    level_data = LEVELS.get(current_level, LEVELS[max(LEVELS.keys())])
    current_multiplier = level_data['multiplier']
    next_upgrade_cost = level_data['cost']

    if request.method == 'POST':
        # --- CLICK LOGIC ---
        if 'click' in request.form:
            redis_client.incrby(user_click_key, current_multiplier)
            return redirect(url_for('home'))

        # --- UPGRADE LOGIC ---
        elif 'upgrade' in request.form:
            if next_upgrade_cost is not None and current_count >= next_upgrade_cost:
                # Deduct cost and increment level for this user only
                redis_client.decrby(user_click_key, next_upgrade_cost)
                redis_client.incr(user_level_key)
                return redirect(url_for('home'))

    # 4. Render the page with the user's personal stats
    return render_template_string(HTML_TEMPLATE,
                                  user_id=user_id,
                                  count=current_count,
                                  multiplier=current_multiplier,
                                  level=current_level,
                                  next_cost=next_upgrade_cost)

if __name__ == '__main__':
    # Default port for local testing is 5000
    app.run(host='0.0.0.0', port=5000)
