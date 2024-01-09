document.addEventListener('DOMContentLoaded', () => {
    const socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);
    const spinner = document.getElementById('spinner');
    const temperatureInput = document.getElementById('temperature');
    const maxTokensInput = document.getElementById('max-tokens');
    const temperatureValueDisplay = document.getElementById('temperature-value');
    const updateSettingsButton = document.getElementById('update-settings');
    // const assistantSelector = document.getElementById('model-select');

    const selectedAssistantId = document.getElementById('selected-assistant-id').value;

    // In your client-side JavaScript
const params = new URLSearchParams(window.location.search);
const assistantIdFromUrl = params.get('assistant_ID') || 'default_assistant_id';  // Replace 'default_assistant_id' with your actual default ID


    socket.on('connect', () => {
        socket.emit('change_assistant', { assistant_id: selectedAssistantId });
    });

    socket.on('connect', () => {
        socket.emit('set_assistant_id', { assistant_id: assistantIdFromUrl });
    });

    socket.on('connect', () => {
        // Emit an event to set the assistant ID when the connection is established
        socket.emit('set_assistant_id', { assistant_id: assistantIdFromUrl || defaultAssistantId });
    });

    socket.on('connect', () => {
        console.log('Socket.IO connected');
    });

    socket.on('disconnect', () => {
        console.log('Socket.IO disconnected');
    });

    // assistantSelector.addEventListener('change', function() {
    //     const selectedAssistantId = this.value;
    //     console.log("Assistant changed to:", selectedAssistantId);
    //     socket.emit('change_assistant', { assistant_id: selectedAssistantId });
    // });

    function appendMessageToChatWindow(sender, text, isUser) {
        const chatWindow = document.querySelector('.chat-window');
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('chat-message');
        if (isUser) {
            messageDiv.classList.add('user-message');
        } else {
            messageDiv.classList.add('bot-message');
        }

        const converter = new showdown.Converter({ sanitize: true });
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
        // This event listener is intentionally left empty.
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
