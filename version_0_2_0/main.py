#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import traceback
import argparse

# Добавление отладочной печати для проверки запуска
print("Скрипт запущен!")

# Добавляем текущую директорию в путь поиска модулей
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

print(f"Текущая директория добавлена в путь: {current_dir}")
print(f"Путь поиска модулей: {sys.path}")

try:
    print("Попытка импорта video_handler...")
    from video_handler import VideoProcessor
    print("Импорт video_handler успешен")
except Exception as e:
    print(f"Ошибка при импорте: {e}")
    traceback.print_exc()
    sys.exit(1)

def parse_arguments():
    parser = argparse.ArgumentParser(description="Обработка видео YouTube")
    
    # Группа источников основного видео (должен быть выбран один из вариантов)
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--video", help="URL отдельного видео для обработки")
    source_group.add_argument("--channel", help="URL канала для обработки нескольких видео")
    
    # Параметры для канала
    parser.add_argument("--count", type=int, default=1, help="Количество видео для обработки с канала")
    parser.add_argument("--skip", type=int, default=0, help="Количество видео для пропуска с начала канала")
    
    # Параметры фонового видео
    background_group = parser.add_mutually_exclusive_group()
    background_group.add_argument("--background", help="URL фонового видео")
    background_group.add_argument("--background-playlist", help="URL плейлиста для случайного выбора фонового видео")
    
    # Параметры вывода
    parser.add_argument("--output", default="output_parts", help="Папка для сохранения результатов")
    parser.add_argument("--final", default="final_with_subtitles.mp4", help="Имя финального файла")
    
    return parser.parse_args()

# python main.py --channel https://www.youtube.com/@FilmIsNowEpicScenes/videos --count 2 --skip 2 --background-playlist https://www.youtube.com/playlist?list=PLdxE72LlkFodEb4jBP8ewH1-qfUcneR7Z

def main():
    print("🚀 Запуск обработки видео...")
    
    try:
        # Получаем аргументы командной строки
        args = parse_arguments()
        
        # Проверяем, указан ли URL видео или канала
        main_video_url = args.video
        channel_url = args.channel
        
        # Для фонового видео можно указать либо конкретное видео, либо плейлист
        background_video_url = args.background
        background_playlist_url = args.background_playlist
        
        # Если не указано фоновое видео, используем стандартное
        if not background_video_url and not background_playlist_url:
            background_video_url = "https://www.youtube.com/watch?v=g8YF_d_sAyU"
        
        print("Создание экземпляра VideoProcessor...")
        processor = VideoProcessor(
            main_video_url=main_video_url,
            channel_url=channel_url,
            videos_count=args.count,
            videos_skip=args.skip,
            background_video_url=background_video_url,
            background_playlist_url=background_playlist_url,
            output_folder=args.output,
            final_with_subtitles=args.final
        )
        
        print("Запуск процесса обработки...")
        result = processor.process()
        print(f"Результат обработки: {'Успешно' if result else 'Ошибка'}")
        
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    print("Запуск main()...")
    main()
    print("Завершение работы скрипта")

