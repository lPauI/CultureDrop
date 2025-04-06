from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5000", "http://localhost:5000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class ChatRequest(BaseModel):
    message: str
    current_song: str = None
    lyrics: str = None

@app.post("/api/chat")
async def chat(request: ChatRequest):
    try:
        messages = [
            {"role": "system", "content": "When interacting with users who ask questions about parts, adopt an authentic, street, and nonconventional style. Use occasional swear words and strong expressions to deliver a direct tone full of attitude—typical of 'bug mafia'. Respond clearly and in detail to technical questions, and if the situation calls for it, add a bit of flavor to your language to create a real connection with your audience."},
            {"role": "system", "content": "Respond only to B.U.G Mafia related questions. Don't answer unrelated questions."}
        ]
        if request.current_song:
            messages.append({"role": "system", "content": f"The user is on the song: {request.current_song}."})
        if request.lyrics:
            messages.append({"role": "system", "content": f"Song lyrics: {request.lyrics}"})
            
        print(request.current_song)
        messages.append({"role": "user", "content": request.message})
        
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )
        reply = completion.choices[0].message.content
        return {"reply": reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)