// ===== UI ELEMENTS =====
const chatBox = document.getElementById('chat-box');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const emergencyBtn = document.getElementById('emergency-btn');
const resultsPanel = document.getElementById('results-panel');
const triageIndicator = document.getElementById('triage-indicator');
const recommendationsDiv = document.getElementById('recommendations');
const historyList = document.getElementById('history-list');

// Make functions global
window.sendMessage = sendMessage;
window.quickSymptom = quickSymptom;
window.emergency = emergency;
window.resetChat = resetChat;

// ===== SEND MESSAGE =====
function sendMessage() {
    const text = userInput.value.trim();
    if (!text) return;

    addMessageToChat('user', text);
    userInput.value = '';
    sendBtn.disabled = true;

    fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text })
    })
    .then(res => res.json())
    .then(data => {
        displayTriageResult(data);
        loadHistory();
    })
    .catch(err => {
        console.error('Error:', err);
        addMessageToChat('system', '❌ Ошибка при обработке.');
    })
    .finally(() => {
        sendBtn.disabled = false;
        userInput.focus();
    });
}

// ===== QUICK SYMPTOM SELECTION =====
function quickSymptom(symptom) {
    userInput.value = symptom;
    userInput.focus();
    sendMessage();
}

// ===== EMERGENCY =====
function emergency() {
    addMessageToChat('system', '🚨 ЭКСТРЕННАЯ СИТУАЦИЯ');
    
    const emergencyResult = {
        triage_level: 'red',
        action: '⚠️ ВЫЗОВИТЕ СКОРУЮ ПОМОЩЬ НЕМЕДЛЕННО',
        steps: [
            '1. Вызовите 112 немедленно',
            '2. Сообщите адрес и симптомы',
            '3. Лягте удобно',
            '4. Держите телефон',
            '5. Не двигайтесь'
        ],
        doctor_questions: ['Когда началось?', 'Какие лекарства?', 'Травмы?']
    };
    
    displayTriageResult(emergencyResult);
}

// ===== DISPLAY TRIAGE RESULT =====
function displayTriageResult(data) {
    chatBox.style.display = 'none';
    resultsPanel.style.display = 'block';
    
    triageIndicator.innerHTML = '';
    recommendationsDiv.innerHTML = '';
    
    const level = data.triage_level;
    
    triageIndicator.className = 'triage-indicator ' + level;
    
    let levelText = '';
    if (level === 'red') levelText = '🔴 ЭКСТРЕННО';
    else if (level === 'yellow') levelText = '🟡 СРОЧНО К ВРАЧУ';
    else levelText = '🟢 САМОПОМОЩЬ';
    
    triageIndicator.textContent = levelText;
    
    let html = `<h2>${data.action}</h2>`;
    html += '<p class="section-title">Что делать:</p><ul>';
    data.steps.forEach(step => {
        html += `<li>${step}</li>`;
    });
    html += '</ul>';
    
    if (data.doctor_questions && data.doctor_questions.length > 0) {
        html += '<p class="section-title">Вопросы для врача:</p><ul>';
        data.doctor_questions.forEach(q => {
            html += `<li>${q}</li>`;
        });
        html += '</ul>';
    }
    
    if (data.home_care && data.home_care.length > 0) {
        html += '<p class="section-title">Домашний уход:</p><ul>';
        data.home_care.forEach(care => {
            html += `<li>${care}</li>`;
        });
        html += '</ul>';
    }
    
    recommendationsDiv.innerHTML = html;
}

// ===== ADD MESSAGE TO CHAT =====
function addMessageToChat(role, text) {
    const div = document.createElement('div');
    div.className = 'message ' + role;
    div.textContent = text;
    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
}

// ===== RESET CHAT =====
function resetChat() {
    chatBox.innerHTML = '<div class="message system">👋 Новая консультация.</div>';
    chatBox.style.display = 'block';
    resultsPanel.style.display = 'none';
    userInput.value = '';
    userInput.focus();
}

// ===== LOAD HISTORY =====
function loadHistory() {
    fetch('/api/history')
        .then(res => res.json())
        .then(data => {
            historyList.innerHTML = '';
            
            if (data.length === 0) {
                historyList.innerHTML = '<p style="color: #999; padding: 10px;">История пуста</p>';
                return;
            }
            
            data.forEach(item => {
                const div = document.createElement('div');
                div.className = 'history-item';
                
                let levelText = item.triage_level === 'red' ? '🔴' : 
                               item.triage_level === 'yellow' ? '🟡' : '🟢';
                
                const date = new Date(item.created_at).toLocaleString('ru-RU');
                
                div.innerHTML = `
                    <div class="history-item-level">${levelText} ${item.triage_level.toUpperCase()}</div>
                    <div style="font-size: 0.9em;">${item.symptoms.substring(0, 50)}</div>
                    <div class="history-item-time">${date}</div>
                `;
                
                historyList.appendChild(div);
            });
        })
        .catch(err => console.error('Error:', err));
}

// ===== KEYBOARD SHORTCUTS =====
if (userInput) {
    userInput.addEventListener('keydown', function(event) {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            sendMessage();
        }
    });
}

// ===== INITIALIZE =====
document.addEventListener('DOMContentLoaded', () => {
    loadHistory();
    if (userInput) userInput.focus();

    if (sendBtn) {
        sendBtn.addEventListener('click', sendMessage);
    }

    if (emergencyBtn) {
        emergencyBtn.addEventListener('click', emergency);
    }

    const quickButtons = document.querySelectorAll('.quick-btn');
    quickButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const symptom = btn.dataset.symptom;
            if (symptom) {
                quickSymptom(symptom);
            }
        });
    });

    const resetBtn = document.getElementById('reset-btn');
    if (resetBtn) {
        resetBtn.addEventListener('click', resetChat);
    }
});
