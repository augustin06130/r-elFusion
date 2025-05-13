from pytube import YouTube

def download_video(url, output_path="outputs/video.mp4"):
    yt = YouTube(url)
    stream = yt.streams.filter(file_extension='mp4', progressive=True).get_highest_resolution()
    stream.download(filename=output_path)
    return output_path
