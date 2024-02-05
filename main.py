# uvicorn main:app
# uvicorn main:app --reload

# Main Imports
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

# Custom Function Imports
from functions.database import store_messages, reset_messages
from functions.openai_requests import convert_audio_to_text, get_chat_response
from functions.text_to_speech import convert_text_to_speech

# Initialize App
app = FastAPI()

# CORS - Origins
origins = ["*"]

# CORS - Middleware
app.add_middleware(CORSMiddleware,
                   allow_origins=origins,
                   allow_credentials=True,
                   allow_methods=["*"],
                   allow_headers=["*"])


# Check health
@app.get("/health")
async def check_health():
    return {"message": "healthy"}


# Reset message
@app.get("/reset")
async def reset_conversation():
    reset_messages()
    return {"message": "conversation reset"}


# Get audio
@app.post("/post-audio/")
async def post_audio(file: UploadFile = File(...)):
    # # Get Saved audio
    # audio_input = open("voice.mp3", "rb")

    # Save file from frontend
    with open(file.filename, "wb") as buffer:
        buffer.write(file.file.read())
    audio_input = open(file.filename, "rb")

    # Decode audio
    message_decoded = convert_audio_to_text(audio_input)

    # Guard: Ensure message decoded:
    if not message_decoded:
        return HTTPException(status_code=400, detail="Failed to decode audio")

    # get ChatGPT response
    chat_response = get_chat_response(message_decoded)

    # Store messages
    store_messages(message_decoded, chat_response)

    print(chat_response)
    # Guard: Ensure message decoded:
    if not chat_response:
        return HTTPException(status_code=400, detail="Failed to get chat response")

    # Convert chat response to audio
    audio_output = convert_text_to_speech(chat_response)

    print(audio_output)

    # Guard: Ensure message decoded:
    if not audio_output:
        return HTTPException(status_code=400, detail="Failed to get eleven labs audio response")

    # Create a generator that yield chunks of data

    def interfile():
        yield audio_output

    # Return audio file
    return StreamingResponse(interfile(), media_type="application/octet-stream")
