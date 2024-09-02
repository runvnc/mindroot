import yt_dlp
import ffmpeg
import argparse
import os
import re

def parse_time(time_str):
    # Check if the time is in MM:SS format
    if re.match(r'^\d{1,2}:\d{2}$', time_str):
        minutes, seconds = map(int, time_str.split(':'))
        return f'00:{time_str}'
    # If it's already in HH:MM:SS format, return as is
    elif re.match(r'^\d{1,2}:\d{2}:\d{2}$', time_str):
        return time_str
    else:
        raise ValueError("Invalid time format. Use either MM:SS or HH:MM:SS")

def download_and_extract_audio(url, start_time, end_time, output_file):
    # Download audio using yt-dlp
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
        }],
        'outtmpl': 'temp_audio.%(ext)s'
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    print(f"start: {start_time}, end: {end_time}")
    # Extract portion of audio using ffmpeg
    input_file = 'temp_audio.wav'
    stream = ffmpeg.input(input_file, ss=start_time, to=end_time)
    stream = ffmpeg.output(stream, output_file, acodec='pcm_s16le')
    ffmpeg.run(stream)

    # Clean up temporary file
    os.remove(input_file)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Download and extract audio from YouTube video')
    parser.add_argument('url', help='YouTube video URL')
    parser.add_argument('start_time', help='Start time in format MM:SS or HH:MM:SS')
    parser.add_argument('end_time', help='End time in format MM:SS or HH:MM:SS')
    parser.add_argument('output_file', help='Output audio file name (will be saved as .wav)')

    args = parser.parse_args()

    # Parse and validate time inputs
    start_time = parse_time(args.start_time)
    end_time = parse_time(args.end_time)

    # Ensure output file has .wav extension
    if not args.output_file.lower().endswith('.wav'):
        args.output_file += '.wav'

    download_and_extract_audio(args.url, start_time, end_time, args.output_file)
    print(f'Audio extracted and saved to {args.output_file}')
