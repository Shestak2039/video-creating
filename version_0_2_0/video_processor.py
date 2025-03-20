import os
import subprocess
import whisper

def get_video_duration(video_file):
    result = subprocess.run(
        ["ffprobe", "-i", video_file, "-show_entries", "format=duration", "-v", "quiet", "-of", "csv=p=0"],
        capture_output=True, text=True
    )
    return float(result.stdout.strip())

def get_video_info(video_file):
    """
    Получает информацию о видео файле
    
    Args:
        video_file (str): Путь к видео файлу
        
    Returns:
        dict: Словарь с информацией о видео
    
    Raises:
        ValueError: Если не удается получить информацию о видео
        FileNotFoundError: Если файл не существует
    """
    # Проверяем существование файла
    if not os.path.exists(video_file):
        print(f"❌ Файл не существует: {video_file}")
        raise FileNotFoundError(f"Файл не существует: {video_file}")
        
    try:
        # Получаем разрешение видео
        resolution_cmd = [
            "ffprobe", "-v", "error", "-select_streams", "v:0", 
            "-show_entries", "stream=width,height", "-of", "csv=p=0", video_file
        ]
        resolution_result = subprocess.run(resolution_cmd, capture_output=True, text=True)
        
        # Проверяем, что вывод не пустой
        if not resolution_result.stdout.strip():
            error_msg = f"Не удалось получить разрешение видео: {video_file}"
            print(f"❌ {error_msg}")
            raise ValueError(error_msg)
            
        width, height = map(int, resolution_result.stdout.strip().split(','))
            
        # Получаем продолжительность видео
        duration_result = subprocess.run(
            ["ffprobe", "-i", video_file, "-show_entries", "format=duration", "-v", "quiet", "-of", "csv=p=0"],
            capture_output=True, text=True
        )
        
        if not duration_result.stdout.strip():
            error_msg = f"Не удалось получить длительность видео: {video_file}"
            print(f"❌ {error_msg}")
            raise ValueError(error_msg)
            
        duration = float(duration_result.stdout.strip())
        
        # Получаем битрейт видео
        bitrate_cmd = [
            "ffprobe", "-v", "error", "-select_streams", "v:0", 
            "-show_entries", "stream=bit_rate", "-of", "csv=p=0", video_file
        ]
        bitrate_result = subprocess.run(bitrate_cmd, capture_output=True, text=True)
        
        # Для битрейта допускаем пустое значение (не все видео имеют его)
        bitrate = bitrate_result.stdout.strip() if bitrate_result.stdout.strip() else "неизвестно"
            
        return {
            'width': width,
            'height': height,
            'duration': duration,
            'duration_formatted': format_time(duration),
            'bitrate': bitrate
        }
        
    except Exception as e:
        print(f"❌ Ошибка при получении информации о видео {video_file}: {e}")
        import traceback
        traceback.print_exc()
        raise

