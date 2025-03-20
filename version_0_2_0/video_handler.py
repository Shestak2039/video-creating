#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time
from video_downloader import (
    download_youtube_video, 
    get_random_video_from_playlist, 
    get_videos_from_channel,
    generate_hashtags
)
from video_processor import (
    generate_subtitles, 
    add_subtitles_to_video, 
    combine_videos, 
    split_video
)

class VideoProcessor:
    def __init__(
        self, 
        main_video_url=None,
        channel_url=None,
        videos_count=1,
        videos_skip=0,
        background_playlist_url=None,
        background_video_url=None,
        output_folder="output_videos",
        final_video="final_full.mp4",
        subtitles_video="main_with_subtitles.mp4",
        final_with_subtitles="final_with_subtitles.mp4"
    ):
        self.main_video_url = main_video_url
        self.channel_url = channel_url
        self.videos_count = videos_count
        self.videos_skip = videos_skip
        self.background_playlist_url = background_playlist_url
        self.background_video_url = background_video_url
        self.output_folder = output_folder
        self.final_video = final_video
        self.subtitles_video = subtitles_video
        self.final_with_subtitles = final_with_subtitles
        
        self.main_video_file = "downloaded_main.mp4"
        self.background_video_file = "downloaded_background.mp4"
        self.subtitles_file = "subtitles.srt"
        self.audio_file = "audio.aac"
        
        # Создаем основную папку для вывода
        os.makedirs(self.output_folder, exist_ok=True)
        
        # Создаем папку для логов
        self.logs_folder = "video_logs"
        os.makedirs(self.logs_folder, exist_ok=True)
        
    def process(self):
        try:
            videos_to_process = []
            
            # Проверяем, указан ли URL канала
            if self.channel_url:
                print(f"🔍 Получение {self.videos_count} видео с канала (пропуск {self.videos_skip})...")
                videos_to_process = get_videos_from_channel(
                    self.channel_url, 
                    count=self.videos_count, 
                    skip=self.videos_skip
                )
                print(f"✅ Получено {len(videos_to_process)} видео с канала")
            elif self.main_video_url:
                # Если указан URL конкретного видео, используем его
                videos_to_process = [{'url': self.main_video_url, 'title': 'Основное видео'}]
            else:
                print("❌ Не указан ни URL канала, ни URL видео")
                return False
            
            processed_videos = []
            
            # Обрабатываем каждое видео
            for index, video_info in enumerate(videos_to_process):
                print(f"\n{'='*50}")
                print(f"🎬 Обработка видео {index+1}/{len(videos_to_process)}: {video_info.get('title', 'Без названия')}")
                print(f"{'='*50}\n")
                
                # Создаем уникальные имена файлов для каждого видео
                video_index = f"{index+1:02d}"
                main_video_file = f"downloaded_main_{video_index}.mp4"
                subtitles_file = f"subtitles_{video_index}.srt"
                subtitles_video = f"main_with_subtitles_{video_index}.mp4"
                final_with_subtitles = f"final_with_subtitles_{video_index}.mp4"
                
                # Создаем отдельную папку для каждого видео
                video_folder = os.path.join(self.output_folder, f"video_{video_index}")
                os.makedirs(video_folder, exist_ok=True)
                
                # Шаг 1: Скачивание видео
                print(f"🔻 Скачивание видео {video_index}...")
                main_video_file, video_details = download_youtube_video(video_info['url'], main_video_file)
                
                # Получаем полную информацию о видео
                video_title = video_details.get('title', video_info.get('title', 'Без названия'))
                video_description = video_details.get('description', video_info.get('description', ''))
                video_uploader = video_details.get('uploader', video_info.get('uploader', 'Неизвестный автор'))
                video_id = video_details.get('id', video_info.get('id', ''))
                
                # Создаем безопасное имя для папки с видео (удаляем недопустимые символы)
                safe_title = ''.join(c for c in video_title if c.isalnum() or c in ' _-')
                safe_title = safe_title.strip()
                if len(safe_title) > 50:  # Ограничиваем длину имени папки
                    safe_title = safe_title[:50]
                
                # Создаем именованную папку для конкретного видео внутри video_XX
                parts_folder = os.path.join(video_folder, f"{safe_title}")
                os.makedirs(parts_folder, exist_ok=True)
                
                # Генерируем хештеги
                hashtags = generate_hashtags(video_title, video_description)
                
                print(f"✅ Видео загружено: {main_video_file}")
                print(f"\n{'*'*50}")
                print(f"📋 ИНФОРМАЦИЯ О ВИДЕО {video_index}:")
                print(f"{'*'*50}")
                print(f"🏷️ Название: {video_title}")
                print(f"👤 Автор: {video_uploader}")
                print(f"🔖 Рекомендуемые хештеги: {' '.join(hashtags)}")
                print(f"{'*'*50}\n")
                
                # Сохраняем информацию о видео в лог-файл в папке видео
                log_file = os.path.join(video_folder, "video_info.txt")
                with open(log_file, 'w', encoding='utf-8') as f:
                    f.write(f"ИНФОРМАЦИЯ О ВИДЕО {video_index}\n")
                    f.write(f"{'='*50}\n")
                    f.write(f"Название: {video_title}\n")
                    f.write(f"Автор: {video_uploader}\n")
                    f.write(f"URL: {video_info['url']}\n")
                    f.write(f"ID: {video_id}\n\n")
                    f.write(f"ОПИСАНИЕ:\n{video_description}\n\n")
                    f.write(f"РЕКОМЕНДУЕМЫЕ ХЕШТЕГИ:\n{' '.join(hashtags)}\n")
                
                # Выбор фонового видео из плейлиста, если предоставлен URL плейлиста
                if self.background_playlist_url and not self.background_video_url:
                    background_video_url = get_random_video_from_playlist(self.background_playlist_url)
                    if not background_video_url:
                        print("❌ Не удалось получить видео из плейлиста")
                        continue
                else:
                    background_video_url = self.background_video_url
                
                background_video_file = f"downloaded_background_{video_index}.mp4"
                print("🔻 Скачивание фонового видео...")
                background_video_file, _ = download_youtube_video(background_video_url, background_video_file)
                print(f"✅ Фоновое видео загружено: {background_video_file}")
                
                # Шаг 2: Генерация субтитров
                print("🔊 Генерация субтитров...")
                subtitles_file = generate_subtitles(main_video_file, subtitles_file)
                print(f"✅ Субтитры созданы: {subtitles_file}")
                
                # Сохраняем копию субтитров в папку видео
                subtitles_copy = os.path.join(video_folder, "subtitles.srt")
                with open(subtitles_file, 'r', encoding='utf-8') as src, open(subtitles_copy, 'w', encoding='utf-8') as dst:
                    dst.write(src.read())
                
                # Шаг 3: Добавление субтитров к основному видео
                print("🎬 Добавление субтитров к видео...")
                subtitles_video = add_subtitles_to_video(
                    main_video_file, 
                    subtitles_file, 
                    subtitles_video
                )
                print(f"✅ Видео с субтитрами создано: {subtitles_video}")
                
                # Шаг 4: Объединение видео
                print("🛠️ Объединение видео...")
                final_with_subtitles = combine_videos(
                    subtitles_video,
                    background_video_file,
                    final_with_subtitles
                )
                print(f"✅ Объединенное видео создано: {final_with_subtitles}")
                
                # Сохраняем копию полного видео в папку видео
                full_video_copy = os.path.join(video_folder, "full_video.mp4")
                import shutil
                shutil.copy(final_with_subtitles, full_video_copy)
                
                # Шаг 5: Разбиение на части
                print("✂️ Разбиение на части...")
                output_parts_folder = split_video(final_with_subtitles, parts_folder)
                print(f"✅ Нарезки сохранены в папке: {output_parts_folder}")
                
                # Добавляем информацию о хештегах в отдельный файл в папке с нарезками
                hashtag_file = os.path.join(parts_folder, "hashtags.txt")
                with open(hashtag_file, 'w', encoding='utf-8') as f:
                    f.write(f"РЕКОМЕНДУЕМЫЕ ХЕШТЕГИ ДЛЯ ВИДЕО {video_index}\n")
                    f.write(f"{'='*50}\n")
                    f.write(f"Название: {video_title}\n\n")
                    f.write(f"Хештеги:\n{' '.join(hashtags)}\n")
                
                # Сохраняем информацию об обработанном видео
                processed_videos.append({
                    'index': video_index,
                    'title': video_title,
                    'folder': video_folder,
                    'parts_folder': parts_folder
                })
                
                # Шаг 6: Очистка временных файлов
                self.cleanup([
                    main_video_file,
                    background_video_file,
                    subtitles_file,
                    f"audio_{video_index}.aac",
                    subtitles_video,
                    final_with_subtitles
                ])
                
                # Делаем небольшую паузу между обработкой видео
                if index < len(videos_to_process) - 1:
                    print("⏳ Пауза перед обработкой следующего видео...")
                    time.sleep(2)
            
            # Создаем итоговый отчет о всех обработанных видео
            summary_file = os.path.join(self.output_folder, "processing_summary.txt")
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(f"ОТЧЕТ О ОБРАБОТКЕ ВИДЕО\n")
                f.write(f"{'='*50}\n\n")
                f.write(f"Всего обработано видео: {len(processed_videos)}\n\n")
                
                for video in processed_videos:
                    f.write(f"Видео {video['index']}: {video['title']}\n")
                    f.write(f"Папка: {video['folder']}\n")
                    f.write(f"Папка с нарезками: {video['parts_folder']}\n")
                    f.write(f"{'-'*30}\n")
            
            print(f"\n{'='*50}")
            print(f"✅ Обработка всех видео завершена!")
            print(f"✅ Каждое видео сохранено в отдельной папке внутри: {self.output_folder}")
            print(f"✅ Итоговый отчет: {summary_file}")
            print(f"{'='*50}\n")
            
            return True
            
        except Exception as e:
            print(f"❌ Произошла ошибка: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def cleanup(self, files_to_remove):
        """Удаляет временные файлы после обработки, оставляя только нарезанные видео"""
        print("🧹 Очистка временных файлов...")
        
        for file in files_to_remove:
            if os.path.exists(file):
                try:
                    os.remove(file)
                    print(f"  ✓ Удален файл: {file}")
                except Exception as e:
                    print(f"  ✗ Не удалось удалить файл {file}: {e}")
        
        print("✅ Очистка завершена. Оставлены только видео в соответствующих папках.")