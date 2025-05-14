import wikipedia

def get_wikipedia_summary(topic, sentences=5):
    wikipedia.set_lang("fr")
    summary = wikipedia.summary(topic, sentences=sentences)
    return summary
