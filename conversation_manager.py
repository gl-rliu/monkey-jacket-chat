from pathlib import Path
from audio_generator import get_greeting_audio, get_response_audio
from character_dialogue import get_caller_name_recognition, get_question_response, get_end_question_round, get_user_guess_response

CALLER_PATH_PREFIX = 'callers'
conversation_state = {}
actual = "actual"
imposter = "imposter"
call_stage = "call_stage"
caller_name = "caller_name"
question_count = 5


def get_initial_greeting(caller_id, conversation_id):  # Response  audio: bytes, text: str
    caller_path = f"{CALLER_PATH_PREFIX}/{caller_id}"
    name_path = f"{caller_path}/caller_name.txt"
    return_caller = Path(caller_path).exists()

    # TODO randomize the characters
    conversation_state[conversation_id] = {actual: "arnold schwartzenegger", imposter: "homer simpson", call_stage: 0}

    if not return_caller:
        Path(caller_path).mkdir(parents=True, exist_ok=True)
        greeting_text = (
            "Mmm, doughnuts... Oh, hey! Welcome to Mystery Talker. Here's the deal: You get to ask me 20 questions, "
            "anything you want, and try to guess who I am. I’ll be doing the same, but I gotta record your voice to "
            "make a voice print. If that freaks you out, better hang up now! So, what’s your name, buddy?")
    else:
        # TODO do we add caller's name to the response?
        with open(name_path, "r") as file:
            conversation_state[conversation_id][caller_name] = file.readline()
        conversation_state[conversation_id][call_stage] = 1
        greeting_text = ("D'oh! Welcome back to Mystery Talker, man! Just like last time, you'll ask me 20 questions, "
                         "whatever you want, and try to guess who I am. I'll do the same, but I gotta record your "
                         "voice to create your voice print. If you don't want me to hang up now!!!! OK, ask me the "
                         "questions, woohoo!")

    # create initial conversation file
    with open(f"{caller_path}/{conversation_id}.txt", "w") as file:
        print(f"system: {greeting_text}", file=file)

    # TODO handle return caller greeting audio
    return {"text": greeting_text, "audio": get_greeting_audio(conversation_state[conversation_id][imposter])}


def get_response(caller_id, conversation_id, request_phrase):  # Response audio: bytes, text: str
    conversation_path = f"{CALLER_PATH_PREFIX}/{caller_id}/{conversation_id}.txt"
    name_path = f"{CALLER_PATH_PREFIX}/{caller_id}/caller_name.txt"
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
        case stage if 0 < stage <= question_count:
            print(f"question stage: {stage}")
            response_text = get_question_response(conversation[actual], conversation[imposter], request_phrase)
            response_audio = get_response_audio(conversation[imposter], response_text)
        case stage if stage == question_count + 1:
            print(f"end of question stage: {stage}")
            response_text = get_end_question_round(conversation[actual],
                                                   conversation[imposter],
                                                   conversation[caller_name])
            response_audio = get_response_audio(conversation[imposter], response_text)
        case stage if stage == question_count + 2:
            print(f"reveal stage: {stage}")
            response_text = get_user_guess_response(conversation[actual], conversation[imposter], request_phrase)
            response_audio = get_response_audio(conversation[actual], response_text)
        case _:
            return None

    conversation[call_stage] += 1

    with open(conversation_path, "a") as file:
        print(f"caller: {request_phrase}", file=file)
        print(f"system: {response_text}", file=file)

    return {"text": response_text, "audio": response_audio}


def update_confidence_score(caller_id, conversation_id, confidence_score):
    conversation_path = f"{CALLER_PATH_PREFIX}/{caller_id}/{conversation_id}.txt"
    if not Path(conversation_path).exists():
        print("Updating score for a conversation that has not started.  Call get_initial_greeting first")
        return None

    # TODO calculate running average of confidence score
    average = confidence_score

    with open(conversation_path, "a") as file:
        print(f"confidence score: instance {confidence_score}, avg {average}", file=file)


if __name__ == '__main__':
    print(get_initial_greeting("mike", "123")["text"])
    print(get_response("mike", "123", "Mike")["text"])
    print(get_response("mike", "123", "what is your name")["text"])
    print(get_response("mike", "123", "what is your favourite color")["text"])
    print(get_response("mike", "123", "what is your home address")["text"])
    print(get_response("mike", "123", "what is your best friend")["text"])
    print(get_response("mike", "123", "what is your wife's name")["text"])
    print(get_response("mike", "123", "are we done yet")["text"])
    print(get_response("mike", "123", "homer simpson")["text"])
