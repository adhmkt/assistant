from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from openai import OpenAI
import os

# Load OpenAI API Key
my_api_key = os.environ.get('OPENAI_API_KEY')

# Initialize Flask
app = Flask(__name__)
CORS(app)

# OpenAI client setup
client = OpenAI(api_key=my_api_key)

# Store threads and assistant IDs by user session ID
# Note: For a REST API, consider a different way to manage user sessions and threads
user_threads = {}
user_assistant_ids = {}
default_assistant_id = 'asst_mR8mXP8ARHS93vEsZrWx6Wp9'
title = "My Assistant Title"


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
   


@app.route('/')
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
        limit="5",
    )
    # Convert the list of assistants to a JSON-like structure
    assistants_data = [{"id": asst.id, "name": asst.name} for asst in my_assistants.data]

    # Find the assistant by ID and return its name
    for assistant in assistants_data:
        if assistant['id'] == assistant_id:
            return assistant['name']
    return None  # Return None if the assistant is not found


@app.route('/chat', methods=['POST'])
def handle_chat():
    data = request.json
    message = data.get('message')
    sid = data.get('sid')  # Placeholder for session management
    assistant_id = data.get('assistant_id', default_assistant_id) 
    thread_id = user_threads.get(sid)

     # Create a new thread for the chat session if it doesn't exist
    if sid not in user_threads:
        thread = client.beta.threads.create()
        user_threads[sid] = thread.id
    thread_id = user_threads[sid]

    response = get_bot_response(thread_id, message, assistant_id)
    return jsonify({'response': response})






if __name__ == '__main__':
    app.run(debug=True)
