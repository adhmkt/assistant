
    const spinner = document.getElementById('spinner');
    const temperatureInput = document.getElementById('temperature');
    const maxTokensInput = document.getElementById('max-tokens');
    const temperatureValueDisplay = document.getElementById('temperature-value');
    const updateSettingsButton = document.getElementById('update-settings');

    const selectedAssistantId = document.getElementById('selected-assistant-id').value;

    console.log('Chat client ready');

    document.addEventListener('DOMContentLoaded', () => {
        const spinner = document.getElementById('spinner');
        const selectedAssistantId = document.getElementById('selected-assistant-id').value;
        console.log('Chat client ready');
    
        function appendMessageToChatWindow(sender, text, isUser) {
            const chatWindow = document.querySelector('.chat-window');
            const messageDiv = document.createElement('div');
            messageDiv.classList.add('chat-message');
            messageDiv.classList.add(isUser ? 'user-message' : 'bot-message');
            
            const converter = new showdown.Converter({ sanitize: true });
            const htmlContent = converter.makeHtml(text);
            messageDiv.innerHTML = `${sender}: ${htmlContent}`;
            chatWindow.appendChild(messageDiv);
            chatWindow.scrollTop = chatWindow.scrollHeight;
        }
    
        function pollForTaskCompletion(taskId) {
            const checkStatus = () => {
                fetch(`/status/${taskId}`) // Adjust this endpoint as needed
                    .then(response => response.json())
                    .then(data => {
                        if (data.status === 'SUCCESS') {
                            appendMessageToChatWindow('Bot', data.result, false);
                            spinner.style.display = 'none';
                        } else {
                            setTimeout(checkStatus, 2000); // Poll every 2 seconds
                        }
                    })
                    .catch(error => console.error('Error:', error));
            };
            checkStatus();
        }
    
        function sendMessage() {
            const inputField = document.getElementById('message-text');
            const messageText = inputField.value.trim();
            if (messageText) {
                console.log("Sending message:", messageText);
                appendMessageToChatWindow('You', messageText, true);
                spinner.style.display = 'inline-block';
    
                fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        message: messageText, 
                        sid: 'user-session-id', // Replace with actual session management
                        assistant_id: selectedAssistantId
                    })
                })
                .then(response => response.json())
                .then(data => {
                    console.log("Task ID received:", data.task_id);
                    pollForTaskCompletion(data.task_id);
                })
                .catch(error => console.error('Error:', error));
    
                inputField.value = '';
            }
        }
    
        function clearChat() {
            const chatWindow = document.querySelector('.chat-window');
            chatWindow.innerHTML = '';
            console.log('Chat cleared');
        }
    
        // Event listeners
        document.getElementById('send-button').addEventListener('click', sendMessage);
        document.getElementById('message-text').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendMessage();
                e.preventDefault();
            }
        });
        document.getElementById('clear-button').addEventListener('click', clearChat);
    });
    