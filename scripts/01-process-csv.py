import re
import subprocess
import os
import sys
import shutil
import time
import csv
import tempfile
from PIL import Image

USERNAME = "StarfishEnglish"
VOICES = [
    "Allison (Enhanced)",
    "Ava (Premium)",
    "Daniel (Enhanced)",
    "Joelle (Enhanced)",
    "Lee (Enhanced)",
    "Karen (Premium)",
    "Kate (Enhanced)",
    "Matilda (Premium)",
    "Nathan (Enhanced)",
    "Oliver (Enhanced)",
    "Samantha (Enhanced)",
    "Serena (Premium)",
    "Stephanie (Enhanced)",
    "Susan (Enhanced)",
    "Tessa (Enhanced)",
    "Zoe (Premium)",
    #    "Moira (Enhanced)",
    #    "Evan (Enhanced)",
    #    "Fiona (Enhanced)",
    #    "Jamie (Premium)",
    #    "Isha (Premium)",
    #    "Rishi (Enhanced)",
    #    "Veena (Enhanced)",
]

VERBOSE = True

# Helper functions
def sanitize_filename(filename):
    # Convert to lowercase
    filename = filename.lower()
    # Remove any character that isn't alphanumeric, underscore, or hyphen
    filename = re.sub(r'[^a-z0-9_-]', '', filename)
    return filename

def normalize_quotes(text):
    # Convert smart quotes and apostrophes to their "dumb" counterparts
    return text.replace('"', '"').replace('"', '"').replace("'", "'").replace("'", "'")

def timestamp():
    return time.strftime("%Y%m%d%H%M%S")

def backup_csv(csv_path):
    old_csv_path = f"{os.path.splitext(csv_path)[0]}-old-{timestamp()}.csv"
    shutil.copy2(csv_path, old_csv_path)
    if VERBOSE:
        print(f"Backed up CSV file to: {old_csv_path}")

def text_to_speech(text, aiff_filename, speed, voice):
    print(f"Converting '{text}' to AIFF with {voice}")
    subprocess.call(["say", "-v", voice, "-o", aiff_filename, "-r", str(speed), text])

def text_to_speech_blank(text, keyword, aiff_filename, voice):
    keyword = keyword.strip('"""\'')
    pattern = fr"(?:^|\b|[\"\"])({re.escape(keyword)})(?:\b|$|[\"\"])"
    blank_sentence = re.sub(pattern, ", blank, ", text, flags=re.IGNORECASE)
    subprocess.call(
        ["say", "-v", voice, "-o", aiff_filename, "-r", "150", blank_sentence]
    )

def check_ffmpeg():
    print("Checking if ffmpeg is installed...")
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False

