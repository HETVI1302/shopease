document.addEventListener('DOMContentLoaded', () => {
    const chatToggle = document.getElementById('aiChatToggle');
    const chatWindow = document.getElementById('aiChatWindow');
    const chatClose = document.getElementById('aiChatClose');
    const chatForm = document.getElementById('aiChatForm');
    const chatInput = document.getElementById('aiChatInput');
    const chatMessages = document.getElementById('aiChatMessages');

    // Toggle Window
    chatToggle.addEventListener('click', () => {
        chatWindow.classList.toggle('d-none');
        chatWindow.classList.toggle('d-flex');
        if (!chatWindow.classList.contains('d-none')) {
            chatInput.focus();
        }
    });

    chatClose.addEventListener('click', () => {
        chatWindow.classList.add('d-none');
        chatWindow.classList.remove('d-flex');
    });

    // Handle form submission
    chatForm.addEventListener('submit', (e) => {
        e.preventDefault();
        
        const message = chatInput.value.trim();
        if (!message) return;
        
        // Add User Message
        appendMessage('user', message);
        chatInput.value = '';
        
        // Add typing indicator
        const typingId = 'typing-' + Date.now();
        appendTyping(typingId);
        
        // Call API
        fetch('/ai-chat/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                // Make sure to include CSRF token if needed, or rely on csrf_exempt for api for now
            },
            body: JSON.stringify({ message: message })
        })
        .then(res => res.json())
        .then(data => {
            removeTyping(typingId);
            appendMessage('ai', data.reply || 'Sorry, I encountered an error.');
        })
        .catch(err => {
            removeTyping(typingId);
            appendMessage('ai', 'Error connecting to the server.');
        });
    });

    function appendMessage(sender, text) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message mb-3 animate-up ${sender === 'user' ? 'text-end' : ''}`;
        
        const bubble = document.createElement('div');
        bubble.className = `chat-bubble p-3 rounded-3 d-inline-block shadow-sm ${
            sender === 'user' 
                ? 'user rounded-top-right-0' 
                : 'bot rounded-top-left-0'
        }`;
        
        // Handle basic markdown/linebreaks safely
        bubble.innerHTML = text.replace(/\n/g, '<br>');
        
        msgDiv.appendChild(bubble);
        chatMessages.appendChild(msgDiv);
        scrollToBottom();
    }
    
    function appendTyping(id) {
        const msgDiv = document.createElement('div');
        msgDiv.id = id;
        msgDiv.className = `message ai-message mb-3 animate-up`;
        msgDiv.innerHTML = `
            <div class="chat-bubble bot text-muted p-2 px-3 rounded-3 rounded-top-left-0 d-inline-block shadow-sm">
                <i class="fa-solid fa-ellipsis fa-fade"></i> Thinking...
            </div>
        `;
        chatMessages.appendChild(msgDiv);
        scrollToBottom();
    }
    
    function removeTyping(id) {
        const el = document.getElementById(id);
        if (el) el.remove();
    }

    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
});
