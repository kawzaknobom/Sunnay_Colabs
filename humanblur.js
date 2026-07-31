const { Human } = require('@vladmandic/human');
const fs = require('fs');
const ffmpeg = require('fluent-ffmpeg');

const human = new Human({
    backend: 'tensorflow',
    face: { enabled: true, gender: { enabled: true } },
    body: { enabled: true }
});

const inputPath = process.argv[2];
let detectedIntervals = [];

// Analyze at 2 FPS for better accuracy
ffmpeg(inputPath).outputOptions('-vf fps=2').format('image2pipe').on('data', async (frame) => {
    const result = await human.detect(frame);
    // Check if any person is classified as female
    const isFemale = result.persons.some(p => p.face?.gender === 'female');
    if (isFemale) {
        // Logic to track time segments
        detectedIntervals.push(human.now / 1000);
    }
}).on('end', () => {
    // Simplify intervals into 'between(t,start,end)' format for FFmpeg
    fs.writeFileSync('blur-log.json', JSON.stringify(detectedIntervals));
});