import asyncio
import aiopg
import json
import sys

class SessionManagerDB:
    def __init__(self, pool, client, DSN, sio):
        self.pool = pool
        self.client = client
        self.DSN = DSN
        self.sio = sio
        print("YOU GOT HERE", file=sys.stdout)

    @classmethod
    async def create(cls,DSN):
        """Asynchronous factory method to create a SessionManager instance with an initialized connection pool."""
        pool = await aiopg.create_pool(DSN)
        return cls(pool) 
    

    async def create_thread_for_sid(self, sid, db_session_id, assistant_id, user_id):
        """Creates a thread for the given session ID, assistant ID, and user ID."""
        try:
            # Example logic to create a thread (replace with your actual thread creation logic)
            loop = asyncio.get_running_loop()
            thread = await loop.run_in_executor(None, lambda: "thread-id-placeholder")  # Mock thread creation
            thread_id = thread if thread else None

            # Use the connection pool for database operations
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute("""
                        INSERT INTO session_data (sid, user_thread_id, user_assistant_id, user_id, thread_to_sid) 
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (sid) DO UPDATE 
                        SET user_thread_id = EXCLUDED.user_thread_id, user_assistant_id = EXCLUDED.user_assistant_id, 
                            user_id = EXCLUDED.user_id, thread_to_sid = EXCLUDED.thread_to_sid, updated_at = NOW()""",
                                      (db_session_id, thread_id, assistant_id, user_id, json.dumps({thread_id: db_session_id})))
            print(f"Thread created for new user: {thread_id} with SID: {db_session_id}")
            print(f"The sid created by socket: {sid}")
        except Exception as e:
            print(f"Error creating thread for SID {db_session_id}: {e}")

    async def get_user_id(self, sid ,sio):

        session_info = sio.get_session(sid)
        if session_info is None:
            return None  # No session info found for the SID
        db_session_id = session_info.get('session_id')

        """Retrieves the user ID for the given session ID."""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT user_id FROM session_data WHERE sid = %s", (db_session_id,))
                result = await cur.fetchone()
                return result[0] if result else None

    async def get_thread_id(self, sid, sio):

        session_info = sio.get_session(sid)
        if session_info is None:
            return None  # No session info found for the SID
        db_session_id = session_info.get('session_id')

        """Retrieves the thread ID for the given session ID."""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT user_thread_id FROM session_data WHERE sid = %s", (db_session_id,))
                result = await cur.fetchone()
                return result[0] if result else None

    # async def get_sid_by_thread_id(self, thread_id):
    #     """Retrieves the session ID for the given thread ID."""
    #     async with self.pool.acquire() as conn:
    #         async with conn.cursor() as cur:
    #             await cur.execute("SELECT sid FROM session_data WHERE thread_to_sid ->> %s IS NOT NULL", (thread_id,))
    #             result = await cur.fetchone()
    #             return result[0] if result else None

    async def get_assistant_id(self, sid, sio):
        session_info = sio.get_session(sid)
        if session_info is None:
            return None  # No session info found for the SID
        db_session_id = session_info.get('session_id')
        """Retrieves the assistant ID for the given session ID."""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT user_assistant_id FROM session_data WHERE sid = %s", (db_session_id,))
                result = await cur.fetchone()
                return result[0] if result else None

    async def remove_session(self, sid, sio):

        session_info = sio.get_session(sid)
        if session_info is None:
            return None  # No session info found for the SID
        db_session_id = session_info.get('session_id')
        """Removes the session data for the given session ID."""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("DELETE FROM session_data WHERE sid = %s", (db_session_id,))
                print(f"Session data removed for SID: {db_session_id}")


    def __init__(self, pool):
        self.pool = pool

    @classmethod
    async def create(cls, DSN):
        """Asynchronous factory method to create a SessionManagerDB instance with an initialized connection pool."""
        pool = await aiopg.create_pool(DSN)
        return cls(pool) 

    async def create_thread_for_sid(self, sid, assistant_id, user_id):
        """Creates a thread for the given session ID, assistant ID, and user ID."""
        try:
            loop = asyncio.get_running_loop()
            thread = await loop.run_in_executor(None, lambda: "thread-id-placeholder")  # Mock thread creation
            thread_id = thread if thread else None

            async with self.pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute("""
                        INSERT INTO session_data (sid, user_thread_id, user_assistant_id, user_id, thread_to_sid) 
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (sid) DO UPDATE 
                        SET user_thread_id = EXCLUDED.user_thread_id, user_assistant_id = EXCLUDED.user_assistant_id, 
                            user_id = EXCLUDED.user_id, thread_to_sid = EXCLUDED.thread_to_sid, updated_at = NOW()""",
                                      (sid, thread_id, assistant_id, user_id, json.dumps({thread_id: sid})))
            print(f"Thread created for new user: {thread_id} with SID: {sid}")
        except Exception as e:
            print(f"Error creating thread for SID {sid}: {e}")

class SessionManager:
    def __init__(self, client):
        self.client = client
        self.user_threads = {}
        self.user_assistant_ids = {}
        self.thread_to_sid = {}
        self.user_ids = {}

    @classmethod
    async def create(cls,DSN):
        """Asynchronous factory method to create a SessionManager instance with an initialized connection pool."""
        pool = await aiopg.create_pool(DSN)
        return cls(pool)     

    async def create_thread_for_sid(self, sid, assistant_id, user_id):
        try:
            loop = asyncio.get_running_loop()
            # Assuming client.beta.threads.create returns a Thread-like object
            thread = await loop.run_in_executor(None, self.client.beta.threads.create)
            # Access the 'id' attribute of the thread object (adjust according to the actual attribute name)
            self.user_threads[sid] = thread.id if hasattr(thread, 'id') else None
            self.user_assistant_ids[sid] = assistant_id
            self.user_ids[sid] = user_id 
            self.thread_to_sid[thread.id if hasattr(thread, 'id') else None] = sid
            print(f"Thread created for new user: {thread.id if hasattr(thread, 'id') else 'Unknown ID'} with SID: {sid}")
        except Exception as e:
            print(f"Error creating thread for SID {sid}: {e}")

    # Define other methods as needed


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
