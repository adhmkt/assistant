from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from openai import OpenAI
from dotenv import load_dotenv

import json

with open('config.json', 'r') as config_file:
    config = json.load(config_file)
    my_api_key = config['openai_api_key']



app = Flask(__name__)
CORS(app)
socketio = SocketIO(app)

conversation_history = []
instructions = ""
current_temperature = 0.1  # Default temperature
current_max_tokens = 500   # Default max tokens


client = OpenAI(api_key=my_api_key)

def truncate_context(messages, max_length=4097):
    total_length = sum(len(message['content']) for message in messages)
    while total_length > max_length and len(messages) > 1:
        messages.pop(0)  # Remove the oldest message
        total_length = sum(len(message['content']) for message in messages)
    return messages

@app.route('/')
def index():
    return render_template('chat.html')

@socketio.on('connect')
def handle_connect():
    print('Socket.IO connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Socket.IO disconnected')

@socketio.on('set_instructions')
def handle_set_instructions(message):
    global instructions
    instructions = message.strip()
    print('Instructions set:', instructions)

@socketio.on('update_settings')
def handle_update_settings(settings):
    global current_temperature, current_max_tokens
    current_temperature = settings['temperature']
    current_max_tokens = settings['maxTokens']
    print('Updated settings: Temperature -', current_temperature, 'Max Tokens -', current_max_tokens)




@socketio.on('message')
def handle_message(message):
    print('Received message:', message)
    global conversation_history, instructions

    messages = []

    # Always include instructions in the conversation history if set
    if instructions:
        messages.append({"role": "system", "content": instructions})

    # Add the existing conversation history
    messages.extend(conversation_history)

    # Add the new user message
    messages.append({"role": "user", "content": message})

    # Ensure the conversation history doesn't exceed the maximum token limit
    messages = truncate_context(messages)

    # Log the messages being sent to the API
    print("Sending to API:", json.dumps(messages, indent=4))

    # API call to OpenAI with the updated messages
    response = client.chat.completions.create(
        model="gpt-4-1106-preview",
        messages=messages,
        temperature=current_temperature,
        max_tokens=current_max_tokens,
        top_p=1
    )

    bot_response = response.choices[0].message.content

    # Update conversation history with both user message and bot response
    conversation_history.append({"role": "user", "content": message})
    conversation_history.append({"role": "system", "content": bot_response})

    emit('response', {'response': bot_response})
    print('Bot Response:', bot_response)

if __name__ == '__main__':
    socketio.run(app, debug=True)

