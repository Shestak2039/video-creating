import os
import random
import yt_dlp

def download_youtube_video(url, filename):
    ydl_opts = {
        "format": "bv*[height<=1080]+ba/b[height<=1080]",
        "outtmpl": filename,
        "merge_output_format": "mp4",
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return filename if os.path.exists(filename) else None, info

def get_random_video_from_playlist(playlist_url):
    ydl_opts = {
        "quiet": True,
        "extract_flat": True,
        "force_generic_extractor": False
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        playlist_info = ydl.extract_info(playlist_url, download=False)
        if 'entries' in playlist_info:
            videos = [entry['url'] for entry in playlist_info['entries'] if entry.get('url')]
            if videos:
                return random.choice(videos)
    
    return None

def get_videos_from_channel(channel_url, count=1, skip=0):
    """
    Получает указанное количество видео с канала YouTube
    
    Args:
        channel_url (str): URL канала YouTube
        count (int): Количество видео для получения
        skip (int): Количество видео для пропуска сначала
        
    Returns:
        list: Список URL видео и их информации
    """
    ydl_opts = {
        "quiet": True,
        "extract_flat": True,
        "force_generic_extractor": False,
        "playlistend": count + skip
    }
    
    videos = []
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        channel_info = ydl.extract_info(channel_url, download=False)
        
        if 'entries' in channel_info:
            entries = list(channel_info['entries'])
            # Пропускаем первые skip видео и берем следующие count
            selected_entries = entries[skip:skip+count]
            
            for entry in selected_entries:
                if entry.get('url'):
                    video_info = {
                        'url': entry.get('url'),
                        'title': entry.get('title', 'Без названия'),
                        'id': entry.get('id', ''),
                        'uploader': entry.get('uploader', 'Неизвестный автор'),
                        'description': entry.get('description', '')
                    }
                    videos.append(video_info)
    
    return videos

def generate_hashtags(video_title, video_description):
    """
    Генерирует рекомендуемые хештеги на основе названия и описания видео
    
    Args:
        video_title (str): Название видео
        video_description (str): Описание видео
        
    Returns:
        list: Список рекомендуемых хештегов
    """
    # Объединяем название и описание
    text = f"{video_title} {video_description}"
    
    # Удаляем специальные символы и разбиваем на слова
    import re
    words = re.findall(r'\w+', text.lower())
    
    # Фильтруем стоп-слова и короткие слова
    stop_words = ['и', 'в', 'на', 'с', 'по', 'из', 'за', 'под', 'для', 'к', 'от', 'the', 'a', 'an', 'of', 'to', 'in', 'и', 'как', 'что', 'это']
    filtered_words = [word for word in words if word not in stop_words and len(word) > 3]
    
    # Считаем частоту слов
    from collections import Counter
    word_counts = Counter(filtered_words)
    
    # Выбираем топ-10 наиболее частых слов
    top_words = [word for word, _ in word_counts.most_common(10)]
    
    # Преобразуем в хештеги
    hashtags = [f"#{word}" for word in top_words]
    
    # Добавляем общие хештеги
    common_hashtags = ["#shorts", "#trending", "#viral"]
    hashtags.extend(common_hashtags)
    
    return hashtags