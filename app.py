from flask import Flask, request, render_template_string

app = Flask(__name__)

counter = 0

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Docker Clicker</title>
    <style>
        body { font-family: sans-serif; text-align: center; margin-top: 50px; }
        .count { font-size: 80px; font-weight: bold; color: #333; }
        button { padding: 20px 40px; font-size: 24px; cursor: pointer; background-color: #007bff; color: white; border: none; border-radius: 5px; }
        button:hover { background-color: #0056b3; }
    </style>
</head>
<body>
    <h1>Total Clicks</h1>
    <div class="count">{{ count }}</div>
    <br>
    <form method="POST">
        <button type="submit">CLICK!</button>
    </form>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def home():
    global counter
    if request.method == 'POST':
        counter += 1
    return render_template_string(HTML_TEMPLATE, count=counter)

if __name__ == '__main__':
    
    app.run(host='0.0.0.0', port=5000)

import os

if __name__ == '__main__':

    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
