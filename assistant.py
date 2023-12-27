from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from openai import OpenAI
import json
from time import sleep

# Load OpenAI API Key
with open('config.json', 'r') as config_file:
    config = json.load(config_file)
    my_api_key = config['openai_api_key']

# Initialize Flask and SocketIO
app = Flask(__name__)
CORS(app)
socketio = SocketIO(app)

# OpenAI client setup
client = OpenAI(api_key=my_api_key)

# Retrieve the assistant
assistant_id = 'asst_FFHD6j4WsXHFtbti9iz9poEA'  # Replace with your assistant ID
assistant = client.beta.assistants.retrieve(assistant_id=assistant_id)

@app.route('/')
def index():
    return render_template('chat.html')

@socketio.on('connect')
def handle_connect():
    print('Socket.IO connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Socket.IO disconnected')

@socketio.on('message')
def handle_message(message):
    print('Received message:', message)

    # Create a new thread for each user interaction
    thread = client.beta.threads.create()
    print("Thread created:", thread)

    # Send the user's message to the thread
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=message
    )
    print("Message sent to thread")

    # Run the assistant on the thread
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id
    )
    print("Run created:", run)

    # Wait a moment to ensure the assistant has time to respond
    sleep(5)  # Adjust the sleep time as necessary

    # Retrieve the run to get the assistant's response
    run = client.beta.threads.runs.retrieve(
        thread_id=thread.id,
        run_id=run.id
    )
    print("Run retrieved:", run)

    # Retrieve all messages from the thread
    messages_response = client.beta.threads.messages.list(
        thread_id=thread.id
    )

    # Convert messages_response to a serializable format
    messages_json = []
    for msg in messages_response.data:
        message_dict = {
            "id": msg.id,
            "assistant_id": msg.assistant_id,
            "content": [content.text.value for content in msg.content if hasattr(content, 'text')],
            "created_at": msg.created_at,
            "role": msg.role
        }
        messages_json.append(message_dict)

    print("Messages response JSON:", json.dumps(messages_json, indent=4))  # Print the JSON structure

    # Extract the bot's response from the messages
    bot_response = ""
    for msg in messages_json:
        if msg.get('role') == 'assistant':
            bot_response = " ".join(msg.get('content', []))
            break

    bot_response = bot_response.strip()
    print('Bot Response:', bot_response)
    emit('response', {'response': bot_response})

if __name__ == '__main__':
    socketio.run(app, debug=True)
