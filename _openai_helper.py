from openai import OpenAI
from time import sleep

class OpenAIHelper:
    def __init__(self, api_key, assistant_id):
        self.client = OpenAI(api_key=api_key)
        self.assistant_id = assistant_id

    def upload_file(self, file_path):
        # Upload a file to OpenAI
        with open(file_path, 'rb') as file:
            response = self.client.files.create(file=file, purpose='answers')
        return response.id

    def send_message(self, message, file_id=None):
        # Create a new thread for each user interaction
        thread = self.client.beta.threads.create()

        # Send the user's message to the thread
        self.client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=message
        )

        # Run the assistant on the thread
        run = self.client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=self.assistant_id,
            file_ids=[file_id] if file_id else None
        )

        # Wait a moment to ensure the assistant has time to respond
        sleep(5)  # Adjust the sleep time as necessary

        # Retrieve the run to get the assistant's response
        run = self.client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        )

        # Retrieve all messages from the thread
        messages_response = self.client.beta.threads.messages.list(
            thread_id=thread.id
        )

        # Extract the bot's response from the messages
        bot_response = ""
        for msg in messages_response.data:
            if msg.role == 'assistant':
                bot_response += msg.content + "\n"

        return bot_response.strip()

# Example usage
# api_key = 'your-api-key'
# assistant_id = 'your-assistant-id'
# openai_helper = OpenAIHelper(api_key, assistant_id)
# file_id = openai_helper.upload_file("path/to/yourfile.txt")
# response = openai_helper.send_message("Please analyze this file.", file_id=file_id)
# print(response)
