import random
from pathlib import Path
from audio_generator import get_response_audio
from character_dialogue import *
import statistics
import os
import re

CALLER_PATH_PREFIX = 'callers'
conversation_state = {}
actual = "actual"
imposter = "imposter"
call_stage = "call_stage"
caller_name = "caller_name"
confidence_scores = "confidence_scores"
first_call = "first_call"
caller_question_count = 5
character_reveal_stage = caller_question_count + 1
character_question_count = 5
caller_reveal_stage = character_reveal_stage + character_question_count
confidence_threshold = 85.0

cached_greeting_audio = {}
character_list = ["arnold schwartzenegger",
                  "homer simpson",
                  "elmer fudd",
                  "miss piggy",
                  "scarlett johansson",
                  "crush the turtle",
                  "yoda",
                  "morgan freeman",
                  "super mario"
                  ]


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


def cache_greeting_audio(character, audio_bytes, new_caller):
    if new_caller:
        file_prefix = "initial"
    else:
        file_prefix = "return"

    file_name = f'audio/{file_prefix}_greeting-{character}.wav'
    with open(file_name, 'wb') as file:  # Open a file in binary write mode
        file.write(audio_bytes)

    cached_greeting_audio[character][file_prefix] = file_name


def get_cached_audio(audiofile):
    if audiofile:
        file_name = "audio/" + audiofile
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
    while fake_character == real_character:
        fake_character = random.choice(character_list)

    conversation_state[conversation_id] = {actual: real_character,
                                           imposter: fake_character,
                                           confidence_scores: [],
                                           call_stage: 0,
                                           first_call: True}
    conversation = conversation_state[conversation_id]

    if not Path(name_path).exists():
        Path(caller_path).mkdir(parents=True, exist_ok=True)
    else:
        with open(name_path, "r") as file:
            conversation[caller_name] = file.readline()

        conversation[call_stage] = 1
        conversation[first_call] = False

        with open(f"{caller_path}/{conversation_id}.txt", "w") as file:
            print(f"call started with actual: {conversation[actual]} and imposter: {conversation[imposter]}",
                  file=file)

    return conversation


def get_initial_greeting(caller_id, conversation_id):  # Response  audio: bytes, text: str
    caller_path = f"{CALLER_PATH_PREFIX}/{caller_id}"
    conversation = initialize_conversation(caller_id, conversation_id)

    if conversation[first_call]:
        caller_status = "initial"
    else:
        caller_status = "return"

    if caller_status in cached_greeting_audio[conversation[imposter]]:
        audio = get_cached_audio(cached_greeting_audio[conversation[imposter]][caller_status])
        greeting_text = "cached initial greeting"
    else:
        greeting_text = get_first_greeting(conversation[actual], conversation[imposter])
        audio = get_response_audio(conversation[imposter], greeting_text)
        cache_greeting_audio(conversation[imposter], audio, caller_status == "initial")

    with open(f"{caller_path}/{conversation_id}.txt", "a") as file:
        print(f"system: {greeting_text}", file=file)

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
    match conversation[call_stage]:
        case 0:  # post initial greeting is caller saying their name
            print(f"init stage: 0")
            conversation[caller_name] = request_phrase
            with open(name_path, "a") as file:
                print(conversation[caller_name], file=file)
            response_text = get_caller_name_recognition(conversation[actual],
                                                        conversation[imposter],
                                                        conversation[caller_name])
            response_audio = get_response_audio(conversation[imposter], response_text)
        case stage if 0 < stage < caller_question_count:
            print(f"caller_question_stage: {stage}")
            response_text = get_question_response(conversation[actual], conversation[imposter], request_phrase)
            response_text += ". Ask me another one."
            response_audio = get_response_audio(conversation[imposter], response_text)
        case stage if stage == caller_question_count:
            print(f"end_caller_question_stage: {stage}")
            response_text = get_question_response(conversation[actual], conversation[imposter], request_phrase)
            response_text += get_end_caller_question_round(conversation[actual],
                                                           conversation[imposter],
                                                           conversation[caller_name])
            response_audio = get_response_audio(conversation[imposter], response_text)
        case stage if stage == character_reveal_stage:
            print(f"character_reveal_stage: {stage}")
            response_text = get_user_guess_response(conversation[actual], request_phrase)
            response_text += get_guess_caller_first_question(conversation[actual])
            response_audio = get_response_audio(conversation[actual], response_text)
        case stage if character_reveal_stage < stage < caller_reveal_stage:
            print(f" character_question_stage: {stage}")
            if stage == caller_reveal_stage - 1:
                response_text = "final question. "
                response_text += get_guess_caller_question(conversation[actual])
            else:
                response_text = get_guess_caller_question(conversation[actual])
            response_audio = get_response_audio(conversation[actual], response_text)
        case stage if stage == caller_reveal_stage:
            print(f" caller_reveal_stage: {stage}")
            if (conversation[first_call] or
                    (len(conversation[confidence_scores]) > 0 and
                     max(conversation[confidence_scores]) >= confidence_threshold)):
                response_text = get_real_caller_response(conversation[actual],
                                                         conversation[caller_name])
            else:
                response_text = get_fake_caller_response(conversation[actual],
                                                         conversation[caller_name])

            response_audio = get_response_audio(conversation[actual], response_text)
            call_terminate = True
        case _:
            print(f" default_stage: {stage}")
            response_text = get_end_call_response(conversation[actual], conversation[caller_name])
            response_audio = get_response_audio(conversation[actual], response_text)
            call_terminate = True

    conversation[call_stage] += 1

    with open(conversation_path, "a") as file:
        print(f"caller: {request_phrase}", file=file)
        print(f"system: {response_text}", file=file)

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


if __name__ == '__main__':
    load_greeting_cache("audio")

    # Guess the Character Round
    print(get_initial_greeting("mike", "123")["text"])
    print(get_response("mike", "123", "Mike")["text"])
    print(get_response("mike", "123", "what is your name")["text"])
    print(get_response("mike", "123", "what is your favourite color")["text"])
    print(get_response("mike", "123", "what is your home address")["text"])
    print(get_response("mike", "123", "what is your best friend")["text"])
    print(get_response("mike", "123", "what is your wife's name")["text"])
    print(get_response("mike", "123", "homer simpson")["text"])
    print(get_response("mike", "123", "Caller Answer 1")["text"])
    print(get_response("mike", "123", "Caller Answer 2")["text"])
    print(get_response("mike", "123", "Caller Answer 3")["text"])
    update_confidence_score("mike", "123", 90)
    print(get_response("mike", "123", "Caller Answer 4")["text"])
    print(get_response("mike", "123", "Caller Answer 5")["text"])
