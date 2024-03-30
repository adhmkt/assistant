from quart import Quart, session, redirect, url_for, render_template, websocket, request, Response, abort, jsonify
import uvicorn
import asyncio
import socketio
from quart_cors import cors
from openai import OpenAI
import httpx
import os
import re
import json
from urllib.parse import parse_qs
from command.command_registry import CommandRegistry
from supabase import create_client, Client
from database_manager import DatabaseManager
from urllib.parse import quote 
import uuid

app = Quart(__name__)
# Allow CORS for all domains on all routes
app = cors(app, allow_origin="*")


# Assuming command_registry is a module you have for command execution



# Load OpenAI API Key and setup the client
my_api_key = os.getenv('OPENAI_API_KEY')
my_supabase_key = os.getenv('SUPABASE_KEY')
my_supabase_url = os.getenv('SUPABASE_URL')
app.secret_key = os.getenv('MY_APP_SECRET_KEY')

client = OpenAI(api_key=my_api_key)


sio = socketio.AsyncServer(async_mode='asgi')
sio_app = socketio.ASGIApp(sio, app)



class SessionManager:
    def __init__(self):
        self.user_threads = {}
        self.user_assistant_ids = {}
        self.thread_to_sid = {}
        self.user_ids = {}

    async def create_thread_for_sid(self, sid, assistant_id, user_id):
        try:
            loop = asyncio.get_running_loop()
            # Assuming client.beta.threads.create returns a Thread-like object
            thread = await loop.run_in_executor(None, client.beta.threads.create)
            # Access the 'id' attribute of the thread object (adjust according to the actual attribute name)
            self.user_threads[sid] = thread.id if hasattr(thread, 'id') else None
            self.user_assistant_ids[sid] = assistant_id
            self.user_ids[sid] = user_id 
            self.thread_to_sid[thread.id if hasattr(thread, 'id') else None] = sid
            print(f"Thread created for new user: {thread.id if hasattr(thread, 'id') else 'Unknown ID'} with SID: {sid}")
        except Exception as e:
            print(f"Error creating thread for SID {sid}: {e}")

    def get_user_id(self, sid):
         
         return self.user_ids.get(sid)

    def get_thread_id(self, sid):
        return self.user_threads.get(sid)

    def get_sid_by_thread_id(self, thread_id):
        return self.thread_to_sid.get(thread_id)

    def get_assistant_id(self, sid):
        return self.user_assistant_ids.get(sid)

    def remove_session(self, sid):
        thread_id = self.user_threads.pop(sid, None)
        self.user_assistant_ids.pop(sid, None)
        if thread_id:
            self.thread_to_sid.pop(thread_id, None)
        # print(f"Session data removed for SID: {sid}")

session_manager = SessionManager()



async def handle_function(run, thread_id, assistant_id, client, function_name, tool_arguments,tool_call_id, origin_message):
    # print("Starting handle_function with hardcoded testing")
    command_registry = CommandRegistry()

    # Hardcoded tool name for testing
    tool_name = function_name

    try:
        # print(f"Executing command: {tool_name}")
        # Directly use the hardcoded tool name and example arguments

        stored_prompt = prompts_storage.get(thread_id)
        # print(f'stored_prompt = {stored_prompt}')

        if stored_prompt and tool_name == 'generate_image':
            # print(f"Retrieved stored prompt for thread_id {thread_id}: {stored_prompt}")
            tool_arguments = {'img_generation_prompt': clean_prompt(stored_prompt)}
        else:
            # print(f"No prompt stored for thread_id {thread_id}.")
            tool_arguments = tool_arguments
        result = await command_registry.execute_command(tool_name, tool_arguments)
        # print(f"Command executed successfully: {tool_name}, Result: {result}")



        # Create tool_outputs with the response string
        tool_outputs = [
            {
                "tool_call_id": tool_call_id,
                "output": result,
            },
        ]

        # Submit tool_outputs to the thread run
        client.beta.threads.runs.submit_tool_outputs(
            thread_id=thread_id,
            run_id=run.id,
            tool_outputs=tool_outputs
        )

        # Directly handle and send the response without using a queue
        sid = session_manager.get_sid_by_thread_id(thread_id)
        if sid:
           
            #await sio.emit('response', {'response': result}, room=sid)
            print("")
    except Exception as e:
        print(f"An error occurred while executing {tool_name}: {e}")

async def load_assistants():
    try:
        with open('static/data/assistants.json', 'r') as file:
            data = json.load(file)
        return data['assistants']
    except FileNotFoundError:
        print("The assistants.json file was not found.")
        return []