def convert_to_mp3(aiff_filename, mp3_filename):
    print(f"Converting {aiff_filename} to MP3...")
    try:
        subprocess.check_call(
            [
                "ffmpeg",
                "-i",
                aiff_filename,
                "-b:a",
                "32k",
                "-ac",
                "1",
                "-c:a",
                "libmp3lame",
                mp3_filename,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError as e:
        print(f"Error during conversion: {str(e)}")
        return
    try:
        os.remove(aiff_filename)
    except OSError as e:
        print(f"Error while deleting file {aiff_filename}: {str(e)}")

def convert_to_webp(input_path, output_path):
    print(f"Converting {input_path} to WebP...")
    try:
        with Image.open(input_path) as img:
            img.save(output_path, 'WEBP')
    except Exception as e:
        print(f"Error during conversion: {str(e)}")

def process_csv(csv_file):
    print(f"Processing {csv_file}...")
    base_name = os.path.splitext(os.path.basename(csv_file))[0]
    media_dir = f"media-{base_name}"
    voice_index = 0
    current_timestamp = timestamp()

    for directory in [media_dir]:
        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
            except OSError as e:
                print(f"Error while creating directory {directory}: {str(e)}")
                return

    try:
        with open(csv_file, "r") as infile, open(
            f"{csv_file}.tmp", "w", newline=""
        ) as outfile, tempfile.TemporaryDirectory() as temp_dir:
            reader = csv.reader(infile, delimiter=",")
            writer = csv.writer(outfile, delimiter=",", quoting=csv.QUOTE_MINIMAL)

            header = next(reader)
            header.pop(5)
            header.pop(4)

            header = [
                "guid",
                "word en",
                "word ja",
                "sentence ja",
                "sentence en",
                "sentence en pronunciation",
                "example",
                "example cloze",
                "image",
                "image filename",
                "word audio",
                "word audio filename",
                "sentence en audio",
                "sentence en audio filename",
                "sentence en blank audio",
                "sentence en blank audio filename",
                "tags",
            ]

            writer.writerow(header)

            for row in reader:
                if len(row) < 6:
                    print(f"Error: line has fewer than 6 columns: {row}")
                    continue
                if "" in row:
                    print(f"Error: line has missing values: {row}")
                    continue

                try:
                    word = normalize_quotes(row[0])
                    sentence = normalize_quotes(row[3].strip())
                    image_file = row[5]

                    lower_sentence = sentence.lower()
                    lower_word = word.lower()

                    pattern = fr'(?:^|\b|["\'])({re.escape(lower_word)})(?:\b|$|["\'])'
                    matches = [(m.start(), m.end()) for m in re.finditer(pattern, lower_sentence)]

                    example = sentence[:]
                    example_cloze = sentence[:]

                    for start, end in reversed(matches):
                        actual_word = sentence[start:end]
                        stripped_word = actual_word.strip('"\'')

                        # Check if the word is surrounded by quotes
                        left_quote = sentence[max(0, start-1):start]
                        right_quote = sentence[end:end+1]

                        if left_quote in ['"', "'"] and right_quote in ['"', "'"]:
                            example = (
                                example[:start-1] +
                                left_quote +
                                f'<b>{stripped_word}</b>' +
                                right_quote +
                                example[end+1:]
                            )
                            example_cloze = (
                                example_cloze[:start-1] +
                                left_quote +
                                f'{{{{c1::{stripped_word}}}}}' +
                                right_quote +
                                example_cloze[end+1:]
                            )
                        else:
                            example = example[:start] + f'<b>{stripped_word}</b>' + example[end:]
                            example_cloze = example_cloze[:start] + f'{{{{c1::{stripped_word}}}}}' + example_cloze[end:]

                    # Image processing
                    image_filename, image_ext = os.path.splitext(image_file)
                    if image_ext.lower() in [".jpg", ".jpeg", ".webp"]:
                        old_image_path = os.path.join("images", image_file)

                        if image_ext.lower() == ".jpg" and not os.path.exists(old_image_path):
                            old_image_path = os.path.join("images", image_filename + ".jpeg")
                            if not os.path.exists(old_image_path):
                                raise FileNotFoundError(f"Neither {image_file} nor {image_filename}.jpeg found")
                            image_ext = ".jpeg"
                            image_file = image_filename + ".jpeg"

                        if image_ext.lower() == ".jpg":
                            new_jpg_path = os.path.join("images", image_filename + ".jpeg")
                            os.rename(old_image_path, new_jpg_path)
                            old_image_path = new_jpg_path
                            image_ext = ".jpeg"
                            image_file = image_filename + ".jpeg"

                        image_filename = sanitize_filename(image_filename)

                        new_image_filename = f"{sanitize_filename(USERNAME)}-{image_filename}-{current_timestamp}.webp"
                        new_image_path = os.path.join(media_dir, new_image_filename)

                        if image_ext.lower() in [".jpg", ".jpeg"]:
                            convert_to_webp(old_image_path, new_image_path)
                        else:
                            shutil.copy2(old_image_path, new_image_path)
                    else:
                        # Handle the case where the image doesn't exist or has an unsupported format
                        print(f"Warning: Image file {image_file} not found or unsupported format. Using a placeholder.")
                        new_image_filename = "placeholder.webp"  # You might want to create a actual placeholder image

                    # Audio processing
                    voice = VOICES[voice_index]
                    voice_index = (voice_index + 1) % len(VOICES)

                    sanitized_word = sanitize_filename(word)

                    word_mp3_filename = os.path.join(
                        media_dir,
                        f"{sanitize_filename(USERNAME)}-{sanitized_word}-{current_timestamp}.mp3",
                    )
                    sentence_mp3_filename = os.path.join(
                        media_dir,
                        f"{sanitize_filename(USERNAME)}-{sanitized_word}-{current_timestamp}-sentence.mp3",
                    )
                    sentence_blank_mp3_filename = os.path.join(
                        media_dir,
                        f"{sanitize_filename(USERNAME)}-{sanitized_word}-{current_timestamp}-sentence-blank.mp3",
                    )

                    word_aiff_filename = os.path.join(temp_dir, "word.aiff")
                    sentence_aiff_filename = os.path.join(temp_dir, "sentence.aiff")
                    sentence_blank_aiff_filename = os.path.join(
                        temp_dir, "sentence_blank.aiff"
                    )

                    text_to_speech(word, word_aiff_filename, 150, voice)
                    text_to_speech(sentence, sentence_aiff_filename, 150, voice)
                    text_to_speech_blank(
                        sentence, word, sentence_blank_aiff_filename, voice
                    )

                    convert_to_mp3(word_aiff_filename, word_mp3_filename)
                    convert_to_mp3(sentence_aiff_filename, sentence_mp3_filename)
                    convert_to_mp3(
                        sentence_blank_aiff_filename,
                        sentence_blank_mp3_filename,
                    )

                    new_row = [
                        "",  # guid (empty)
                        word,  # Word EN
                        row[1],  # Word JA
                        row[2],  # Sentence JA
                        sentence,  # Sentence EN
                        sentence,  # Sentence EN Pronunciation
                        example,  # Example
                        example_cloze,  # Example Cloze
                        f'<img src="{new_image_filename}">',  # Image (with <img> tag)
                        new_image_filename,  # Image Filename
                        f"[sound:{os.path.basename(word_mp3_filename)}]",  # Word Audio
                        os.path.basename(word_mp3_filename),  # Word Audio Filename
                        f"[sound:{os.path.basename(sentence_mp3_filename)}]",  # Sentence EN Audio
                        os.path.basename(sentence_mp3_filename),  # Sentence EN Audio Filename
                        f"[sound:{os.path.basename(sentence_blank_mp3_filename)}]",  # Sentence EN Blank Audio
                        os.path.basename(sentence_blank_mp3_filename),  # Sentence EN Blank Audio Filename
                        "",  # tags (empty)
                    ]
                    writer.writerow(new_row)

                except IndexError as e:
                    print(f"Error processing line: {row} - {str(e)}")
                    continue

        # Replace the original file with the temporary file
        os.replace(f"{csv_file}.tmp", csv_file)

    except IOError as e:
        print(f"Error opening file {csv_file}: {str(e)}")
        return

if __name__ == "__main__":
    print(f"Running {sys.argv[0]}...")
    if len(sys.argv) != 2:
        print("Usage: python combined_script.py <csv_file>")
    else:
        csv_file = sys.argv[1]
        backup_csv(csv_file)
        process_csv(csv_file)
