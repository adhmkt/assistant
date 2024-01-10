from flask import Flask, render_template, request, jsonify
from celery import Celery
from flask_cors import CORS
from openai import OpenAI
import os
import logging
from celery.result import AsyncResult
import time
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)



if os.environ.get('FLASK_ENV') == 'production':
    app.config.from_object('config_production.ProductionConfig')
else:
    app.config.from_object('config_development.DevelopmentConfig')

    # Load OpenAI API Key
my_api_key = os.environ.get('OPENAI_API_KEY')

# Set up logging
logging.basicConfig(level=logging.INFO)

CORS(app)


def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config['REDIS_TLS_URL'],
        broker=app.config['REDIS_TLS_URL']
    )
    celery.conf.update(app.config)
    return celery

celery = make_celery(app)



# OpenAI client setup
client = OpenAI(api_key=my_api_key)

# Store threads and assistant IDs by user session ID
# Note: For a REST API, consider a different way to manage user sessions and threads
user_threads = {}
user_assistant_ids = {}
default_assistant_id = 'asst_mR8mXP8ARHS93vEsZrWx6Wp9'
title = "My Assistant Title"



@celery.task
def get_bot_response(thread_id, message, assistant_id):
    try:
        # Send the user's message to the thread
        client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=message
        )
        logging.info("Message sent to thread")

        # Run the assistant on the thread
        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id
        )
        logging.info(f"Run created: {run}")

        # Add a timeout mechanism for the loop
        timeout = time.time() + 60  # 60 seconds from now
        while True:
            if time.time() > timeout:
                logging.error("Timeout while waiting for run to complete")
                return "Sorry, the request timed out."

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
        # response = " ".join(content.text.value for msg in messages_response.data if msg.role == 'assistant' for content in msg.content if hasattr(content, 'text'))
        # latest_message = next((msg for msg in reversed(messages_response.data) if msg.role == 'assistant'), None)
        # response = latest_message.content[0].text.value if latest_message and hasattr(latest_message.content[0], 'text') else ""
        
        

        # Find the timestamp of the latest user message
        latest_user_msg = next((msg for msg in reversed(messages_response.data) if msg.role == 'user'), None)
        latest_user_msg_timestamp = latest_user_msg.created_at if latest_user_msg else None

        # Find the first assistant message after the latest user message
        response = ""
        for msg in messages_response.data:
            if msg.role == 'assistant' and msg.created_at > latest_user_msg_timestamp:
                response = msg.content[0].text.value if hasattr(msg.content[0], 'text') else ""
                break
    
        return response

    except Exception as e:
        logging.error(f"Error in asynchronous bot response: {e}")
        return "Sorry, an error occurred."
    
@app.route('/status/<task_id>')
def get_status(task_id):
    task = AsyncResult(task_id, app=celery)

    if task.state == 'SUCCESS':
        return jsonify({
            'status': task.state,
            'result': task.result
        })
    else:
        return jsonify({'status': task.state})


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
    # assistant_id = data.get('assistant_id', default_assistant_id) 
    assistant_id = data.get('assistant_id') 
    thread_id = user_threads.get(sid)

     # Create a new thread for the chat session if it doesn't exist
    if sid not in user_threads:
        thread = client.beta.threads.create()
        user_threads[sid] = thread.id
    thread_id = user_threads[sid]

     # Call the asynchronous task
    task = get_bot_response.delay(thread_id, message, assistant_id)
    return jsonify({'task_id': task.id})  # Return the task ID for status checking

print("Redis URL:", app.config['REDIS_URL'])



if __name__ == '__main__':
    app.run(debug=True)