def format_time(seconds):
    """
    Форматирует секунды в формат ЧЧ:ММ:СС
    
    Args:
        seconds (float): Время в секундах
        
    Returns:
        str: Форматированное время
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"

def generate_subtitles(video_file, subtitles_file="subtitles.srt"):
    print("🔊 Извлечение аудио из видео...")
    audio_file = os.path.splitext(video_file)[0] + ".wav"
    
    # Instead of trying to copy the audio codec, we'll convert it to WAV format
    # which is well supported by whisper and ffmpeg
    subprocess.run([
        "ffmpeg", 
        "-i", video_file, 
        "-vn",            # No video
        "-ar", "16000",   # Audio sample rate that whisper expects
        "-ac", "1",       # Mono audio (1 channel)
        "-c:a", "pcm_s16le",  # PCM 16-bit audio codec
        "-y",             # Overwrite output file if it exists
        audio_file
    ])

    print("📝 Распознавание речи...")
    model = whisper.load_model("base")
    result = model.transcribe(audio_file, fp16=False)

    with open(subtitles_file, "w", encoding="utf-8") as f:
        index = 1
        for segment in result["segments"]:
            words = segment["text"].split()
            start_time = segment["start"]
            end_time = segment["end"]
            duration = end_time - start_time
            
            chunk_size = 3
            for i in range(0, len(words), chunk_size):
                chunk = " ".join(words[i:i + chunk_size])
                
                chunk_start = start_time + (i / len(words)) * duration
                chunk_end = chunk_start + (duration / (len(words) / chunk_size))

                start_str = f"{int(chunk_start // 3600):02}:{int((chunk_start % 3600) // 60):02}:{int(chunk_start % 60):02},{int((chunk_start % 1) * 1000):03}"
                end_str = f"{int(chunk_end // 3600):02}:{int((chunk_end % 3600) // 60):02}:{int(chunk_end % 60):02},{int((chunk_end % 1) * 1000):03}"

                f.write(f"{index}\n")
                f.write(f"{start_str} --> {end_str}\n")
                f.write(f"{chunk}\n\n")
                index += 1
    
    # Удаляем временный аудио файл
    if os.path.exists(audio_file):
        os.remove(audio_file)
    
    return subtitles_file

def add_subtitles_to_video(video_file, subtitles_file, output_file):
    print("🎬 Накладываем субтитры...")
    subprocess.run([
        "ffmpeg", "-i", video_file, "-vf",
        f"subtitles={subtitles_file}:force_style='Fontsize=24,PrimaryColour=&HFFFFFF&,Alignment=2'",
        "-c:a", "copy", "-y", output_file
    ])
    return output_file

def combine_videos(main_video, background_video, output_file):
    print("🛠️ Объединяем видео в формате 9:16 для TikTok...")
    
    try:
        # Получаем длительность основного видео
        main_duration = get_video_duration(main_video)
        print(f"  📊 Длительность основного видео: {format_time(main_duration)}")
        
        # Получаем длительность фонового видео
        bg_duration = get_video_duration(background_video)
        print(f"  📊 Длительность фонового видео: {format_time(bg_duration)}")
        
        # Создаем временный файл для обработанного фонового видео
        temp_bg_file = "temp_background.mp4"
        
        # Подготовка фонового видео по длительности
        if abs(main_duration - bg_duration) < 1:
            # Если длительности примерно одинаковые (разница меньше 1 секунды),
            # используем фоновое видео как есть
            print("  ✓ Длительности видео примерно совпадают, дополнительная обработка не требуется")
            processed_bg = background_video
        elif bg_duration > main_duration:
            # Если фоновое видео длиннее основного, обрезаем его
            print(f"  ✂️ Обрезаем фоновое видео до {format_time(main_duration)}")
            subprocess.run([
                "ffmpeg", "-i", background_video, "-t", str(main_duration),
                "-c:v", "copy", "-c:a", "copy", "-y", temp_bg_file
            ])
            processed_bg = temp_bg_file
        else:
            # Если фоновое видео короче основного, зацикливаем его
            print(f"  🔄 Удлиняем фоновое видео до {format_time(main_duration)}")
            # Создаем список повторений для достижения необходимой длительности
            repetitions = int(main_duration / bg_duration) + 1
            print(f"  🔢 Требуется повторений: {repetitions}")
            
            # Создаем временный файл с инструкциями для concat демультиплексора
            concat_file = "concat_list.txt"
            with open(concat_file, "w") as f:
                for _ in range(repetitions):
                    f.write(f"file '{background_video}'\n")
            
            # Соединяем повторения
            subprocess.run([
                "ffmpeg", "-f", "concat", "-safe", "0", "-i", concat_file,
                "-t", str(main_duration), "-c", "copy", "-y", temp_bg_file
            ])
            
            # Удаляем временный файл со списком
            if os.path.exists(concat_file):
                os.remove(concat_file)
            
            processed_bg = temp_bg_file
        
        # Создаем более простой и надежный подход к объединению видео
        print("  🔄 Создаем композицию в формате 9:16...")
        
        # Определяем размеры итогового видео (9:16)
        output_width = 1080
        output_height = 1920
        
        # Создаем временные файлы для масштабированных видео
        temp_main_scaled = "temp_main_scaled.mp4"
        temp_bg_scaled = "temp_bg_scaled.mp4"
        
        # 1. Масштабируем основное видео до 1/3 высоты (с сохранением пропорций)
        main_target_height = int(output_height / 3)
        print(f"  📐 Масштабируем основное видео (высота: {main_target_height}px)")
        subprocess.run([
            "ffmpeg", "-i", main_video,
            "-vf", f"scale=-1:{main_target_height}",
            "-c:a", "copy", "-y", temp_main_scaled
        ], check=True)
        
        # Получаем информацию о размерах масштабированного основного видео
        main_scaled_info = get_video_info(temp_main_scaled)
        main_scaled_width = main_scaled_info['width']
        main_scaled_height = main_scaled_info['height']
        
        print(f"  📏 Размеры масштабированного основного видео: {main_scaled_width}x{main_scaled_height}")
        
        # 2. Масштабируем фоновое видео до оставшихся 2/3 высоты
        bg_target_height = output_height - main_scaled_height
        print(f"  📐 Масштабируем фоновое видео (высота: {bg_target_height}px)")
        
        # Масштабируем с заполнением и обрезкой (crop) для сохранения пропорций
        subprocess.run([
            "ffmpeg", "-i", processed_bg,
            "-vf", f"scale={output_width}:{bg_target_height}:force_original_aspect_ratio=increase,"
                   f"crop={output_width}:{bg_target_height}:(iw-ow)/2:(ih-oh)/2",
            "-c:a", "copy", "-y", temp_bg_scaled
        ], check=True)
        
        # 3. Соединяем масштабированные видео вертикально
        print("  🔄 Объединяем масштабированные видео вертикально")
        
        # Если основное видео меньше выходной ширины, центрируем его
        if main_scaled_width < output_width:
            x_offset = int((output_width - main_scaled_width) / 2)
            subprocess.run([
                "ffmpeg", "-i", temp_main_scaled, "-i", temp_bg_scaled,
                "-filter_complex",
                f"[0:v]pad={output_width}:{main_scaled_height}:{x_offset}:0[top];"
                "[top][1:v]vstack=inputs=2[v]",
                "-map", "[v]", "-map", "0:a",
                "-c:v", "libx264", "-crf", "28", "-preset", "fast",
                "-aspect", "9:16", "-y", output_file
            ], check=True)
        else:
            # Если основное видео шире выходной ширины, обрезаем его
            if main_scaled_width > output_width:
                print(f"  ✂️ Обрезаем основное видео по ширине (целевая ширина: {output_width}px)")
                # Создаем дополнительный временный файл для обрезанного основного видео
                temp_main_cropped = "temp_main_cropped.mp4"
                subprocess.run([
                    "ffmpeg", "-i", temp_main_scaled,
                    "-vf", f"crop={output_width}:{main_scaled_height}:(iw-{output_width})/2:0",
                    "-c:a", "copy", "-y", temp_main_cropped
                ], check=True)
                
                # Используем обрезанное видео
                temp_main_final = temp_main_cropped
            else:
                temp_main_final = temp_main_scaled
            
            # Объединяем видео
            subprocess.run([
                "ffmpeg", "-i", temp_main_final, "-i", temp_bg_scaled,
                "-filter_complex", "[0:v][1:v]vstack=inputs=2[v]",
                "-map", "[v]", "-map", "0:a",
                "-c:v", "libx264", "-crf", "28", "-preset", "fast",
                "-aspect", "9:16", "-y", output_file
            ], check=True)
            
            # Удаляем дополнительный временный файл, если он был создан
            if main_scaled_width > output_width and os.path.exists("temp_main_cropped.mp4"):
                os.remove("temp_main_cropped.mp4")
        
        # Удаляем временные файлы
        temp_files = [temp_bg_file, temp_main_scaled, temp_bg_scaled]
        for file in temp_files:
            if os.path.exists(file) and file not in [background_video, main_video]:
                os.remove(file)
                print(f"  🧹 Удален временный файл: {file}")
        
        print(f"  ✅ Создано видео в формате 9:16: {output_file}")
        return output_file
        
    except Exception as e:
        print(f"❌ Ошибка при объединении видео: {e}")
        import traceback
        traceback.print_exc()
        
        # Копируем основное видео как результат, если произошла ошибка
        import shutil
        try:
            shutil.copy(main_video, output_file)
            print(f"⚠️ Из-за ошибки объединения, копируем основное видео как результат: {output_file}")
            return output_file
        except Exception as copy_error:
            print(f"❌ Не удалось создать выходной файл: {copy_error}")
            return None

def split_video(video_file, output_folder, segment_time=120):
    os.makedirs(output_folder, exist_ok=True)
    print("✂️ Нарезка видео на части...")
    
    # Получаем информацию о видео
    video_info = get_video_info(video_file)
    
    # Сохраняем информацию о видео в файл
    info_file = os.path.join(output_folder, "video_info.txt")
    with open(info_file, 'w', encoding='utf-8') as f:
        f.write(f"Информация о видео:\n")
        f.write(f"Разрешение: {video_info['width']}x{video_info['height']}\n")
        f.write(f"Продолжительность: {video_info['duration_formatted']} ({video_info['duration']:.2f} сек)\n")
        f.write(f"Битрейт: {video_info['bitrate']} бит/с\n")
    
    # Нарезаем видео на части
    subprocess.run([
        "ffmpeg", "-i", video_file, "-c", "copy", "-map", "0",
        "-segment_time", str(segment_time), "-f", "segment", "-reset_timestamps", "1",
        os.path.join(output_folder, "part_%03d.mp4")
    ])
    
    # Получаем список созданных частей
    parts = [f for f in os.listdir(output_folder) if f.startswith("part_") and f.endswith(".mp4")]
    parts.sort()
    
    # Создаем файл с информацией о частях
    parts_info_file = os.path.join(output_folder, "parts_info.txt")
    with open(parts_info_file, 'w', encoding='utf-8') as f:
        f.write(f"Информация о частях видео:\n")
        f.write(f"{'='*50}\n")
        for i, part in enumerate(parts):
            part_path = os.path.join(output_folder, part)
            part_info = get_video_info(part_path)
            f.write(f"Часть {i+1}: {part}\n")
            f.write(f"Продолжительность: {part_info['duration_formatted']}\n")
            f.write(f"Размер файла: {os.path.getsize(part_path) / (1024*1024):.2f} МБ\n")
            f.write(f"{'='*50}\n")
    
    return output_folder