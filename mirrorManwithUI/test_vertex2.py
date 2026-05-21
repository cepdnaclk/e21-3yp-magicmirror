import os
import asyncio
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_PATH')
client = genai.Client(vertexai=True, project=os.getenv('GEMINI_PROJECT_ID'), location='us-central1')

async def test():
    try:
        async with client.aio.live.connect(model='gemini-2.0-flash', config=types.LiveConnectConfig(response_modalities=['AUDIO'])) as s:
            await s.send(input='hello', end_of_turn=True)
            async for r in s.receive():
                print('Success!')
                break
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(test())
