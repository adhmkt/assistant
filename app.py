from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room
from flask_cors import CORS
from openai import OpenAI
import json
import os

# Load OpenAI API Key


my_api_key = os.environ.get('OPENAI_API_KEY')

# Initialize Flask and SocketIO
app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, async_mode='threading')

# OpenAI client setup
client = OpenAI(api_key=my_api_key)

# Store threads and assistant IDs by user session ID
user_threads = {}
user_assistant_ids = {}
default_assistant_id = 'asst_mR8mXP8ARHS93vEsZrWx6Wp9'
title = "My Assistant Title"

@app.route('/')
@app.route('/assistants')
def assistant_links():
    return render_template('menu.html')

@app.route('/<assistant_id>')
def index(assistant_id=None):
    # Use the provided assistant ID or the default one
    assistant_id = assistant_id or default_assistant_id
    
    # Retrieve the list of assistants from the OpenAI API
    my_assistants = client.beta.assistants.list(
        order="desc",
        limit="20",
    )
    # Convert the list of assistants to a JSON-like structure
    assistants_data = [{"id": asst.id, "name": asst.name} for asst in my_assistants.data]

    # Find the assistant's name by the provided assistant ID
    assistant_name = next((asst['name'] for asst in assistants_data if asst['id'] == assistant_id), "Unknown Assistant")

    # Render the chat template, passing the assistants data, selected assistant ID, and assistant name to the template
    return render_template('chat.html', data=assistants_data, selected_assistant_id=assistant_id, assistant_name=assistant_name)


def get_assistant_name_by_id(assistant_id):
    # Retrieve the list of assistants from the OpenAI API
    my_assistants = client.beta.assistants.list(
        order="desc",
        limit="20",
    )
    # Convert the list of assistants to a JSON-like structure
    assistants_data = [{"id": asst.id, "name": asst.name} for asst in my_assistants.data]

    # Find the assistant by ID and return its name
    for assistant in assistants_data:
        if assistant['id'] == assistant_id:
            return assistant['name']
    return None  # Return None if the assistant is not found

@socketio.on('connect')
def handle_connect():
    print('Socket.IO connected')
    join_room(request.sid)

    # Retrieve the assistant ID from the request's query parameters or use the default
    assistant_id = request.args.get('assistant_id', default_assistant_id)
    user_assistant_ids[request.sid] = assistant_id

    print(f"Assistant ID for user {request.sid}: {assistant_id}")
    try:
        thread = client.beta.threads.create()
        user_threads[request.sid] = thread.id
        print("Thread created for new user:", thread.id)
    except Exception as e:
        print(f"Error creating thread: {e}")

@socketio.on('disconnect')
def handle_disconnect():
    print('Socket.IO disconnected')
    # Clean up user session data
    user_threads.pop(request.sid, None)
    user_assistant_ids.pop(request.sid, None)

@socketio.on('change_assistant')
def handle_change_assistant(data):
    # Update the assistant ID for the user session
    user_assistant_ids[request.sid] = data['assistant_id']
    print(f"Assistant ID for user {request.sid} changed to: {data['assistant_id']}")

def get_bot_response(thread_id, message, assistant_id):
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
            assistant_id=assistant_id
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
    assistant_id = user_assistant_ids.get(sid)
    if assistant_id:
        response = get_bot_response(thread_id, message, assistant_id)
        socketio.emit('response', {'response': response}, room=sid)
    else:
        # Handle the case where the assistant ID is not found
        print(f"No assistant ID found for user session {sid}")
        socketio.emit('response', {'response': "Assistant ID not set."}, room=sid)

@socketio.on('message')
def handle_message(message):
    print('Received message:', message)
    thread_id = user_threads.get(request.sid)
    if thread_id:
        socketio.start_background_task(send_bot_response, thread_id, message, request.sid)
    else:
        emit('response', {'response': "No active thread found. Please reconnect."})

if __name__ == '__main__':
    socketio.run(app, debug=True)

