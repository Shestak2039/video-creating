const ytdl = require('youtube-dl-exec');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs-extra');

const video1Url = 'https://www.youtube.com/watch?v=9cCpZl8euLI'; // Основное видео
const video1RawPath = path.join(__dirname, 'video1_raw.mp4');     // Оригинал
const video1ConvertedPath = path.join(__dirname, 'video1_final.mp4'); // Финальный mp4 для iPhone

const downloadVideo = async (url, outputPath) => {
  console.log(`Downloading raw video from: ${url}`);
  await ytdl(url, {
    output: outputPath,
    format: 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]',
    mergeOutputFormat: 'mp4',
    noPlaylist: true
  });
  console.log(`Downloaded raw video to: ${outputPath}`);
};

const convertForiPhone = async (inputPath, outputPath) => {
  console.log(`Converting ${inputPath} to iPhone-friendly mp4...`);
  return new Promise((resolve, reject) => {
    const ffmpeg = spawn('ffmpeg', [
      '-i', inputPath,
      '-c:v', 'libx264',
      '-profile:v', 'baseline',     // ✅ для совместимости с iPhone
      '-level', '3.1',              // ✅ уровень для совместимости
      '-pix_fmt', 'yuv420p',        // ✅ обязательно для iOS
      '-c:a', 'aac',
      '-b:a', '128k',
      '-movflags', '+faststart',    // ✅ важно для Telegram и быстрой загрузки
      '-preset', 'fast',
      '-crf', '23',
      outputPath
    ]);

    ffmpeg.stderr.on('data', (data) => console.log(data.toString()));
    ffmpeg.on('close', (code) => {
      if (code === 0) {
        console.log(`Converted video ready: ${outputPath}`);
        resolve();
      } else {
        reject(new Error(`FFmpeg exited with code ${code}`));
      }
    });
  });
};

(async () => {
  try {
    await downloadVideo(video1Url, video1RawPath);
    await convertForiPhone(video1RawPath, video1ConvertedPath);

    // Опционально удаляем raw-версию
    await fs.remove(video1RawPath);

    console.log('✅ Done! Ready to upload to Telegram and watch on iPhone.');
  } catch (error) {
    console.error('Error:', error);
  }
})();
