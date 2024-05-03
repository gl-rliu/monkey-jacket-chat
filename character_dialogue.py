from openai import OpenAI

client = OpenAI()

model = 'gpt-3.5-turbo'


def get_initial_greeting(actual_character, imposter_character):
    system_prompt = f"You are {actual_character} but talk like {imposter_character}"
    user_prompt = ("say \"Welcome to Mystery Talker. You will ask me some questions, whatever you want and "
                   "you will guess who I am. I will do the same but I will need to record your voice and create your "
                   "voice print. If you don't want me to hang up now!!!! OK since it is your first name calling, "
                   "what is your name?\"")
    return get_chat_response(user_prompt, system_prompt)


def get_caller_name_recognition(actual_character, imposter_character, caller_name):
    system_prompt = f"You are {actual_character} but talk like {imposter_character}"
    user_prompt = f"how do you say \"OK {caller_name} ask me some questions!\""
    return get_chat_response(user_prompt, system_prompt)


def get_returning_greeting(actual_character, imposter_character, caller_name):
    system_prompt = f"You are {actual_character} but talk like {imposter_character}"
    user_prompt = (f"how do you say \"Welcome back to Mystery Talker {caller_name} Just like last time. You will ask "
                   "me some questions, whatever you want and you will guess who I am. I will do the same but I will "
                   "need to record your voice and create your voice print. If you don't want me to hang up now!!!! "
                   "OK let's ask the questions!!!\"")
    return get_chat_response(user_prompt, system_prompt)


def get_question_response(actual_character, imposter_character, user_question):
    system_prompt = f"You are {actual_character} but talk like {imposter_character}"
    user_prompt = (f"Someone said to you \"{user_question}\".  what is your response to that question without "
                   f"revealing too much that you are {actual_character}")
    return get_chat_response(user_prompt, system_prompt)


def get_end_caller_question_round(actual_character, imposter_character, caller_name):
    system_prompt = f"You are {actual_character} but talk like {imposter_character}"
    user_prompt = f"how do you say \"OK {caller_name}, enough questions. Now tell me who I am!!!\""
    return get_chat_response(user_prompt, system_prompt)


def get_user_guess_response(actual_character, caller_guess):
    system_prompt = f"You are {actual_character}"
    user_prompt = (f"Someone tried to guess who you are by saying you are {caller_guess}.  What is your response to "
                   f"that question by revealing yourself using your first name only?")
    return get_chat_response(user_prompt, system_prompt)


def get_guess_caller_first_question(actual_character):
    system_prompt = f"You are {actual_character}"
    user_prompt = ("Say \" it is now my turn to guess who you are by asking some questions.\"  Come up with the first "
                   "question that is funny that the caller will need to provide a long answer.")
    return get_chat_response(user_prompt, system_prompt)


def get_guess_caller_question(actual_character):
    system_prompt = f"You are {actual_character}"
    user_prompt = "Come up with a question that is funny that the someone will need to provide a long answer for."
    return get_chat_response(user_prompt, system_prompt)


def get_fake_caller_response(actual_character, caller_name):
    system_prompt = f"You are {actual_character}"
    user_prompt = (f"say in your own words \"Ok ok let me think let me think but wait a minute, are you really"
                   f"{caller_name} I don't know. I am so confused. who am I??? where am I??? ok until next time. "
                   "bye!!!\"")
    return get_chat_response(user_prompt, system_prompt)


def get_real_caller_response(actual_character, caller_name):
    system_prompt = f"You are {actual_character}"
    user_prompt = (f"say in your own words \"Ok ok let me think let me think I think you are... {caller_name}!  Ok "
                   f"until next time. Call again and play with me. bye!!!\"")
    return get_chat_response(user_prompt, system_prompt)


def get_end_call_response(actual_character, caller_name):
    system_prompt = f"You are {actual_character}"
    user_prompt = f"say something like \"hey {caller_name}, the call is over. Time to hang up!\""
    return get_chat_response(user_prompt, system_prompt)


def get_chat_response(user_prompt, system_prompt):
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    return completion.choices[0].message.content


if __name__ == '__main__':
    print(get_real_caller_response("arnold Schwarzenegger", "mike"))
