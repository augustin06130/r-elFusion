# 🎬 Auto-Shorts Generator – Fully Automated TikTok / Reels / Shorts Creation from Any Theme

**Auto-Shorts Generator** is a fully automated pipeline for creating short-form videos (TikToks, YouTube Shorts, Instagram Reels) from a **single theme input** like `horror`, `sci-fi`, or `history`.

Powered by Reddit, multilingual TTS (`xtts-v2`), and AI video editing tools, this project transforms viral Reddit content into engaging, ready-to-publish short videos **with subtitles in multiple languages** — in just one click.

---

## 🧠 How It Works

1. **Theme Input**: You provide a theme (e.g., `horror`)
2. **Content Scraping**: The script fetches the top post from the relevant subreddit (e.g., `/r/horror`) using Reddit's API
3. **Text Processing**:
   - Parses long-form posts or comments into coherent narrative
   - Translates the story into multiple languages
   - Breaks the text into speech-friendly segments (1–1.5 min per segment)
4. **Voice Generation**: Uses [`xtts-v2`](https://huggingface.co/coqui/XTTS-v2) for zero-shot multilingual voice synthesis
5. **Video Creation**:
   - Downloads a relevant background video from YouTube
   - Crops it to vertical (9:16) format
   - Adds the voiceover and generates matching subtitles
6. **Output**:
   - Multiple videos (1 per language)
   - All videos are export-ready for TikTok, Shorts, and Reels

---

## 📦 Installation

### 1. Clone the Repository

```bash
git clone git@github.com:augustin06130/r-elFusion.git
cd r-elFusion
````

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

> This includes `huggingface_hub`, `praw`, `moviepy`, `openai`, `yt_dlp`, etc.

### 3. Download the Voice Model

Run this script to automatically download the [`xtts-v2`](https://huggingface.co/coqui/XTTS-v2) model hosted on [Hugging Face](https://huggingface.co/):

```bash
cd xtts-v2_Docker_API
python download_model.py
```

This will create a local folder `xtts-v2-model/` with the necessary voice model files (\~1.8 GB).

---

## 🔊 XTTS-v2 Voice Model

This project uses **XTTS-v2** for high-quality, zero-shot, multilingual voice generation. Due to GitHub's 100MB file size limit, the model is hosted on **[XTTS-v2](https://huggingface.co/coqui/XTTS-v2)** and is automatically downloaded using the script below:

### `download_model.py` (included in the repo):

```python
from huggingface_hub import snapshot_download
import os

model_dir = "xtts-v2-model"

if not os.path.isdir(model_dir):
    print("Downloading XTTS-v2 model from Hugging Face...")
    snapshot_download(
        repo_id="https://huggingface.co/coqui/XTTS-v2",
        repo_type="model",
        local_dir=model_dir,
        local_dir_use_symlinks=False
    )
    print("Model downloaded.")
else:
    print("Model already present.")
```

---

## 🚀 Example Usage

Generate short videos in multiple languages from a theme:

```bash
python main.py --theme horror --languages en fr es
```

* Fetches Reddit stories from `/r/horror`
* Converts and narrates them in English, French, and Spanish
* Creates video files with synced audio and subtitles
* Outputs are saved in `/output/` and are ready for upload

---

## ⚠️ Licensing Notice

This project uses the [`xtts-v2`](https://huggingface.co/coqui/XTTS-v2) model developed by [Coqui](https://coqui.ai). The model is redistributed via Hugging Face and subject to its original license. You are responsible for ensuring that your use of the model complies with [Coqui's license and terms of use](https://huggingface.co/coqui/XTTS-v2#license).

This repository itself is licensed under **MIT**.

---

## 🧰 Requirements (summary)

* Python 3.8+
* [`huggingface_hub`](https://pypi.org/project/huggingface-hub/)
* `moviepy`, `nltk`
* `openai`
* `praw` (Reddit API wrapper)

Full list in `requirements.txt`

---

## 📈 Roadmap

* [x] Voice cloning support using XTTS speaker embeddings
* [x] Web UI or desktop GUI interface
* [ ] Scheduled auto-posting to TikTok / YouTube / Instagram

---

## 🤝 Contributing

Pull requests are welcome! Please open an issue first to discuss major changes or feature ideas.

---

## 📬 Contact

Questions? Feedback? Open an issue or reach me at `nicauglazic@gmail.com`.

---

## 🧠 Credits

* [Coqui XTTS-v2](https://huggingface.co/coqui/XTTS-v2) for multilingual voice synthesis
* [Hugging Face Hub](https://huggingface.co/) for model hosting
* [Reddit API](https://www.reddit.com/dev/api/) for story sourcing
* [MoviePy](https://zulko.github.io/moviepy/) for video composition
