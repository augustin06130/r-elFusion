from utils.youtube_downloader import download_video
# from utils.text_fetcher import get_wikipedia_summary
# from utils.tts_generator import generate_audio
# from utils.video_editor import combine_video_audio

def main():
    print("🟡 Téléchargement de la vidéo...")
    video_path = download_video("https://www.youtube.com/watch?v=SrKiHTnLlLg")

    # print("🟢 Récupération du texte Wikipédia...")
    # text = get_wikipedia_summary("Python (langage)")

    # print("🔵 Génération audio...")
    # audio_path = generate_audio(text)

    # print("🟣 Montage final...")
    # combine_video_audio(video_path, audio_path, text)

    # print("✅ Montage terminé !")

if __name__ == "__main__":
    main()
