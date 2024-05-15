import requests
import os

CHUNK_SIZE = 1024  # Size of chunks to read/write at a time
XI_API_KEY = os.environ["XI_API_KEY"]  # Your API key for authentication
BYTE_ARRAY = True

voices = {"arnold schwartzenegger": "4q1HMIvKfgbjxb0BZsu3",
          "elmer fudd": "7BXee8r6HkvGL1OZIoEb",
          "miss piggy": "I6hJhvdUjFywlRS2sHr1",
          "scarlett johansson": "LJwyTpb1P1Y0YgmwA1cU",
          "crush the turtle": "O2Jg7hvavg2CM92Adt5T",
          "yoda": "OPPPrIAzqxpRo0z4bVUt",
          "morgan freeman": "cKjPC0QFrO0D9852wMzs",
          "super mario": "lXteNbvxCHpyDoNeWC0b",
          "hussain jaber": "ul8JnhojCgF8iA2WgCjz",
          "homer simpson": "vWgQedHHDqGUvqr7A08O",
          "emily": "qKTZGZRubYFEhl3ZqFjn"}


def get_response_audio(voice_character, response_text):
    voice_id = voices[voice_character]
    # Construct the URL for the Text-to-Speech API request
    tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream"

    # Set up headers for the API request, including the API key for authentication
    headers = {
        "Accept": "application/json",
        "xi-api-key": XI_API_KEY
    }

    # Set up the data payload for the API request, including the text and voice settings
    data = {
        "text": response_text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.8,
            "style": 0.0,
            "use_speaker_boost": True
        }
    }

    # set output format to be mu-law PCM for Genesys AudioHook support
    querystring = {"output_format": "ulaw_8000"}

    # Make the POST request to the TTS API with headers and data, enabling streaming response
    response = requests.post(tts_url, headers=headers, json=data, stream=True, params=querystring)

    # Check if the request was successful
    if response.ok:
        byte_array = bytearray()
        # Read the response in chunks and write to the file
        for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
            if chunk:  # Filter out keep-alive new chunks
                byte_array.extend(chunk)

        return byte_array
    else:
        # Print the error message if the request was not successful
        print(response.text)
