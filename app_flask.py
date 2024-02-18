from flask import Flask, render_template, request 
from flask_socketio import SocketIO, emit, join_room
from flask_cors import CORS
from openai import OpenAI
import json
import os

from command.command_registry import CommandRegistry

# Load OpenAI API Key and setup the client
my_api_key = os.environ.get('OPENAI_API_KEY')
client = OpenAI(api_key=my_api_key)

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, async_mode='threading')



# Store threads and assistant IDs by user session ID
user_threads = {}
user_assistant_ids = {}
default_assistant_id = 'asst_mR8mXP8ARHS93vEsZrWx6Wp9'
title = "My Assistant Title"
response_queue = []
# Global set to keep track of handled tool calls
handled_tool_calls = set()
thread_to_sid = {}


def get_sid_by_thread_id(thread_id):
    """ Retrieve the SocketIO session ID (sid) for a given thread ID """
    return thread_to_sid.get(thread_id)


# Revised handle_function - removed run creation from this function
def handle_function(run, thread_id, assistant_id, client):
    command_registry = CommandRegistry()
    tools_to_call = run.required_action.submit_tool_outputs.tool_calls
    for each_tool in tools_to_call:
        tool_call_id = each_tool.id

        if tool_call_id in handled_tool_calls:
            continue

        function_name = each_tool.function.name
        function_arg = json.loads(each_tool.function.arguments)
        print(f"Tool ID: {tool_call_id}, Function to Call: {function_name}, Parameters: {function_arg}")

        try:
            result = command_registry.execute_command(function_name, function_arg)
            response_queue.append((thread_id, result))
            handled_tool_calls.add(tool_call_id)
            send_queued_responses(client)
        except ValueError as e:
            print(f"Command Error: {e}")
        except Exception as e:
            print(f"An error occurred: {e}")

def send_queued_responses(client):
    while response_queue:
        thread_id, response = response_queue.pop(0)
        sid = get_sid_by_thread_id(thread_id)  # You'll need to implement this function to map thread_id back to sid
        socketio.emit('response', {'response': response}, room=sid)
        # socketio.emit('response', {'response': f'<a href="{image_url}" target="_blank">Click to see your image</a>'}, room=sid)





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

  
    try:
        thread = client.beta.threads.create()
        user_threads[request.sid] = thread.id
        thread_to_sid[thread.id] = request.sid
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

# Modified get_bot_response function
    

def get_bot_response(thread_id, message, assistant_id, client):
    try:
        # Check for an active run
        runs = client.beta.threads.runs.list(thread_id=thread_id)
        active_run = next((run for run in runs if run.status in ["active", "requires_action"]), None)

        if active_run:
            # If there's an active run, return a message to wait
            print("Active run detected. Waiting for it to complete.")
            return "Processing previous request, please wait or refresh  your browser"

        # If no active run, proceed to send the user's message
        client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=message
        )

        # Create a new run
        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id
        )

        # Poll for the assistant's response
        while True:
            run = client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )
            if run.status == 'completed':
                send_queued_responses(client) 
                break
            if run.status == "requires_action":
                handle_function(run, thread_id, assistant_id, client)
            socketio.sleep(1)  # Non-blocking sleep

        # Retrieve all messages from the thread
        messages_response = client.beta.threads.messages.list(
            thread_id=thread_id
        )

        # Extract the bot's response
        for msg in messages_response.data:
            if msg.role == 'assistant':
                return " ".join(content.text.value for content in msg.content if hasattr(content, 'text'))

    except Exception as e:
        print(f"Error in getting bot response: {e}")
        return "Sorry, an error occurred."


def send_bot_response(thread_id, message, sid):
    assistant_id = user_assistant_ids.get(sid)
    if assistant_id:
        response = get_bot_response(thread_id, message, assistant_id, client)
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