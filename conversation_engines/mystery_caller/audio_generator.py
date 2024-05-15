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
          "homer simpson": "vWgQedHHDqGUvqr7A08O"}

cached_first_greeting_audio = {"homer simpson": "audio/initial_greeting-homer simpson.wav",
                               "crush the turtle": "audio/greeting-crush_as_elmer.wav",
                               "scarlett johansson": "audio/greeting-scarlett_as_piggy.wav"}
cached_return_greeting_audio = {"homer simpson": "audio/return_greeting-homer simpson.wav",
                                "crush the turtle": "audio/return_greeting-crush_as_elmer.wav",
                                "scarlett johansson": "audio/return_greeting-scarlett_as_piggy.wav"}


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
        if BYTE_ARRAY:
            byte_array = bytearray()
            # Read the response in chunks and write to the file
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                if chunk:  # Filter out keep-alive new chunks
                    byte_array.extend(chunk)

            return byte_array
        else:
            with open('audio/greeting-crush_as_elmer.wav', 'wb') as file:  # Open a file in binary write mode
                # Iterate over the response content in chunks and write to the file
                for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                    if chunk:  # Filter out keep-alive new chunks
                        file.write(chunk)
    else:
        # Print the error message if the request was not successful
        print(response.text)


def get_greeting_audio(voice_character, first_time):
    if first_time:
        cached_file = cached_first_greeting_audio[voice_character]
    else:
        cached_file = cached_return_greeting_audio[voice_character]
    if cached_file:
        try:
            with open(cached_file, 'rb') as file:
                byte_array = bytearray(file.read())
                return byte_array
        except FileNotFoundError:
            print(f"File '{cached_file}' not found.")
            return None
        except Exception as e:
            print(f"An error occurred: {e}")
            return None


if __name__ == '__main__':
    text = ("Oh, hey! Welcome to Mystery Talker. Here's the deal: You get to ask me some questions, "
            "anything you want, and try to guess who I am. I’ll be doing the same, but I gotta record your voice to "
            "make a voice print. If that freaks you out, better hang up now! So, what’s your name, buddy?")
    # text = ("Welcome back to Mystery Talker, man! Just like last time, you'll ask me some questions,"
    #         "whatever you want, and try to guess who I am. I'll do the same, but I gotta record your "
    #         "voice to create your voice print. If you don't want me to hang up now!!!! OK, ask me the "
    #         "questions")
    print(f"{len(get_response_audio('crush the turtle', text))} bytes were produced")
