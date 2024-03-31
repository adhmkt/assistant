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
    const nameFromUrl = params.get('assistant_name');
    const sessionFromUrl = params.get('session_id');
    
    console.log('Extracted user_ID from URL:', userIdFromUrl);
    console.log('Extracted sesssion_ID from URL:', sessionFromUrl);
    console.log('Extracted assistant name from URL:', nameFromUrl);
 
     // Define your elements first
     const infoPanel = document.getElementById('info-panel');



    // Ensure assistantIdFromUrl is not null or undefined before connecting
    const queryString = assistantIdFromUrl ? `?assistant_id=${encodeURIComponent(assistantIdFromUrl)}&user_id=${encodeURIComponent(userIdFromUrl)}&session_id=${encodeURIComponent(sessionFromUrl)}` : '';
    console.log('Query string for socket connection NEW VERSION:', queryString);

    let socketUrl;
    if (location.port) {
        socketUrl = `https://${document.domain}:${location.port}${queryString}`;
    } else {
        socketUrl = `https://${document.domain}${queryString}`;
}
console.log('Full socket URL:', socketUrl);
    console.log('Full socket URL:', socketUrl);
    // Verify document.domain
    console.log('Document domain:', document.domain);

    // Verify location.port
    console.log('Location port:', location.port);

   

    const socket = io({
        query: queryString,
        autoConnect: false,
    });

    // Manually connect for the first time
    socket.connect();

    socket.on('connect', () => {
        console.log('Connected to Socket.IO');
    });


    console.log('Attempting to connect to Socket.IO with URL:', socketUrl);


socket.on('disconnect', (reason) => {
    console.log(`Disconnected: ${reason}`);
    // Handle automatic reconnection for certain scenarios
    if (reason === 'io server disconnect' || reason === 'io client disconnect') {
        // Update server-side session handling to manage 'session_id' for reconnection purposes
        // This is a conceptual step - ensure your server logic uses 'session_id' to re-establish context
        console.log('Attempting to reconnect...');
        socket.connect();
    }
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
            
            // Prepare the message data as an object
            const messageData = {
                text: messageText,
                // Add any additional data here
                session_id: sessionFromUrl, // Replace this with the actual session ID
                user_id: userIdFromUrl, // Replace this with the actual user ID
                assistant_id: assistantIdFromUrl,
                // You can add more fields as needed
            };
    
            // Emit the message event with the messageData object
            socket.emit('message', messageData);
    
            inputField.value = ''; // Clear the input field after sending
            spinner.style.display = 'inline-block'; // Show spinner or any indicator for message sending
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



    document.getElementById('send-button').addEventListener('click', sendMessage);
    document.getElementById('message-text').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
            e.preventDefault();
        }
    });


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