@app.route('/login', methods=['GET', 'POST'])
async def login():
    # Capture assistant_id and assistant_name from the URL query parameters, with defaults if not provided
    assistant_id = request.args.get('assistant_id')
    assistant_name = request.args.get('assistant_name')
    

    print(f"Captured on login: assistant_id={assistant_id}, assistant_name={assistant_name}")  # Debug print

    if request.method == 'POST':
        assistant_id = (await request.form)['assistant_id']
        assistant_name = (await request.form)['assistant_name']
        
        print(f"Captured on login POST: assistant_id={assistant_id}, assistant_name={assistant_name}")  # Debug print
        
        email = (await request.form)['email']
        password = (await request.form)['password']
        database_manager = DatabaseManager()
        user_id = await database_manager.do_login(email, password)

        if user_id:
            # session['user_id'] = user_id  # Store user_id in session to indicate authentication

            _session_id = str(uuid.uuid4())
            encoded_session_id = quote(_session_id)

            
            await database_manager.save_session_data(
                    session_id=_session_id,
                    user_id=user_id,
                    assistant_id=assistant_id,
                    thread_id=None  # No thread_id yet
                )

            # Construct redirect URL using the actual assistant_id and assistant_name captured from the request
            redirect_url = url_for('index', assistant_id=assistant_id) + \
                f"?assistant_name={assistant_name}&user_id={user_id}&session_id={encoded_session_id}"
            

            return redirect(redirect_url)
        else:
            return await render_template('login.html', assistant_id=assistant_id, assistant_name=assistant_name)
    else:
        # Pass assistant_id and assistant_name to the template to preserve them in any forms or links
        return await render_template('login.html', assistant_id=assistant_id, assistant_name=assistant_name)

@app.route('/<assistant_id>')
async def index(assistant_id=None):

    user_id = request.args.get('user_id')
    session_id = request.args.get('session_id')
    
    

    if user_id is None:
        assistant_name = request.args.get('name', '')  # Provide a default value if 'name' is not found

        # Encode the assistant_id and assistant_name to ensure the URL is valid
        encoded_assistant_id = quote(assistant_id)
        encoded_assistant_name = quote(assistant_name)
        

            

        # Construct the URL with Quart's url_for
        # Note: Quart's url_for is an async function, so you need to await it
        redirect_url = url_for('login', assistant_id=encoded_assistant_id, assistant_name=encoded_assistant_name)
        
    
        return redirect(redirect_url)
    
    assistant_id = assistant_id
    assistant_name = request.args.get('assistant_name')
    session_id = request.args.get('session_id')

    if not assistant_name:
    # Assuming you have a function to fetch the assistant name by ID
     assistant_name = "Assistant Name Error"
    
    
    
    print(f"session_id after login:  {session_id}")

    return await render_template('chat.html', data={}, selected_assistant_id=assistant_id, assistant_name=assistant_name, user_id=user_id,session_id=session_id)


@app.route('/image_proxy')
async def image_proxy():
    image_url = request.args.get('url')  # Get the image URL from query parameters
    if not image_url:
        return "Image URL not provided", 400
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(image_url)
            if response.status_code == 200:
                return Response(response.content, content_type=response.headers['Content-Type'])
            else:
                return "Failed to fetch image", response.status_code
        except Exception as e:
            return f"Error fetching image: {e}", 500

@app.route('/assistants')
async def assistant_links():
    return await render_template('menu.html')
    


@app.route('/forms', methods=['GET', 'POST'])
async def submit_form():
    try:
        data = await request.form
        
        user_name = data['user_name']
        user_type = data['user_type']
        user_school = data['user_school']
        user_city = data['user_city']

        data_manager = DatabaseManager()

        
        await data_manager.submit_form(
            user_name=user_name, 
            user_type=user_type, 
            school_name=user_school, 
            school_city=user_city
        )

        # Return a success response (adjust as needed)
        return jsonify({"message": "Form submitted successfully"}), 200
        
    except Exception as e:
        # If an error occurred during the insert operation
        return jsonify({"error": str(e)}), 500

        
        

     

@sio.event
async def connect(sid, environ):
    # print('Socket.IO connected')
    await sio.enter_room(sid, room=sid)
    query_string = environ.get('QUERY_STRING', '')
    parsed_query = parse_qs(query_string)
    print(f'Query String = {query_string}')
    print(f'Parsed Query = {parsed_query}')

    # print(f'Query String = {query_string}')
    
    # print(f'Parsed String = {parsed_query}')
    assistant_id = parsed_query.get('assistant_id', ['default_assistant_id'])[0]  # Example default ID
    user_id = parsed_query.get('user_id', ['default_user_id'])[0] 
    session_id = parsed_query.get('session_id', ['default_user_id'])[0] 
    print(f"USER ID AT CONNECT:  {user_id}")
    print(f"PARSED QUERY:  {parsed_query}")
    print(f"session_id at connect:  {session_id}")
    # print(f'assistant_id = {assistant_id}')
    # print('Tracing Line 118')
    await session_manager.create_thread_for_sid(sid, assistant_id,user_id)

@sio.event
async def disconnect(sid):
    # print('Socket.IO disconnected')
    session_manager.remove_session(sid)

