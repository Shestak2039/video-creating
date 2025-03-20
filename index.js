const { spawn } = require('child_process');
const ytdl = require('youtube-dl-exec');
const fs = require('fs-extra');
const path = require('path');

const video1Url = 'https://www.youtube.com/watch?v=LnSCCxGqBJw'; // Основное видео
const video2Url = 'https://www.youtube.com/watch?v=ZtLrNBdXT7M'; // Дополнительное видео
const numSegments = 13;

const video1Path = path.join(__dirname, 'video1.mp4');
const video2Path = path.join(__dirname, 'video2.mp4');
const outputDir = path.join(__dirname, 'output_parts');
const finalOutputDir = path.join(__dirname, 'final_output1');

const downloadVideo = async (url, outputPath) => {
    console.log(`Downloading in BEST quality: ${url}`);
    await ytdl(url, {
        output: outputPath,
        format: 'bestvideo[height<=720][fps<=30][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][fps<=30][ext=mp4]',
        mergeOutputFormat: 'mp4',
        noPlaylist: true
    });
    console.log(`Downloaded: ${outputPath}`);
};

const runFFmpeg = (args) => {
    return new Promise((resolve, reject) => {
        const ffmpeg = spawn('ffmpeg', args);
        ffmpeg.stdout.on('data', (data) => console.log(data.toString()));
        ffmpeg.stderr.on('data', (data) => console.error(data.toString()));

        ffmpeg.on('close', (code) => {
            if (code === 0) resolve();
            else reject(new Error(`FFmpeg process exited with code ${code}`));
        });
    });
};

const getVideoDuration = async (filePath) => {
    return new Promise((resolve, reject) => {
        const ffmpeg = spawn('ffmpeg', ['-i', filePath, '-hide_banner', '-f', 'null', '-']);
        let duration = 0;
        ffmpeg.stderr.on('data', (data) => {
            const output = data.toString();
            const match = output.match(/Duration: (\d+):(\d+):(\d+\.\d+)/);
            if (match) {
                const hours = parseInt(match[1], 10);
                const minutes = parseInt(match[2], 10);
                const seconds = parseFloat(match[3]);
                duration = hours * 3600 + minutes * 60 + seconds;
            }
        });

        ffmpeg.on('close', () => resolve(duration));
        ffmpeg.on('error', reject);
    });
};

const splitVideo = async (inputPath, outputPattern, segmentDuration) => {
    fs.ensureDirSync(outputDir);
    console.log(`Splitting ${inputPath} into ${numSegments} parts (~${segmentDuration.toFixed(2)} sec each)...`);

    await runFFmpeg([
        '-i', inputPath,
        '-c:v', 'libx264',
        '-crf', '23',
        '-preset', 'fast',
        '-g', '30',
        '-sc_threshold', '0',
        '-c:a', 'aac',
        '-b:a', '128k',
        '-force_key_frames', `expr:gte(t,n*${segmentDuration})`,
        '-segment_time', segmentDuration.toString(),
        '-f', 'segment',
        '-reset_timestamps', '1',
        path.join(outputDir, outputPattern)
    ]);
};

const getVideoParts = (prefix) => {
    return fs.readdirSync(outputDir)
        .filter(file => file.startsWith(prefix))
        .sort()
        .map(file => path.join(outputDir, file));
};

const mergeTwoVideos = async (video1, video2, outputPath) => {
    console.log(`Merging (9:16 format): ${video1} + ${video2}`);

    // Финальный размер вертикального видео: 1080x1920
    const width = 1080;
    const height = 1920;

    const topHeight = Math.floor(height * 0.4);   // 40% высоты
    const bottomHeight = height - topHeight;      // 60% высоты

    await runFFmpeg([
        '-i', video1,
        '-i', video2,
        '-filter_complex',
        `[0:v]scale=${width}:${topHeight}:force_original_aspect_ratio=increase,crop=${width}:${topHeight}[top];` +
        `[1:v]scale=${width}:${bottomHeight}:force_original_aspect_ratio=increase,crop=${width}:${bottomHeight}[bottom];` +
        `[top][bottom]vstack=inputs=2[stacked]`,
        '-map', '[stacked]',
        '-map', '0:a',
        '-c:v', 'libx264',
        '-profile:v', 'baseline',
        '-level', '3.1',
        '-pix_fmt', 'yuv420p',
        '-crf', '28',
        '-preset', 'fast',
        '-c:a', 'aac',
        '-b:a', '96k',
        '-movflags', '+faststart',
        '-y', // перезаписывать если файл уже есть
        outputPath
    ]);
};

const cleanUp = async () => {
    console.log('Cleaning up temporary files...');
    try {
        await fs.remove(outputDir);
        await fs.remove(video1Path);
        await fs.remove(video2Path);
        console.log('Cleanup completed.');
    } catch (error) {
        console.error('Error during cleanup:', error);
    }
};

const processVideos = async () => {
    try {
        console.log('Downloading videos...');
        await downloadVideo(video1Url, video1Path);
        await downloadVideo(video2Url, video2Path);

        console.log('Getting main video duration...');
        const mainDuration = await getVideoDuration(video1Path);
        const segmentDuration = mainDuration / numSegments;

        console.log(`Total main video duration: ${mainDuration.toFixed(2)} sec`);
        console.log(`Splitting videos into ${numSegments} parts, each ~${segmentDuration.toFixed(2)} sec`);

        await splitVideo(video1Path, 'video1_%02d.mp4', segmentDuration);
        await splitVideo(video2Path, 'video2_%02d.mp4', segmentDuration);

        console.log('Processing video parts...');
        fs.ensureDirSync(finalOutputDir);

        const video1Parts = getVideoParts('video1_');
        let video2Parts = getVideoParts('video2_');

        console.log(`Video1 has ${video1Parts.length} parts`);
        console.log(`Video2 has ${video2Parts.length} parts`);

        for (let i = 0; i < video1Parts.length; i++) {
            let video2Part = video2Parts[i] || video2Parts[Math.floor(Math.random() * video2Parts.length)];
            const outputPath = path.join(finalOutputDir, `final_part${i}.mp4`);
            console.log(`Merging part ${i + 1}/${video1Parts.length}`);
            await mergeTwoVideos(video1Parts[i], video2Part, outputPath);
        }

        console.log('Processing completed! All final parts are in:', finalOutputDir);

        await cleanUp();
    } catch (error) {
        console.error('Error during processing:', error);
    }
};

processVideos().catch(console.error);
