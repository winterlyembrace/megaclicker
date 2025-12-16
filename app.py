HTML_TEMPLATE = """
<!doctype html>
<head>
    <title>Clicks Counter</title>
    <style>
        /* Стили для центрирования всего содержимого */
        body {
            display: flex;
            flex-direction: column;
            align-items: center; /* Центрирование по горизонтали */
            justify-content: center; /* Центрирование по вертикали */
            min-height: 100vh; /* Занимает всю высоту viewport */
            margin: 0;
            font-family: Arial, sans-serif;
            text-align: center;
        }
        
        /* Стили для основного контейнера, чтобы расположить элементы рядом */
        .main-container {
            display: flex;
            align-items: center;
            gap: 50px; /* Расстояние между элементами */
        }
        
        /* Увеличение заголовка */
        h1 {
            font-size: 2.5em;
        }
        
        /* Увеличение и выделение счетчика */
        .count {
            font-size: 5em;
            font-weight: bold;
            color: #333;
        }
        
        /* Стили для кнопки CLICK */
        .click-button {
            padding: 20px 40px;
            font-size: 1.8em;
            cursor: pointer;
            border: none;
            border-radius: 10px;
            color: white;
            background-color: #28a745; /* Зеленый цвет */
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transition: background-color 0.3s;
        }
        
        .click-button:hover {
            background-color: #218838;
        }

        /* Стили для надписи апгрейда */
        .upgrade-status {
            font-size: 1.2em;
            color: #555;
            min-width: 250px; /* Чтобы не скакало при появлении кнопки */
            text-align: left;
        }

        /* Стили для кнопки UPGRADE */
        .upgrade-button {
            padding: 10px 20px;
            font-size: 1.2em;
            cursor: pointer;
            border: none;
            border-radius: 5px;
            color: white;
            background-color: #dc3545; /* Красный цвет */
            transition: opacity 0.3s;
            margin-top: 10px;
        }
    </style>
</head>
<body>
    <h1>Total Clicks (x{{ multiplier }})</h1>
    <div class="main-container">
        
        <div class="count">{{ count }}</div>
        
        <form method="POST">
            <button type="submit" name="click" class="click-button">CLICK!</button>
        </form>
        
        <div class="upgrade-status">
            {% if multiplier > 1 %}
                <p style="color: green; font-weight: bold;">UPGRADED! Clicks per action: {{ multiplier }}</p>
            {% else %}
                <p>Get {{ upgrade_threshold - count }} more clicks to upgrade.</p>
                {% if upgrade_available %}
                    <form method="POST">
                        <button type="submit" name="upgrade" class="upgrade-button">UPGRADE!</button>
                    </form>
                {% else %}
                    <p style="color: #999;">Requires {{ upgrade_threshold }} clicks.</p>
                {% endif %}
            {% endif %}
        </div>
        
    </div>
</body>
</html>
"""

from flask import Flask, request, render_template_string, redirect, url_for
import redis
import os

app = Flask(__name__)

# --- Константы игры ---
UPGRADE_THRESHOLD = 200  # Порог для получения апгрейда
INITIAL_MULTIPLIER = 1   # Начальный множитель
UPGRADED_MULTIPLIER = 5  # Множитель после апгрейда

# Подключение к Redis (имя хоста 'redis' берется из docker-compose.yml)
try:
    redis_client = redis.Redis(host='redis', port=6379, db=0)
    redis_client.ping()
except Exception as e:
    print(f"Ошибка подключения к Redis: {e}")
    # В продакшене лучше предусмотреть резервное поведение

# --- 💡 ФУНКЦИЯ ДЛЯ ЧТЕНИЯ/ЗАПИСИ МНОЖИТЕЛЯ ---
def get_or_set_multiplier(current_count):
    # 1. Сначала пытаемся прочитать текущий множитель из Redis
    multiplier_bytes = redis_client.get('click_multiplier')
    
    if multiplier_bytes is None:
        # 2. Если множителя нет, устанавливаем его
        if current_count >= UPGRADE_THRESHOLD:
            multiplier = UPGRADED_MULTIPLIER
        else:
            multiplier = INITIAL_MULTIPLIER
            
        # Записываем его обратно в Redis для сохранения
        redis_client.set('click_multiplier', multiplier)
        return multiplier
    else:
        # 3. Если множитель уже есть, просто возвращаем его
        return int(multiplier_bytes.decode('utf-8'))

# --- ОСНОВНАЯ ЛОГИКА ---
@app.route('/', methods=['GET', 'POST'])
def home():
    
    # 1. ПОЛУЧЕНИЕ ДАННЫХ
    try:
        count_bytes = redis_client.get('click_counter')
    except Exception:
        count_bytes = None

    current_count = int(count_bytes.decode('utf-8')) if count_bytes else 0
    current_multiplier = get_or_set_multiplier(current_count) # Получаем множитель

    # 2. ОБРАБОТКА POST-ЗАПРОСА (КЛИК)
    if request.method == 'POST':
        # Если нажата кнопка "CLICK!"
        if 'click' in request.form:
            # Используем текущий множитель для увеличения счетчика
            redis_client.incrby('click_counter', current_multiplier)
            return redirect(url_for('home')) # Перенаправляем, чтобы избежать повторных кликов при обновлении
        
        # Если нажата кнопка "UPGRADE"
        elif 'upgrade' in request.form:
            # Если апгрейд доступен и множитель еще не повышен
            if current_count >= UPGRADE_THRESHOLD and current_multiplier == INITIAL_MULTIPLIER:
                # Устанавливаем новый множитель и сохраняем его в Redis
                redis_client.set('click_multiplier', UPGRADED_MULTIPLIER)
                return redirect(url_for('home'))

    # 3. ЛОГИКА ОТОБРАЖЕНИЯ
    # Определяем состояние апгрейда
    upgrade_available = current_count >= UPGRADE_THRESHOLD and current_multiplier == INITIAL_MULTIPLIER
    
    return render_template_string(HTML_TEMPLATE, 
                                  count=current_count,
                                  multiplier=current_multiplier,
                                  upgrade_threshold=UPGRADE_THRESHOLD,
                                  upgrade_available=upgrade_available)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
