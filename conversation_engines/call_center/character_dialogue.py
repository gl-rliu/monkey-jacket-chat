from openai import OpenAI

client = OpenAI()

model = 'gpt-4-turbo'
system_prompt = ("you are impersonating a call center agent named Emily at private wealth management firm called Acme "
                 "Wealth.  You are handling a Funds transfer request.  Ask only one question at a time with no bullet "
                 "points or numbered lists.  Introduce yourself at the beginning of the conversation")


def get_greeting():
    user_prompt = "Hello."
    return get_chat_response(user_prompt, system_prompt)


def get_chat_response_with_history(conversation_history):
    completion = client.chat.completions.create(
        model=model,
        messages=conversation_history
    )
    return completion.choices[0].message.content


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
    print(get_greeting())
