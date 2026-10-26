import asyncio, os, shutil, subprocess, textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W, H = 720, 1280

def run(*args):
    subprocess.run(args, check=True)

def font(size):
    candidates = ['/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', '/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf']
    for path in candidates:
        if Path(path).exists(): return ImageFont.truetype(path, size)
    return ImageFont.load_default()

def wrap_text(draw, text, f, max_width):
    words, lines, current = text.split(), [], ''
    for word in words:
        test = f'{current} {word}'.strip()
        if draw.textbbox((0,0), test, font=f)[2] <= max_width:
            current = test
        else:
            if current: lines.append(current)
            current = word
    if current: lines.append(current)
    return lines

def card(text, label, destination):
    img = Image.new('RGB', (W,H), '#071529')
    d = ImageDraw.Draw(img)
    for y in range(H):
        v = int(18 + 25*y/H)
        d.line((0,y,W,y), fill=(5,v,50+int(30*y/H)))
    d.ellipse((420,100,900,580), outline='#25d5ff', width=8)
    d.ellipse((-210,800,320,1320), outline='#9a70ff', width=6)
    d.rounded_rectangle((50,70,670,158), radius=22, fill='#163957')
    d.text((75,91), label, font=font(34), fill='#80eaff')
    f = font(52)
    lines = wrap_text(d, text, f, 610)
    spacing = 72
    top = max(250, (H - len(lines)*spacing)//2)
    for i, line in enumerate(lines):
        bbox = d.textbbox((0,0), line, font=f)
        x = (W - (bbox[2]-bbox[0]))/2
        d.text((x,top+i*spacing), line, font=f, fill='white', stroke_width=1)
    d.text((68,1155), 'SCIENCE • AMAZING FACTS', font=font(26), fill='#b2d7ed')
    img.save(destination)

async def make_voice(narration, output):
    try:
        import edge_tts
        await edge_tts.Communicate(narration, 'en-US-AriaNeural').save(str(output))
        return
    except Exception as exc:
        print('edge-tts failed, falling back to local espeak:', str(exc)[:160])
    if not shutil.which('espeak-ng'):
        raise RuntimeError('Both edge-tts and espeak-ng unavailable')
    wav = output.with_suffix('.wav')
    run('espeak-ng', '-v', 'en-us', '-s', '145', '-w', str(wav), narration)
    run('ffmpeg','-y','-i',str(wav),'-codec:a','libmp3lame',str(output))

def duration(path):
    result = subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1',str(path)], text=True)
    return float(result.strip())

def make_video(fact, narration, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    voice = output_dir / 'voice.mp3'
    asyncio.run(make_voice(narration, voice))
    length = duration(voice) + 0.5
    if not 8 <= length <= 59:
        raise RuntimeError(f'Unexpected duration: {length:.1f}s')
    image = output_dir / 'card.png'
    card(fact['fact'], 'DID YOU KNOW?', image)
    video = output_dir / 'final.mp4'
    run('ffmpeg','-y','-loop','1','-framerate','30','-i',str(image),'-i',str(voice),
        '-t',f'{length:.3f}','-c:v','libx264','-preset','veryfast','-pix_fmt','yuv420p',
        '-vf','scale=720:1280,format=yuv420p','-c:a','aac','-b:a','128k','-movflags','+faststart',str(video))
    if not video.exists() or video.stat().st_size < 10000:
        raise RuntimeError('Video render failed')
    return video
