import os
from flask import Flask, render_template_string, request, redirect, url_for
import redis

app = Flask(__name__)

# Подключение к Redis (замените параметры на свои при необходимости)
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# --- КОНФИГУРАЦИЯ УРОВНЕЙ ---
# Level 0: Старт (1 очко за клик). Чтобы перейти на след уровень, нужно заплатить 200.
# Level 1: (куплено за 200). Дает 5 очков. След цена: 500.
# Level 2: (куплено за 500). Дает 10 очков. След цена: 1000.
LEVELS = {
    0: {'multiplier': 1,  'cost': 200},
    1: {'multiplier': 5,  'cost': 500},
    2: {'multiplier': 10, 'cost': 1000},
    3: {'multiplier': 20, 'cost': None} # Максимальный уровень (цены нет)
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Clicker Upgrade</title>
    <style>
        body { font-family: 'Arial', sans-serif; text-align: center; margin: 0; padding: 0; background-color: #f4f4f9; }
        
        /* Основной контейнер по центру */
        .main-container {
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            height: 100vh;
        }

        h1 { font-size: 3rem; color: #333; }
        .score { font-size: 5rem; font-weight: bold; color: #007bff; margin: 20px 0; }
        
        .btn-click {
            padding: 20px 50px;
            font-size: 2rem;
            background-color: #28a745;
            color: white;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            box-shadow: 0 5px #1e7e34;
        }
        .btn-click:active { box-shadow: 0 2px #1e7e34; transform: translateY(3px); }

        /* --- БЛОК АПГРЕЙДА (СВЕРХУ СПРАВА) --- */
        .upgrade-panel {
            position: absolute;
            top: 20px;
            right: 20px;
            background: white;
            padding: 20px;
            border: 2px solid #ccc;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            width: 250px;
            text-align: left;
        }

        .upgrade-info { margin-bottom: 10px; font-size: 0.9rem; color: #555; }
        
        .btn-upgrade {
            width: 100%;
            padding: 10px;
            background-color: #ffc107;
            border: none;
            border-radius: 5px;
            font-weight: bold;
            cursor: pointer;
            color: #333;
        }
        .btn-upgrade:disabled { background-color: #ddd; color: #999; cursor: not-allowed; }
        .btn-upgrade:hover:not(:disabled) { background-color: #e0a800; }

    </style>
</head>
<body>

    <div class="upgrade-panel">
        <h3>Магазин</h3>
        <div class="upgrade-info">
            <strong>Текущий уровень:</strong> {{ level }}<br>
            <strong>Множитель:</strong> x{{ multiplier }}<br>
            {% if next_cost %}
                <strong>След. апгрейд:</strong> {{ next_cost }} кликов
            {% else %}
                <strong>Максимум достигнут!</strong>
            {% endif %}
        </div>

        <form method="POST">
            {% if next_cost %}
                {% if count >= next_cost %}
                    <button class="btn-upgrade" name="upgrade">
                        КУПИТЬ ( -{{ next_cost }} )
                    </button>
                {% else %}
                    <button class="btn-upgrade" disabled>
                        Нужно {{ next_cost }} кликов
                    </button>
                {% endif %}
            {% else %}
                <button class="btn-upgrade" disabled>MAX LEVEL</button>
            {% endif %}
        </form>
    </div>

    <div class="main-container">
        <h1>Кликер</h1>
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
    # 1. Получаем текущие данные из Redis
    # Если счетчика нет, будет 0
    current_count = int(redis_client.get('click_counter') or 0)
    # Текущий уровень апгрейда (0, 1, 2...)
    current_level = int(redis_client.get('upgrade_level') or 0)

    # Определяем параметры текущего уровня из словаря LEVELS
    # .get(..., LEVELS[max]) нужно на случай, если уровень выйдет за пределы словаря
    level_data = LEVELS.get(current_level, LEVELS[max(LEVELS.keys())])
    current_multiplier = level_data['multiplier']
    next_upgrade_cost = level_data['cost']

    if request.method == 'POST':
        # --- КЛИК ---
        if 'click' in request.form:
            redis_client.incrby('click_counter', current_multiplier)
            return redirect(url_for('home'))

        # --- АПГРЕЙД ---
        elif 'upgrade' in request.form:
            # Проверяем, есть ли цена (не макс уровень) и хватает ли денег
            if next_upgrade_cost is not None and current_count >= next_upgrade_cost:
                # 1. Списываем очки ("тратятся")
                redis_client.decrby('click_counter', next_upgrade_cost)
                # 2. Повышаем уровень
                redis_client.incr('upgrade_level')
                return redirect(url_for('home'))

    # 3. РЕНДЕРИНГ
    return render_template_string(HTML_TEMPLATE,
                                  count=current_count,
                                  multiplier=current_multiplier,
                                  level=current_level,
                                  next_cost=next_upgrade_cost)

if __name__ == '__main__':
    # Очистка базы при перезапуске (раскомментируйте, если хотите сбрасывать прогресс)
    # redis_client.flushall()
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