@sio.event
async def message(sid, data):
    # print('Received message:', data)
    thread_id = session_manager.get_thread_id(sid)
    if thread_id:
        assistant_id = session_manager.get_assistant_id(sid)
        
        await send_bot_response(thread_id, data, sid, assistant_id)
    else:
        await sio.emit('response', {'response': "No active thread found. Please reconnect."}, room=sid)

# handled_actions = {}


# Assuming there's a global dictionary to store prompts
prompts_storage = {}

def clean_prompt(response_text):
    """
    Extracts content between special markers **bg_prtx0345** and **end_prtx0345**.

    Args:
    response_text (str): The full text from which to extract the content.

    Returns:
    str: The extracted content if both markers are found, otherwise an empty string or error message.
    """
    # Define the pattern to match the content between the two markers
    pattern = r'\*\*bg_prtx0345\*\*(.*?)\*\*end_prtx0345\*\*'
    match = re.search(pattern, response_text, re.DOTALL)

    if match:
        # Extract and return the content between the markers
        return match.group(1).strip()
    else:
        # Return an empty string or error message if the markers are not found
        return "Prompt could not be extracted."

async def get_bot_response(thread_id, user_id, message, assistant_id, client):
    # print(f'Message is : {message}')
    try:
        
        # user_id = 'gfergergeeerge'
        session_id =1
        data_manager = DatabaseManager()
        speaker = "user"
        print(f"MY USER ID:  {user_id}")

        await data_manager.save_chat_conversation(user_id=user_id,thread_id=thread_id,session_id=session_id,message=message, speaker=speaker, assistant_id=assistant_id)
    
        loop = asyncio.get_running_loop()
        # print("Sending user message to the thread...")
        # Send the user message to the thread
        await loop.run_in_executor(None, lambda: client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=message
        ))
        # print("User message sent successfully.")

        # print("Creating a new run for the thread...")
        # Create a new run for the thread
        run = await loop.run_in_executor(None, lambda: client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id
        ))
        # print(f"New run created: {run}")
        # print(f"New run created with run_id: {run.id}")

        handled_actions = set()  # Keep track of handled actions to prevent re-execution

        while True:
            # Check the status of the run
            run_status = await loop.run_in_executor(None, lambda: client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            ))
            
            if run_status.status in ['completed', 'failed']:
                break  # Exit loop if the run is completed or failed
            if run_status.status == 'requires_action' and run.id not in handled_actions:
                # print(f"The content of the run : {run}")
                tool_call = run_status.required_action.submit_tool_outputs.tool_calls[0]
                # print(run_status.required_action.submit_tool_outputs)
                # Parse the JSON-formatted string in the arguments attribute
               
                tool_call_id = tool_call.id  # This captures the needed tool_call_id
                function_name = run.tools[0].function.name
                # tool_call_id = run.tools[0].function_id
                
                # function_id = run.tools[0].function.id
                tool_arguments = tool_call.function.arguments 
                # tool_arguments = run.tools[0].function.parameters.get('properties', {}).get('user_prompt', {}).get('default', '')
                handled_actions.add(run.id)  # Mark this run as handled
                # Handle the required action
                await handle_function(run, thread_id, assistant_id, client, function_name, tool_arguments, tool_call_id, message)
            await asyncio.sleep(1)  # Wait before checking the run status again

        
        # Retrieve messages after the run completes
        messages_response = await loop.run_in_executor(None, lambda: client.beta.threads.messages.list(
            thread_id=thread_id
        ))
        print(f"thread_id : {thread_id}.")
        # print("Messages retrieved successfully.")
        # Process each assistant message to find and store the prompt with the identifier
        for msg in messages_response:
            if msg.role == 'assistant':
                response_text = msg.content[0].text.value if hasattr(msg.content[0], 'text') else ""
                speaker = "bot"
                await data_manager.save_chat_conversation(user_id=user_id,thread_id=thread_id,session_id=session_id,message=response_text, speaker=speaker, assistant_id=assistant_id)
    
                # Check for the identifier in the response text
                if 'prtx0345' in response_text:
                    # Assuming the entire response is relevant, otherwise, extract the specific part
                    prompts_storage[thread_id] = response_text
                    print(f"Stored prompt for thread_id {thread_id}.")
                else:
                    prompts_storage[thread_id] = 'not_defined'
                return response_text

    except Exception as e:
        print(f"Error in getting bot response: {e}")
        return "Sorry, an error occurred. Please try again later."


async def send_bot_response(thread_id, message, sid , assistant_id):
   
    assistant_id = session_manager.get_assistant_id(sid)  # Make sure to call the method with sid
    user_id = session_manager.get_user_id(sid)
    # print("FROM send_bot_response, line 229 , assistant_ID = ", assistant_id)
    
    if assistant_id:

        
        
        response = await get_bot_response(thread_id, user_id, message, assistant_id, client)
        await sio.emit('response', {'response': response}, room=sid)
    else:
        
        await sio.emit('response', {'response': "Assistant ID not set."}, room=sid)





if __name__ == "__main__":
     #uvicorn.run("app:sio_app", host="127.0.0.1", port=5000, reload=True)
    pass

