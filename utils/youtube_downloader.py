# from pytube import YouTube

# def download_video(url, output_path="outputs/video.mp4"):
#     yt = YouTube(url)
#     stream = yt.streams.filter(file_extension='mp4', progressive=True).get_highest_resolution()
#     stream.download(filename=output_path)
#     return output_path

import yt_dlp

def download_video(url, output_path="outputs/video.mp4"):
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]',
        'outtmpl': output_path,
        'quiet': True,
        'noplaylist': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    return output_path

