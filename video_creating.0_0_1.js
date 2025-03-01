const { spawn } = require('child_process');
const ytdl = require('youtube-dl-exec');
const fs = require('fs-extra');
const path = require('path');

const video1Url = 'https://www.youtube.com/watch?v=0AfdAFneMdM'; // Замени на реальный ID
const video2Url = 'https://www.youtube.com/watch?v=XBIaqOm0RKQ'; // Дополнительное видео

const video1Path = path.join(__dirname, 'video1.mp4');
const video2Path = path.join(__dirname, 'video2.mp4');
const outputDir = path.join(__dirname, 'output_parts');
const finalOutputDir = path.join(__dirname, 'final_output');

const downloadVideo = async (url, outputPath) => {
    console.log(`Downloading: ${url}`);
    await ytdl(url, {
        output: outputPath,
        format: 'mp4',
        mergeOutputFormat: 'mp4',
        noPlaylist: true
    });
    console.log(`Downloaded: ${outputPath}`);
};

const ffmpegPath = "C:\\ffmpeg\\bin\\ffmpeg.exe"; // Укажи реальный путь

const runFFmpeg = (args) => {
    return new Promise((resolve, reject) => {
        const ffmpeg = spawn(ffmpegPath, args);

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

const splitVideo = async (inputPath, outputPattern, duration = 60) => {
    fs.ensureDirSync(outputDir);

    const totalDuration = await getVideoDuration(inputPath);
    const lastSegmentDuration = totalDuration % duration || duration; // Длина последнего сегмента

    console.log(`Splitting ${inputPath} into 1-minute parts...`);
    await runFFmpeg([
        '-i', inputPath,
        '-c:v', 'libx264',
        '-crf', '23',
        '-preset', 'fast',
        '-g', '30',
        '-sc_threshold', '0',
        '-c:a', 'aac',
        '-b:a', '128k',
        '-force_key_frames', `expr:gte(t,n*${duration})`,
        '-f', 'segment',
        '-segment_times', Array.from({ length: Math.floor(totalDuration / duration) }, (_, i) => (i + 1) * duration).join(',') + `,${totalDuration}`,
        '-reset_timestamps', '1',
        path.join(outputDir, outputPattern)
    ]);

    console.log(`Splitting completed: last segment duration is ${lastSegmentDuration}s`);
};

const getVideoParts = (prefix) => {
    return fs.readdirSync(outputDir)
        .filter(file => file.startsWith(prefix))
        .sort()
        .map(file => path.join(outputDir, file));
};

const mergeTwoVideos = async (video1, video2, outputPath) => {
    console.log(`Merging: ${video1} + ${video2}`);
    await runFFmpeg([
        '-i', video1,
        '-i', video2,
        '-filter_complex', '[0:v]scale=1280:720[top]; [1:v]scale=1280:720[bottom]; [top][bottom]vstack=inputs=2[out]',
        '-map', '[out]',
        '-map', '0:a',
        '-c:v', 'libx264',
        '-crf', '23',
        '-preset', 'fast',
        '-c:a', 'aac',
        '-b:a', '128k',
        outputPath
    ]);
};

const processVideos = async () => {
    console.log('Downloading videos...');
    await downloadVideo(video1Url, video1Path);
    await downloadVideo(video2Url, video2Path);

    console.log('Splitting videos into 1-minute parts...');
    await splitVideo(video1Path, 'video1_%02d.mp4');
    await splitVideo(video2Path, 'video2_%02d.mp4');

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
};

processVideos().catch(console.error);
