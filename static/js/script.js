document.addEventListener('DOMContentLoaded', () => {
    const spinner = document.getElementById('spinner');
    const temperatureInput = document.getElementById('temperature');
    const maxTokensInput = document.getElementById('max-tokens');
    const temperatureValueDisplay = document.getElementById('temperature-value');
    const updateSettingsButton = document.getElementById('update-settings');

    const selectedAssistantId = document.getElementById('selected-assistant-id').value;

    console.log('Chat client ready');

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
    
            fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    message: messageText, 
                    sid: 'user-session-id',  // Replace 'user-session-id' with actual session management
                    assistant_id: selectedAssistantId  // Send the selected assistant ID
                })
            })
            .then(response => response.json())
            .then(data => {
                console.log("Received response:", data.response);
                appendMessageToChatWindow('Bot', data.response, false);
                spinner.style.display = 'none';
            })
            .catch(error => console.error('Error:', error));
    
            inputField.value = '';
            spinner.style.display = 'inline-block';
        }
    }
    

    function clearChat() {
        const chatWindow = document.querySelector('.chat-window');
        chatWindow.innerHTML = '';
        console.log('Chat cleared');
    }

    // Other functions remain the same...

    document.getElementById('send-button').addEventListener('click', sendMessage);
    document.getElementById('message-text').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
            e.preventDefault();
        }
    });
    document.getElementById('clear-button').addEventListener('click', clearChat);

    // Remove event listeners related to Socket.IO and any other unnecessary code
});
