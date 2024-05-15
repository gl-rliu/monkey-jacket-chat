import math
import random
from pathlib import Path
from .audio_generator import get_response_audio
from .character_dialogue import *
import statistics
import os
import re
from datetime import datetime, timedelta

AUDIO_CACHE_PATH = os.getcwd() + "/call_center_audio/"

CALLER_PATH_PREFIX = os.getcwd() + '/callers/'
conversation_state = {}
actual = "actual"
imposter = "imposter"
call_stage = "call_stage"
caller_name = "caller_name"
confidence_scores = "confidence_scores"
first_call = "first_call"
time_to_allow_input = "time_to_allow_input"
conversation_history = "conversation_history"
caller_question_count = 5
character_reveal_stage = caller_question_count + 1
character_question_count = 5
caller_reveal_stage = character_reveal_stage + character_question_count
sample_rate = 8000
confidence_threshold = 85.0

IGNORE_RESPONSE_TIME = False

cached_greeting_audio = {}
character_list = ["scarlett johansson"]

call_synopsis = ("you are impersonating a call center agent for a large bank.  People will occasionally call to "
                 "ask question about their account. You are receiving a call and will introduce yourself as Maria "
                 "from Acme Financial")


def load_greeting_cache(path):
    try:
        directory_listing = os.listdir(path)
    except FileNotFoundError:
        print(f"Directory '{path}' not found.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

    for character in character_list:
        cached_greeting_audio[character] = {}

    prefix_pattern = r'^(.*?)_greeting'
    character_pattern = r'_greeting-(.*?)\.wav'
    for file_name in directory_listing:
        prefix_match = re.search(prefix_pattern, file_name)
        prefix = prefix_match.group(1)
        character_match = re.search(character_pattern, file_name)
        character = character_match.group(1)
        cached_greeting_audio[character][prefix] = file_name

    print(f'Audio Cache: {cached_greeting_audio}')


def cache_greeting_audio(character, audio_bytes, new_caller):
    if new_caller:
        file_prefix = "initial"
    else:
        file_prefix = "return"

    file_name = f'{file_prefix}_greeting-{character}.wav'
    print(f'Caching {file_prefix} greeting for character: {character} filename: {file_name}')
    with open(AUDIO_CACHE_PATH + file_name, 'wb') as file:
        file.write(audio_bytes)

    cached_greeting_audio[character][file_prefix] = file_name


def get_cached_audio(audiofile):
    if audiofile:
        file_name = AUDIO_CACHE_PATH + audiofile
        try:
            with open(file_name, 'rb') as file:
                byte_array = bytearray(file.read())
                return byte_array
        except FileNotFoundError:
            print(f"File '{file_name}' not found.")
            return None
        except Exception as e:
            print(f"An error occurred: {e}")
            return None


def initialize_conversation(caller_id, conversation_id):
    caller_path = f"{CALLER_PATH_PREFIX}/{caller_id}"
    name_path = f"{caller_path}/caller_name.txt"

    real_character = random.choice(character_list)
    fake_character = real_character

    conversation_state[conversation_id] = {actual: real_character,
                                           imposter: fake_character,
                                           confidence_scores: [],
                                           call_stage: 0,
                                           first_call: True,
                                           time_to_allow_input: 0,
                                           conversation_history: []}
    conversation = conversation_state[conversation_id]

    if not Path(name_path).is_file():
        Path(caller_path).mkdir(parents=True, exist_ok=True)
    else:
        with open(name_path, "r") as file:
            conversation[caller_name] = file.readline()

        conversation[call_stage] = 1
        conversation[first_call] = False

        with open(f"{caller_path}/{conversation_id}.txt", "w") as file:
            print(f"call started.  First time: {conversation[first_call]} character: {conversation[actual]}",
                  file=file)

    return conversation


def get_initial_greeting(caller_id, conversation_id):  # Response  audio: bytes, text: str
    caller_path = f"{CALLER_PATH_PREFIX}/{caller_id}"
    conversation = initialize_conversation(caller_id, conversation_id)

    if not cached_greeting_audio:
        print("loading greeting cache")
        load_greeting_cache(AUDIO_CACHE_PATH)

    if conversation[first_call]:
        caller_status = "initial"
    else:
        caller_status = "return"

    conversation[conversation_history].append({"role": "system", "content": call_synopsis})
    if conversation[actual] in cached_greeting_audio and caller_status in cached_greeting_audio[conversation[actual]]:
        audio = get_cached_audio(cached_greeting_audio[conversation[actual]][caller_status])
        greeting_text = "Hello! This is Maria from Acme Financial. How can I assist you today?"
    else:
        if caller_status == "initial":
            greeting_text = get_greeting()
        else:
            greeting_text = get_greeting()
        audio = get_response_audio(conversation[actual], greeting_text)
        cache_greeting_audio(conversation[actual], audio, caller_status == "initial")

    conversation[conversation_history].append({"role": "assistant", "content": greeting_text})

    with open(f"{caller_path}/{conversation_id}.txt", "a") as file:
        print(f"system: {greeting_text}", file=file)

    audio_seconds = get_audio_length_pcmu(audio, sample_rate)

    conversation[time_to_allow_input] = datetime.now() + timedelta(seconds=audio_seconds)

    return {"text": greeting_text,
            "audio": audio,
            "stage": "greeting"}


def get_response(caller_id, conversation_id, request_phrase):  # Response audio: bytes, text: str
    conversation_path = f"{CALLER_PATH_PREFIX}/{caller_id}/{conversation_id}.txt"
    name_path = f"{CALLER_PATH_PREFIX}/{caller_id}/caller_name.txt"
    call_terminate = False
    if not Path(conversation_path).exists():
        print("Getting a response for a conversation that has not started.  Call get_initial_greeting first")
        return None

    conversation = conversation_state[conversation_id]

    if not IGNORE_RESPONSE_TIME and datetime.now() < conversation[time_to_allow_input]:
        print("ignoring input before the response is finished")
        return {"text": "", "audio": [], "terminate": False}

    conversation[conversation_history].append({"role": "user", "content": request_phrase})

    response_text = get_chat_response_with_history(conversation[conversation_history])
    response_audio = get_response_audio(conversation[imposter], response_text)

    conversation[conversation_history].append({"role": "assistant", "content": response_text})

    with open(conversation_path, "a") as file:
        print(f"caller: {request_phrase}", file=file)
        print(f"system: {response_text}", file=file)

    audio_seconds = get_audio_length_pcmu(response_audio, sample_rate)
    conversation[time_to_allow_input] = datetime.now() + timedelta(seconds=audio_seconds)

    return {"text": response_text, "audio": response_audio, "terminate": call_terminate}


def update_confidence_score(caller_id, conversation_id, confidence_score):
    conversation_path = f"{CALLER_PATH_PREFIX}/{caller_id}/{conversation_id}.txt"
    if not Path(conversation_path).exists():
        print("Updating score for a conversation that has not started.  Call get_initial_greeting first")
        return None

    conversation = conversation_state[conversation_id]

    conversation[confidence_scores].append(confidence_score)
    with open(conversation_path, "a") as file:
        print(
            f"confidence score: instance {confidence_score}, avg {statistics.fmean(conversation[confidence_scores])}, max {max(conversation[confidence_scores])}",
            file=file)


def get_audio_length_pcmu(byte_array, sample_rate):
    # Assuming 8-bit mu-law PCM encoding
    bytes_per_sample = 1

    # Calculate the number of samples
    num_samples = len(byte_array) // bytes_per_sample

    # Calculate the duration of the audio in seconds
    duration = math.ceil(num_samples / float(sample_rate))

    return duration


if __name__ == '__main__':
    # Guess the Character Round
    print(get_initial_greeting("mike", "123")["text"])
    print(get_response("mike", "123", "I need to reset my card pin")["text"])
    # print(get_response("mike", "123", "what is your name")["text"])
    # print(get_response("mike", "123", "what is your favourite color")["text"])
    # print(get_response("mike", "123", "what is your home address")["text"])
    # print(get_response("mike", "123", "what is your best friend")["text"])
    # print(get_response("mike", "123", "what is your wife's name")["text"])
    # print(get_response("mike", "123", "homer simpson")["text"])
    # print(get_response("mike", "123", "Caller Answer 1")["text"])
    # print(get_response("mike", "123", "Caller Answer 2")["text"])
    # print(get_response("mike", "123", "Caller Answer 3")["text"])
    # update_confidence_score("mike", "123", 90)
    # print(get_response("mike", "123", "Caller Answer 4")["text"])
    # print(get_response("mike", "123", "Caller Answer 5")["text"])
