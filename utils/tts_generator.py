from gtts import gTTS

def generate_audio(text, output_path="outputs/voice.mp3"):
    tts = gTTS(text, lang='fr')
    tts.save(output_path)
    return output_path
