const chatBox = document.getElementById('chat-box');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');

let messageHistory = [];

function appendMessage(role, text) {
    const div = document.createElement('div');
    div.classList.add('message', role);
    div.textContent = text;
    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
    return div;
}

async function sendMessage() {
    const text = userInput.value.trim();
    if (!text) return;

    appendMessage('user', text);
    userInput.value = '';
    sendBtn.disabled = true;

    const aiMessageDiv = appendMessage('ai', '');
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
                        aiMessageDiv.textContent = aiResponseText;
                        chatBox.scrollTop = chatBox.scrollHeight;
                    }
                } catch (e) {
                    console.error("Ошибка парсинга JSON", e);
                }
            }
        }

        messageHistory.push({ role: "user", content: text });
        messageHistory.push({ role: "assistant", content: aiResponseText });

    } catch (error) {
        aiMessageDiv.textContent = "Ошибка: " + error.message;
        aiMessageDiv.style.color = "#ff6b6b";
    } finally {
        sendBtn.disabled = false;
        userInput.focus();
    }
}

sendBtn.addEventListener('click', sendMessage);
userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});