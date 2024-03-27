from supabase import create_client, Client
import os
import asyncio
import pytz
import datetime


class DatabaseManager:
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)

    async def save_chat_conversation(self, user_id: str,thread_id: str, session_id: str, message: str, speaker: str, assistant_id: str):
        
        try:
            conversation = {
                "app_user": user_id,  # Use the actual user_id from your users table or authentication response
                "message": message,
                "thread_id": thread_id,
                "session_id": session_id,
                "speaker": speaker
            }

            print("Attempting to insert conversation:", conversation)

            self.supabase.table("conversations").insert(conversation).execute()

            print("Conversation inserted successfully.")
        except Exception as e:
            print("An error occurred while inserting conversation:", e)
                
            
        
    async def do_login(self, email, password):
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, self._sync_sign_in_with_password, email, password)
            user_details = response.user 
            user_id = getattr(user_details, "id", None)
            # print(f"Response from Supabase Auth: {response}, redirecting...")
            print(f"User ID: {user_id}, redirecting...")
            if user_id:
                return user_id
        except Exception as e:
            # This catches any exception, including AuthApiError, but loses specificity
            print(f"An error occurred during login: {e}")
        return None

    def _sync_sign_in_with_password(self, email, password):
        # Correctly pass arguments as a dictionary
        return self.supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

    

    async def submit_form(self, user_name, user_type, school_name, school_city):

        try:
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(None, lambda: self.supabase.table("biblio_users").insert({
                "user_name": user_name,
                "user_type": user_type,
                "school_name": school_name,
                "school_city": school_city
            }).execute())

            # Check the response and handle accordingly
            if response.error:
                return None, response.error.message
            return response.data, None
        except Exception as e:
            return None, str(e)

    def parse_datetime(dt_str):
        return datetime.fromisoformat(dt_str.rstrip("Z")).replace(tzinfo=pytz.UTC)

    def get_user_id_from_response(self, data):

        # Accessing attributes directly or via getter methods (adjust according to your object's structure)
        # provider_token = getattr(data, "provider_token", None)
        # provider_refresh_token = getattr(data, "provider_refresh_token", None)
        # access_token = getattr(data, "access_token", None)
        # refresh_token = getattr(data, "refresh_token", None)
        # expires_in = getattr(data, "expires_in", None)
        # expires_at = getattr(data, "expires_at", None)
        # token_type = getattr(data, "token_type", None)

        # Assuming the 'user' attribute is another object with its own properties
        user_details = data.user  # Direct attribute access, adjust if necessary

        user_id = getattr(user_details, "id", None)
        # phone = getattr(user_details, "phone", None)
        # app_metadata = getattr(user_details, "app_metadata", {})
        # user_metadata = getattr(user_details, "user_metadata", {})
        # aud = getattr(user_details, "aud", None)
        # email = getattr(user_details, "email", None)

        # # Assuming these dates are already datetime objects, otherwise, you'll need to parse them as shown previously
        # created_at = user_details.created_at
        # confirmed_at = user_details.confirmed_at
        # last_sign_in_at = user_details.last_sign_in_at
        # role = getattr(user_details, "role", None)
        # updated_at = user_details.updated_at

        return user_id


    def authenticate_user (self, user_name, user_type, school_name, school_city):
        


        params = {
        "p_user_name": f"%{user_name}%",
        "p_user_type": f"%{user_type}%",
        "p_school_name": f"%{school_name}%",
        "p_school_city": f"%{school_city}%"
        }

        try:
            # Execute the RPC call and get the response object
            response =   self.supabase.rpc("search_biblio_users_cs", params).execute()

            # Debug print to inspect the raw response
            print("Raw response:", response)

            # Access the 'data' attribute of the response object
            if response.data:

                
                # There are records in the 'data' attribute
                records = response.data
                print("Records found:", records)
                return True  # Return True as a matching record is found
            else:
                
                # No records found in the 'data' attribute
                print("No records found in the response.")
                return False
        except Exception as e:
            # Log any errors encountered during the execution
            print(f"An error occurred: {e}")
            return False

        
        