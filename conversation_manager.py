from pathlib import Path
from audio_generator import get_greeting_audio, get_response_audio
from character_dialogue import *
import statistics

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
confidence_threshold = 0.80


def get_initial_greeting(caller_id, conversation_id):  # Response  audio: bytes, text: str
    caller_path = f"{CALLER_PATH_PREFIX}/{caller_id}"
    name_path = f"{caller_path}/caller_name.txt"

    # TODO randomize the characters
    conversation_state[conversation_id] = {actual: "arnold schwartzenegger",
                                           imposter: "homer simpson",
                                           confidence_scores: [],
                                           call_stage: 0,
                                           first_call: True}
    conversation = conversation_state[conversation_id]

    if not Path(name_path).exists():
        Path(caller_path).mkdir(parents=True, exist_ok=True)
        greeting_text = (
            "Mmm, doughnuts... Oh, hey! Welcome to Mystery Talker. Here's the deal: You get to ask me some questions, "
            "anything you want, and try to guess who I am. I’ll be doing the same, but I gotta record your voice to "
            "make a voice print. If that freaks you out, better hang up now! So, what’s your name, buddy?")
    else:
        # TODO do we add caller's name to the response?
        with open(name_path, "r") as file:
            conversation[caller_name] = file.readline()

        conversation[call_stage] = 1
        conversation[first_call] = False
        greeting_text = ("D'oh! Welcome back to Mystery Talker, man! Just like last time, you'll ask me some questions,"
                         "whatever you want, and try to guess who I am. I'll do the same, but I gotta record your "
                         "voice to create your voice print. If you don't want me to hang up now!!!! OK, ask me the "
                         "questions, woohoo!")

    # create initial conversation file
    with open(f"{caller_path}/{conversation_id}.txt", "w") as file:
        print(f"system: {greeting_text}", file=file)

    return {"text": greeting_text,
            "audio": get_greeting_audio(conversation[imposter], conversation[first_call]),
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
            with open(name_path, "w") as file:
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
                     statistics.fmean(conversation[confidence_scores]) >= confidence_threshold)):
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
        print(f"confidence score: instance {confidence_score}, avg {statistics.fmean(conversation[confidence_scores])}",
              file=file)


if __name__ == '__main__':
    # Guess the Character Round
    print(get_initial_greeting("mike", "123")["text"])
    # print(get_response("mike", "123", "Mike")["text"])
    print(get_response("mike", "123", "what is your name")["text"])
    print(get_response("mike", "123", "what is your favourite color")["text"])
    print(get_response("mike", "123", "what is your home address")["text"])
    print(get_response("mike", "123", "what is your best friend")["text"])
    print(get_response("mike", "123", "what is your wife's name")["text"])
    print(get_response("mike", "123", "homer simpson")["text"])
    print(get_response("mike", "123", "Caller Answer 1")["text"])
    print(get_response("mike", "123", "Caller Answer 2")["text"])
    print(get_response("mike", "123", "Caller Answer 3")["text"])
    print(get_response("mike", "123", "Caller Answer 4")["text"])
    print(get_response("mike", "123", "Caller Answer 5")["text"])
