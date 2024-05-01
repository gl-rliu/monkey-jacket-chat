# genesys-chat


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

get_response_audio("arnold", "Who is your daddy and what does he do?")
- returns byte[] of mu-law PCM encoded audio

### Available characters
- arnold
- elmer
- piggy
- scarlett
- crash
- yoda
- freeman
- mario
- hussain
- homer