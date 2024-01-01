from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room
from flask_cors import CORS
from openai import OpenAI
import json

# Load OpenAI API Key
with open('config.json', 'r') as config_file:
    config = json.load(config_file)
    my_api_key = config['openai_api_key']

# Initialize Flask and SocketIO
app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, async_mode='threading')

# OpenAI client setup
client = OpenAI(api_key=my_api_key)

# Retrieve the assistant
assistant_id = 'asst_9m5KykiGCv2uENyVPicYOCke'  # Replace with your assistant ID
assistant = client.beta.assistants.retrieve(assistant_id=assistant_id)

# Store threads by user session ID
user_threads = {}

@app.route('/')
def index():
    with open('assistants_config.json', 'r') as file:
        data = json.load(file)
    return render_template('chat.html', data=data)
    #return render_template('chat.html')

def dropdown():
    with open('assistants_config copy.json', 'r') as file:
        data = json.load(file)
        return render_template('dropdown.html', data=data)

@socketio.on('connect')
def handle_connect():
    print('Socket.IO connected')
    join_room(request.sid)  # Client joins a room named after their session ID
    # Create a new thread for each user session upon connection
    try:
        thread = client.beta.threads.create()
        user_threads[request.sid] = thread.id
        print("Thread created for new user:", thread.id)
    except Exception as e:
        print(f"Error creating thread: {e}")

@socketio.on('disconnect')
def handle_disconnect():
    print('Socket.IO disconnected')

def get_bot_response(thread_id, message):
    try:
        # Send the user's message to the thread
        client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=message
        )
        print("Message sent to thread")

        # Run the assistant on the thread
        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant.id
        )
        print("Run created:", run)

        # Poll for the assistant's response
        while True:
            run = client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )
            if run.status == 'completed':
                break
            socketio.sleep(1)  # Non-blocking sleep

        # Retrieve all messages from the thread
        messages_response = client.beta.threads.messages.list(
            thread_id=thread_id
        )

        # Extract the bot's response from the messages
        for msg in messages_response.data:
            if msg.role == 'assistant':
                return " ".join(content.text.value for content in msg.content if hasattr(content, 'text'))

    except Exception as e:
        print(f"Error in getting bot response: {e}")
        return "Sorry, an error occurred."

def send_bot_response(thread_id, message, sid):
    response = get_bot_response(thread_id, message)
    # Use socketio.emit with room argument
    socketio.emit('response', {'response': response}, room=sid)

@socketio.on('message')
def handle_message(message):
    print('Received message:', message)
    thread_id = user_threads.get(request.sid)

    if thread_id:
        # Include the session ID as an argument
        socketio.start_background_task(send_bot_response, thread_id, message, request.sid)
    else:
        emit('response', {'response': "No active thread found. Please reconnect."})

if __name__ == '__main__':
    socketio.run(app, debug=True)
