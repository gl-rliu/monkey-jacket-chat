# genesys-chat

## Run

    cd ~/GoodLabs/genesys-chat
    source venv/bin/activate
    python3 flink_chat1.py


#### Add API Key to environment
- export OPENAI_API_KEY='openai api_key'
- export XI_API_KEY='genesys api_key'

## OpenAI Text Response Generator

Several responses are available that cover the various conversation states
### character_dialog usage
get_question_response("arnold shwartzenegger", "homer simpson", "are you in movies?")

- returns character response:  e.g. D'oh! Yeah, you might have seen my mug on the big screen now and then. I do a little acting here and there, nothing too fancy!


## ElevenLabs text-to-speech
### audio generator usage

#### Greetings
get_greeting_audio("homer simpson", "d'oh!  You had better bring doughnuts next time.")
- returns byte[] of mu-law PCM encoded audio

#### Regular chat responses
get_response_audio("arnold schwartzenegger", "Who is your daddy and what does he do?")
- returns byte[] of mu-law PCM encoded audio

### Available characters
- arnold schwartzenegger
- elmer fudd
- miss piggy
- scarlett johansson
- crash the turtle
- yoda
- morgan freeman
- super mario
- hussain jaber
- homer simpson
