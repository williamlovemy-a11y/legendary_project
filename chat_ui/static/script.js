const chatBox = document.getElementById('chat-box');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');

let messageHistory = [];

function appendMessage(role, text, isStreaming = false) {
    // Если сообщение в процессе стриминга, обновляем последнее, иначе создаем новое
    if (isStreaming && chatBox.lastChild && chatBox.lastChild.classList.contains('ai') && chatBox.lastChild.querySelector('.streaming')) {
        const bubble = chatBox.lastChild.querySelector('.bubble');
        bubble.textContent = text;
    } else {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', role);
        
        if (role === 'ai') {
            messageDiv.innerHTML = `
                <div class="avatar-chat"><i class="fas fa-robot"></i></div>
                <div class="bubble${isStreaming ? ' streaming' : ''}">${text}</div>
            `;
        } else {
            messageDiv.innerHTML = `
                <div class="avatar-chat" style="background:#1e88e5; color:white;"><i class="fas fa-user"></i></div>
                <div class="bubble">${text}</div>
            `;
        }
        chatBox.appendChild(messageDiv);
    }
    chatBox.scrollTop = chatBox.scrollHeight;
}

async function sendMessage() {
    const text = userInput.value.trim();
    if (!text) return;

    appendMessage('user', text);
    userInput.value = '';
    sendBtn.disabled = true;

    let aiResponseText = "";

    try {
        const response = await fetch('http://localhost:8001/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: text,
                history: messageHistory
            })
        });

        if (!response.ok) {
            throw new Error(`Ошибка сервера: ${response.status}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');
            
            for (const line of lines) {
                if (!line.trim()) continue;
                try {
                    const json = JSON.parse(line);
                    if (json.message && json.message.content) {
                        const content = json.message.content;
                        aiResponseText += content;
                        appendMessage('ai', aiResponseText, true);
                    }
                } catch (e) {
                    console.error("Ошибка парсинга JSON", e);
                }
            }
        }

        messageHistory.push({ role: "user", content: text });
        messageHistory.push({ role: "assistant", content: aiResponseText });

    } catch (error) {
        appendMessage('ai', `⚠️ Ошибка соединения: ${error.message}. Проверьте, запущен ли сервер.`);
    } finally {
        sendBtn.disabled = false;
        userInput.focus();
    }
}

// Обработчики событий
sendBtn.addEventListener('click', sendMessage);
userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

// Быстрые кнопки
document.querySelectorAll('.quick-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const question = btn.getAttribute('data-question');
        if (question) {
            userInput.value = question;
            sendMessage();
        }
    });
});

// Плавный скролл до чата
const scrollBtn = document.getElementById('scrollToDemoBtn');
if (scrollBtn) {
    scrollBtn.addEventListener('click', () => {
        document.getElementById('demo-chat-section').scrollIntoView({ behavior: 'smooth' });
    });
}