document.addEventListener('DOMContentLoaded', () => {
    const socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);
    const spinner = document.getElementById('spinner');
    const temperatureInput = document.getElementById('temperature');
    const maxTokensInput = document.getElementById('max-tokens');
    const temperatureValueDisplay = document.getElementById('temperature-value');
    const updateSettingsButton = document.getElementById('update-settings');

    socket.on('connect', () => {
        console.log('Socket.IO connected');
    });

    socket.on('disconnect', () => {
        console.log('Socket.IO disconnected');
    });

    function appendMessageToChatWindow(sender, text, isUser) {
        const chatWindow = document.querySelector('.chat-window');
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('chat-message');
        if (isUser) {
            messageDiv.classList.add('user-message');
        } else {
            messageDiv.classList.add('bot-message');
        }

        // Configure Showdown converter with XSS protection
        const converter = new showdown.Converter({ sanitize: true });

    
        
        // Convert Markdown to HTML
        const htmlContent = converter.makeHtml(text);
        messageDiv.innerHTML = `${sender}: ${htmlContent}`;
        chatWindow.appendChild(messageDiv);
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }
    

    function sendMessage() {
        const inputField = document.getElementById('message-text');
        let messageText = inputField.value.trim();
        if (messageText) {
            console.log("Sending message:", messageText);
            appendMessageToChatWindow('You', messageText, true);
            socket.emit('message', messageText);
            inputField.value = '';
            spinner.style.display = 'inline-block';
        }
    }

    function clearChat() {
        const chatWindow = document.querySelector('.chat-window');
        chatWindow.innerHTML = '';
        console.log('Chat cleared');
    }

    function sendInstructions() {
        const instructionField = document.getElementById('instruction-text');
        let instructionText = instructionField.value.trim();
        if (instructionText) {
            console.log("Sending instructions:", instructionText);
            socket.emit('set_instructions', instructionText);
            instructionField.value = '';
        }
    }

    function updateSettings() {
        const temperature = parseFloat(temperatureInput.value);
        const maxTokens = parseInt(maxTokensInput.value, 10);

        console.log("Updating settings:", { temperature, maxTokens });
        socket.emit('update_settings', { temperature, maxTokens });
    }

    // Event Listeners
    document.getElementById('send-button').addEventListener('click', sendMessage);
    document.getElementById('message-text').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
            e.preventDefault();
        }
    });
    document.getElementById('clear-button').addEventListener('click', clearChat);
    document.getElementById('submit-instructions').addEventListener('click', sendInstructions);

    temperatureInput.addEventListener('input', function() {
        temperatureValueDisplay.textContent = this.value;
    });

    maxTokensInput.addEventListener('input', function() {
        // This event listener is intentionally left empty to avoid automatic updates.
    });

    updateSettingsButton.addEventListener('click', updateSettings);

    socket.on('response', (data) => {
        if (data.response) {
            console.log("Received message:", data.response);
            appendMessageToChatWindow('Bot', data.response, false);
            spinner.style.display = 'none';
        }
    });
});
