from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import sqlite3
import json
from datetime import datetime
import re
import requests


app = Flask(__name__)
CORS(app)

# === DATABASE ===
def init_db():
    conn = sqlite3.connect('consultations.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS consultations
                 (id INTEGER PRIMARY KEY, 
                  symptoms TEXT, 
                  triage_level TEXT, 
                  recommendations TEXT, 
                  created_at TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

# === TRIAGE LOGIC ===
RED_FLAGS = {
    'сложность дыхания': {'keywords': ['не могу дышать', 'затруднение дыхания', 'одышка', 'асфиксия'], 'level': 'red'},
    'боль в груди': {'keywords': ['боль в груди', 'давит в груди', 'жжение в груди'], 'level': 'red'},
    'сознание': {'keywords': ['потеря сознания', 'обморок', 'теряю сознание'], 'level': 'red'},
    'кровотечение': {'keywords': ['кровь', 'кровотечение', 'кровохарканье', 'рвота кровью'], 'level': 'red'},
    'боль живот': {'keywords': ['острая боль в животе', 'невыносимая боль'], 'level': 'red'},
}

YELLOW_FLAGS = {
    'высокая температура': {'keywords': ['температура 39', 'температура 40', 'жар'], 'level': 'yellow'},
    'головокружение': {'keywords': ['головокружение', 'кружится голова', 'шатается'], 'level': 'yellow'},
    'сильная боль': {'keywords': ['сильная боль', 'нестерпимая боль'], 'level': 'yellow'},
    'рвота': {'keywords': ['рвота', 'тошнота и рвота', 'постоянная рвота'], 'level': 'yellow'},
    'слабость': {'keywords': ['сильная слабость', 'не могу встать'], 'level': 'yellow'},
}

RECOMMENDATIONS = {
    'red': {
        'action': '⚠️ ВЫЗОВИТЕ СКОРУЮ ПОМОЩЬ НЕМЕДЛЕННО',
        'steps': [
            '1. Вызовите 112 или скорую помощь',
            '2. Лягте, если возможно, в удобное положение',
            '3. Держите телефон под рукой',
            '4. Сообщите диспетчеру свой адрес и состояние',
        ],
        'doctor_questions': ['Когда начались симптомы?', 'Были ли травмы?', 'На какие лекарства аллергия?']
    },
    'yellow': {
        'action': '⚠️ Свяжитесь с врачом в течение дня',
        'steps': [
            '1. Позвоните своему врачу или в поликлинику',
            '2. Запишитесь на очный приём',
            '3. До приёма: пейте больше воды, отдыхайте',
            '4. Если симптомы ухудшатся — вызовите скорую',
        ],
        'doctor_questions': ['Когда начались симптомы?', 'Как изменялось состояние?', 'Были похожие ситуации?'],
        'exams': ['Анализ крови', 'Консультация врача']
    },
    'green': {
        'action': '✓ Вероятно, ничего серьезного. Самопомощь дома.',
        'steps': [
            '1. Отдыхайте достаточно',
            '2. Пейте много воды и теплые напитки',
            '3. Избегайте переохлаждения и перегрева',
            '4. Если в течение 3-5 дней не лучше — обратитесь к врачу',
        ],
        'doctor_questions': ['Как долго это длится?', 'Что помогало раньше?'],
        'home_care': ['Отдых', 'Гидратация', 'Питание', 'Теплые компрессы']
    }
}

CLARIFYING_QUESTIONS = {
    'symptom': [
        'Когда это началось?',
        'Боль острая или ноющая?',
        'Температура есть?',
        'Уже давали что-то из лекарств?',
        'Была ли травма или падение?',
    ]
}

def analyze_symptoms(text):
    """Анализ симптомов с помощью локальной Llama 3 / Gemma через Ollama"""
    
    # Промпт (системная инструкция) для модели
    prompt = f"""
    Ты - опытный медицинский triage-ассистент. 
    Твоя задача оценить симптомы пациента и присвоить им уровень опасности:
    - RED (экстренно: угроза жизни, сильная боль в груди, удушье, кровотечение, потеря сознания)
    - YELLOW (срочно: высокая температура, сильная боль, рвота, головокружение)
    - GREEN (самопомощь: легкая простуда, легкая боль, насморк)
    
    Симптомы пациента: "{text}"
    
    В ответе напиши ТОЛЬКО ОДНО СЛОВО на английском: red, yellow или green. Больше ничего.
    """

    try:
        response = requests.post('http://localhost:11434/api/generate', json={
            "model": "llama3", # Замените на "gemma", если скачали её
            "prompt": prompt,
            "stream": False
        })
        
        if response.status_code == 200:
            result = response.json()['response'].strip().lower()
            
            # Проверяем, что ИИ ответил правильно
            if 'red' in result:
                return 'red'
            elif 'yellow' in result:
                return 'yellow'
            elif 'green' in result:
                return 'green'
            else:
                # Fallback: если ИИ сглючил, лучше отправить к врачу (yellow)
                return 'yellow'
        else:
            print("Ошибка Ollama API")
            return 'yellow'
            
    except Exception as e:
        print(f"Ошибка подключения к локальному ИИ: {e}")
        return 'yellow' # Безопасный дефолт при падении ИИ

# === API ENDPOINTS ===
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '').strip()
    
    if not user_message:
        return jsonify({'error': 'Сообщение не может быть пустым'}), 400
    
    # Анализ симптомов
    triage_level = analyze_symptoms(user_message)
    
    # Получение рекомендаций
    recs = RECOMMENDATIONS.get(triage_level, RECOMMENDATIONS['green'])
    
    # Сохранение в БД
    conn = sqlite3.connect('consultations.db')
    c = conn.cursor()
    c.execute('INSERT INTO consultations (symptoms, triage_level, recommendations, created_at) VALUES (?, ?, ?, ?)',
              (user_message, triage_level, json.dumps(recs), datetime.now()))
    conn.commit()
    conn.close()
    
    # Следующий вопрос
    next_question = CLARIFYING_QUESTIONS['symptom'][0] if triage_level != 'red' else None
    
    response = {
        'triage_level': triage_level,
        'action': recs['action'],
        'steps': recs['steps'],
        'doctor_questions': recs.get('doctor_questions', []),
        'next_question': next_question,
    }
    
    if triage_level == 'green' and 'home_care' in recs:
        response['home_care'] = recs['home_care']
    
    return jsonify(response)

@app.route('/api/history', methods=['GET'])
def history():
    conn = sqlite3.connect('consultations.db')
    c = conn.cursor()
    c.execute('SELECT * FROM consultations ORDER BY created_at DESC LIMIT 10')
    consultations = c.fetchall()
    conn.close()
    
    result = []
    for row in consultations:
        result.append({
            'id': row[0],
            'symptoms': row[1],
            'triage_level': row[2],
            'created_at': row[4]
        })
    
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)