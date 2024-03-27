document.addEventListener('DOMContentLoaded', () => {

    async function fetchAndDisplayAssistantData(assistantId) {
        try {
            const response = await fetch(`/api/assistant/${assistantId}`);
            if (!response.ok) {
                throw new Error(`Failed to fetch assistant data: ${response.statusText}`);
            }
            const assistantData = await response.json();
    
            // Assuming you have elements in your HTML to populate with the assistant data
            // document.querySelector('#info-panel h2').textContent = assistantData.assistant_name;
            // document.querySelector('#info-panel p').innerHTML = assistantData.assistant_desc;
            // // If you have an <img> tag in your side panel for the assistant's image
            // document.querySelector('#info-panel img').src = `/static/images/assistant_imgs/${assistantData.assistant_img_url}`;

        } catch (error) {
            console.error('Error fetching assistant data:', error);
            // Handle the error appropriately
        }
    }
    
    

    
    console.log('DOM fully loaded and parsed');


    // Extract assistant_id from the URL path
    const pathSegments = window.location.pathname.split('/');
    const assistantIdFromUrl = pathSegments[1]; // The first segment in the path
    
    console.log('Extracted assistantIdFromUrl:', assistantIdFromUrl);
    

    // Check if assistantIdFromUrl is not null or empty and call the function
    // if (assistantIdFromUrl) {
    //     fetchAndDisplayAssistantData(assistantIdFromUrl);
    // }
    
    
    
    console.log('Extracted assistant_ID from URL:', assistantIdFromUrl);

    // Extract name from URL parameters
    const params = new URLSearchParams(window.location.search);
    console.log('URL search parameters:', params.toString());
    const userIdFromUrl = params.get('user_id');
    const nameFromUrl = params.get('name');
    
 
     // Define your elements first
     const infoPanel = document.getElementById('info-panel');
    //  const infoPanelBtn = document.getElementById('info-panel-btn');
    //  const togglePanelBtn = document.getElementById('toggle-panel-btn');
    //  const closePanelBtn = document.getElementById('close-panel-btn');
 
     // Now that we've defined infoPanelBtn, we can attach the event listener
    //  infoPanelBtn.addEventListener('click', function() {
    //      // Toggle the info panel visibility
    //      if (infoPanel.classList.contains('closed')) {
    //          infoPanel.classList.remove('closed');
    //      } else {
    //          infoPanel.classList.add('closed');
    //      }
    //  });
 
     // Function to open the panel
    //  const openPanel = () => {
    //      infoPanel.classList.remove('closed');
    //      document.getElementById('toggle-container').style.display = 'none';
    //  };
 
    //  // Function to close the panel
    //  const closePanel = () => {
    //      infoPanel.classList.add('closed');
    //     //  document.getElementById('toggle-container').style.display = 'block';
    //  };
 
    //  closePanelBtn.addEventListener('click', () => closePanel());
 
    // //  togglePanelBtn.addEventListener('click', () => openPanel());
   



    // Ensure assistantIdFromUrl is not null or undefined before connecting
    const queryString = assistantIdFromUrl ? `?assistant_id=${encodeURIComponent(assistantIdFromUrl)}&user_id=${encodeURIComponent(userIdFromUrl)}` : '';
    console.log('Query string for socket connection:', queryString);

    const socketUrl = `https://${document.domain}:${location.port}${queryString}`;
    console.log('Full socket URL:', socketUrl);
    // Verify document.domain
    console.log('Document domain:', document.domain);

    // Verify location.port
    console.log('Location port:', location.port);

    const socket = io.connect(socketUrl);
    console.log('Attempting to connect to Socket.IO with URL:', socketUrl);


socket.on('disconnect', () => {
    console.log('Socket.IO disconnected');
});




    function appendMessageToChatWindow(sender, text, isUser) {
        const chatWindow = document.querySelector('.chat-window');
        const messageDiv = document.createElement('div');
        const messageDiv_space = document.createElement('div');
        messageDiv_space.classList.add('message-separator');
        messageDiv.classList.add('chat-message');
        if (isUser) {
            messageDiv.classList.add('user-message');
        } else {
            messageDiv.classList.add('bot-message');
        }

        const converter = new showdown.Converter({ sanitize: true });
        const htmlContent = converter.makeHtml(text);
        messageDiv.innerHTML = `${sender} ${htmlContent}`;
        chatWindow.appendChild(messageDiv);
        chatWindow.appendChild(messageDiv_space);
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }

    function sendMessage() {
        const inputField = document.getElementById('message-text');
        let messageText = inputField.value.trim();
        if (messageText) {
            console.log("Sending message:", messageText);
            appendMessageToChatWindow('<img src="static/images/avatar-user.webp" alt="Bot" class="avatar bot-avatar">', messageText, true);
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

    // function updateSettings() {
    //     const temperature = parseFloat(temperatureInput.value);
    //     const maxTokens = parseInt(maxTokensInput.value, 10);

    //     console.log("Updating settings:", { temperature, maxTokens });
    //     socket.emit('update_settings', { temperature, maxTokens });
    // }

    document.getElementById('send-button').addEventListener('click', sendMessage);
    document.getElementById('message-text').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
            e.preventDefault();
        }
    });
    // document.getElementById('clear-button').addEventListener('click', clearChat);
    // document.getElementById('submit-instructions').addEventListener('click', sendInstructions);

    // temperatureInput.addEventListener('input', function() {
    //     temperatureValueDisplay.textContent = this.value;
    // });

    // maxTokensInput.addEventListener('input', function() {
    //     // This event listener is intentionally left empty.
    // });

    // updateSettingsButton.addEventListener('click', updateSettings);

    socket.on('response', (data) => {
        
        console.log("Response received:", data.response);
        if (data.response) {
           
            console.log("Handling text response");
            appendMessageToChatWindow('<img src="static/images/avatar-bot.webp" alt="Bot" class="avatar bot-avatar">', data.response, false);
            
            spinner.style.display = 'none';


        } else {
            console.log("No response or non-image response received");
        }
    });
    
});