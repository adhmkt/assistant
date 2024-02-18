# commands/command.py


import os
from openai import OpenAI
import asyncio
import urllib.parse

# Load OpenAI API Key
my_api_key = os.environ.get('OPENAI_API_KEY')

# OpenAI client setup
client = OpenAI(api_key=my_api_key)

class Command:
    async def execute(self, arguments):
        raise NotImplementedError("You should implement this!")

# commands/command.py

 # Make sure you're using an async client or adapt accordingly

class GenerateImageCommand(Command):
    
    async def execute(self, arguments):
        prompt = arguments['img_generation_prompt']
        proxied_image_url = await self.make_image(prompt)
        return proxied_image_url  # Return the proxied image URL

    async def make_image(self, prompt):
        proxied_image_url = None  # Initialize proxied_image_url
        print(f'The prompt sent to Dalle : {prompt}')
        try:
            # Use asyncio's event loop to run the synchronous code in an executor
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, lambda: client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                response_format="url",
                n=1
            ))

            # Extract the image URL
            original_image_url = response.data[0].url  # The original DALL·E-generated image URL
            
            # Encode the original image URL to be safely used as a query parameter
            encoded_image_url = urllib.parse.quote_plus(original_image_url)
            
            # Construct the proxied image URL using your server's proxy endpoint
            # Replace 'your_server_url' with the actual URL of your server
            # For example, if deploying to Heroku: 'https://your-app-name.herokuapp.com/image_proxy?url='
            proxy_endpoint = "http://127.0.0.1:5000/image_proxy?url="       
            proxied_image_url = proxy_endpoint + encoded_image_url
 
        except Exception as e:
            print(f"An error occurred creating the image: {e}")

        return proxied_image_url



class GetUsedCarPricesCommand(Command):
    async def execute(self, arguments):
        # Simulate asynchronous operation (e.g., fetching data from an API)
        await asyncio.sleep(2)  # Simulating a 2-second delay
        
        # Fake data for used car prices (replace with real data or API calls)
        car_prices = [
            {"make": "Toyota", "model": "Camry", "year": 2019, "price": 20000},
            {"make": "Honda", "model": "Civic", "year": 2018, "price": 18000},
            {"make": "Ford", "model": "Focus", "year": 2017, "price": 16000},
        ]

        # Create an HTML table to display the fake data
        table_html = "<table>"
        table_html += "<tr><th>Make</th><th>Model</th><th>Year</th><th>Price</th></tr>"
        for car in car_prices:
            table_html += f"<tr><td>{car['make']}</td><td>{car['model']}</td><td>{car['year']}</td><td>${car['price']}</td></tr>"
        table_html += "</table>"

        return table_html
