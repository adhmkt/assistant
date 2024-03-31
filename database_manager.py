from supabase import create_client, Client
import os
import asyncio
import pytz
import datetime



class DatabaseManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(DatabaseManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'is_initialized'):
            self.supabase_url = os.getenv('SUPABASE_URL')
            self.supabase_key = os.getenv('SUPABASE_KEY')
            self.supabase = create_client(self.supabase_url, self.supabase_key)
            self.is_initialized = True

    async def save_chat_conversation(self, user_id: str,thread_id: str, session_id: str, message: str, speaker: str, assistant_id: str):
        
        try:

            print(f"Debugging Values AFTER LOGIN:")
            print(f"app_user: {user_id}")  # Use the actual user_id from your users table or authentication response
            print(f"message: {message}")
            print(f"thread_id: {thread_id}")
            print(f"session_id: {session_id}")
            print(f"speaker: {speaker}")

            conversation = {
                "app_user": user_id,  # Use the actual user_id from your users table or authentication response
                "message": message,
                "thread_id": thread_id,
                "session_id": session_id,
                "speaker": speaker
            }

        

            self.supabase.table("conversations").insert(conversation).execute()

            print("Conversation inserted successfully.")
        except Exception as e:
            print("An error occurred while inserting conversation:", e)
                
            
        
    

    async def do_login(self, email, password, session_id, assistant_id):
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, self._sync_sign_in_with_password, email, password)
            user_details = response.user 
            new_user_id = getattr(user_details, "id", None)
            print(f"User ID AFTER LOGIN: {new_user_id}, redirecting...")
            

            if new_user_id:
                
             return new_user_id
        
        except Exception as e:
            print(f"An error occurred during login: {e}")
        return None, None


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

    async def save_session_data(self, session_id, user_id, assistant_id, thread_id):
        """Insert or update session data in the database."""
        try:
            data = {
                "session_id": session_id,
                "user_id": user_id,
                "assistant_id": assistant_id,
                "thread_id": thread_id
            }
            response = self.supabase.table("sessions").upsert(data).execute()
            
            # Check if response contains data; if so, operation was likely successful
            if response.data:
                print("Session data saved successfully:", response.data)
            else:
                # If there's no data or if there's an unexpected response structure, log for further inspection
                print("Unexpected response structure or no data returned:", response)
        except Exception as e:
            # This block will catch any exceptions thrown by the operation
            print(f"An error occurred while saving session data: {e}")


    async def delete_session_data(self, session_id):
        """Delete session data from the database."""
        try:
            response = await self.supabase.table("sessions").delete().match({"session_id": session_id}).execute()
            if response.error:
                print(f"Error deleting session data: {response.error.message}")
            else:
                print("Session data deleted successfully.")
        except Exception as e:
            print(f"An error occurred while deleting session data: {e}")

    async def fetch_session_data(self, session_id):
        """Fetch session data from the database asynchronously for Python 3.8."""
        try:
            loop = asyncio.get_event_loop()  # For Python 3.7 and 3.8
            response = await loop.run_in_executor(
                None,  # Uses the default executor
                lambda: self.supabase.table("sessions").select("*").eq("session_id", session_id).execute()
            )

            # Directly access the 'data' attribute for the response content
            session_data = response.data
            if session_data:
                # Assuming you're interested in the first record if there are multiple
                return session_data[0] 
            else:
                print("No session data found.")
                return None
        except Exception as e:
            print(f"An error occurred while fetching session data: {e}")
            return None


    async def get_user_id(self, session_id):
        session_data = await self.fetch_session_data(session_id)
        return session_data[0].get('user_id') if session_data else None

    async def get_thread_id(self, session_id):
        try:
            print(f"Trying to get thread_id with session: {session_id} ")
            response =  self.supabase.table("sessions").select("*").eq("session_id", session_id).execute()
            
            # Assuming response.data contains the results
            session_data = response.data
           
            # Check if session_data is a list and not empty before accessing
            if isinstance(session_data, list) and len(session_data) > 0:
                print(f"Retrieved value from DB get_thread_id: {session_data[0].get('thread_id')} ")
                return session_data[0].get('thread_id')
            else:
                # Handle the case where no results are found or session_data is not as expected
                print(f"No session data found for session_id: {session_id}")
                return None
        except Exception as e:
            print(f"An error occurred while fetching session data: {e}")
            return None

    async def get_assistant_id(self, session_id):
        try:
            response =  self.supabase.table("sessions").select("*").eq("session_id", session_id).execute()
            
            # Assuming response.data contains the results
            session_data = response.data

            # Check if session_data is a list and not empty before accessing
            if isinstance(session_data, list) and len(session_data) > 0:
                return session_data[0].get('assistant_id')
            else:
                # Handle the case where no results are found or session_data is not as expected
                print(f"No session data found for session_id: {session_id}")
                return None
        except Exception as e:
            print(f"An error occurred while fetching session data: {e}")
            return None

    async def get_session_id(self, session_id):
        # In this context, get_session_id might not be necessary since you already have sid.
        # But if you need to validate its existence or fetch it for some reason, here's how:
        session_data = await self.fetch_session_data(session_id)
        return session_id if session_data else None   