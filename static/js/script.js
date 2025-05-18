const chatMessages = document.getElementById('chat-messages');
const userInput = document.getElementById('user-input');
const sendButton = document.getElementById('send-button');
const sourcesContainer = document.getElementById('sources-container');
const sourcesContent = document.getElementById('sources-content');

sendButton.addEventListener('click', sendMessage);
userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendMessage();
    }
});

window.addEventListener('DOMContentLoaded', () => {
    userInput.focus();
});

function sendMessage() {
    const message = userInput.value.trim();

    if (!message) {
        return;
    }

    addMessage(message, 'user');
    userInput.value = '';

    const loadingElement = addLoadingMessage();
    sourcesContainer.style.display = 'none';

    fetch('/api/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question: message }),
    })
        .then(response => response.json())
        .then(data => {
            chatMessages.removeChild(loadingElement);
            addMessage(data.answer, 'bot');

            if (data.sources && data.sources.length > 0) {
                displaySources(data.sources);
            }

            scrollToBottom();
        })
        .catch(error => {
            chatMessages.removeChild(loadingElement);

            addMessage('Sorry, there was an error processing your request. Please try again.', 'bot');
            console.error('Error:', error);

            scrollToBottom();
        });
}

function addMessage(content, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', `${sender}-message`);

    const processedContent = sender === 'bot' ? marked.parse(content) : content;
    messageDiv.innerHTML = `
        <div class="message-content">
            <div class="message-icon">
                <i class="fas fa-${sender === 'user' ? 'user' : 'robot'}"></i>
            </div>
            <div class="message-text">
                ${sender === 'bot' ? processedContent : `<p>${content}</p>`}
            </div>
        </div>
    `;

    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

function addLoadingMessage() {
    const loadingDiv = document.createElement('div');
    loadingDiv.classList.add('message', 'bot-message');

    loadingDiv.innerHTML = `
        <div class="message-content">
            <i class="fas fa-robot message-icon"></i>
            <div class="message-text">
                <div class="spinner"></div>
                <span>Thinking...</span>
            </div>
        </div>
    `;

    chatMessages.appendChild(loadingDiv);
    scrollToBottom();

    return loadingDiv;
}

function displaySources(sources) {
    sourcesContent.innerHTML = '';

    sources.forEach((source, index) => {
        const sourceDiv = document.createElement('div');
        sourceDiv.classList.add('source-item');

        let metadataHtml = '';
        if (source.metadata) {
            const metaItems = [];
            for (const [key, value] of Object.entries(source.metadata)) {
                if (value && typeof value === 'string') {
                    metaItems.push(`<span><strong>${key}:</strong> ${value}</span>`);
                }
            }
            if (metaItems.length > 0) {
                metadataHtml = `
                    <div class="source-metadata">
                        ${metaItems.join(' | ')}
                    </div>
                `;
            }
        }

        sourceDiv.innerHTML = `
            <div class="source-content">
                <strong>Source ${index + 1}:</strong>
                <p>${source.content}</p>
            </div>
            ${metadataHtml}
        `;

        sourcesContent.appendChild(sourceDiv);
    });

    sourcesContainer.style.display = 'block';
}

function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}