import subprocess
import os
import sys
import shutil
import time
import csv
import tempfile
from PIL import Image

# Constants
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
    "Moira (Enhanced)",
    "Nathan (Enhanced)",
    "Oliver (Enhanced)",
    "Samantha (Enhanced)",
    "Serena (Premium)",
    "Stephanie (Enhanced)",
    "Susan (Enhanced)",
    "Tessa (Enhanced)",
    "Zoe (Premium)",
    #    "Evan (Enhanced)",
    #    "Fiona (Enhanced)",
    #    "Jamie (Premium)",
    #    "Isha (Premium)",
    #    "Rishi (Enhanced)",
    #    "Veena (Enhanced)",
]

VERBOSE = True  # Set to True to enable verbose output


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
    blank_sentence = text.replace(keyword, ", blank, ")
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


def convert_to_webp(jpeg_filename, webp_filename):
    print(f"Converting {jpeg_filename} to WebP...")
    try:
        image = Image.open(jpeg_filename)
        image = image.convert("RGB")
        image.save(webp_filename, "webp")
    except Exception as e:
        print(f"Error during conversion: {str(e)}")


def process_csv(csv_file):
    print(f"Processing {csv_file}...")
    base_name = os.path.splitext(os.path.basename(csv_file))[0]
    media_dir = f"media-{base_name}"
    voice_index = 0
    current_timestamp = timestamp()  # Get the timestamp ONCE outside the loop

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
        ) as outfile, tempfile.TemporaryDirectory() as temp_dir:  # Create temp dir here
            reader = csv.reader(infile, delimiter=",")
            writer = csv.writer(outfile, delimiter=",")

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
                    word = row[0]
                    sentence = row[3]  # Assign sentence from row[3] (Sentence EN)
                    image_file = row[5]  # Assuming image filename is in the 6th column

                    # Create Example and Example Cloze
                    lower_sentence = sentence.lower()
                    lower_word = word.lower()

                    index = lower_sentence.find(lower_word)
                    example = sentence[:index] + f"<b>{sentence[index:index+len(word)]}</b>" + sentence[index+len(word):]
                    example_cloze = sentence[:index] + f"{{{{c1::{sentence[index:index+len(word)]}}}" + sentence[index+len(word):]

                    # Process Image
                    image_filename, image_ext = os.path.splitext(image_file)
                    if image_ext.lower() in [".jpg", ".jpeg", ".webp"]:
                        old_image_path = os.path.join("images", image_file)

                        # Check for .jpeg if .jpg is not found
                        if image_ext.lower() == ".jpg" and not os.path.exists(
                            old_image_path
                        ):
                            old_image_path = os.path.join(
                                "images", image_filename + ".jpeg"
                            )
                            if not os.path.exists(old_image_path):
                                raise FileNotFoundError(
                                    f"Neither {image_file} nor {image_filename}.jpeg found"
                                )
                            image_ext = ".jpeg"
                            image_file = image_filename + ".jpeg"

                        # Always rename .jpg to .jpeg (if .jpg is found)
                        if image_ext.lower() == ".jpg":
                            new_jpg_path = os.path.join(
                                "images", image_filename + ".jpeg"
                            )
                            os.rename(old_image_path, new_jpg_path)
                            old_image_path = new_jpg_path
                            image_ext = ".jpeg"
                            image_file = image_filename + ".jpeg"

                        new_image_filename = f"{USERNAME}-{image_filename.replace(' ', '-')}-{current_timestamp}.webp"
                        new_image_path = os.path.join(media_dir, new_image_filename)

                        if image_ext.lower() in [".jpg", ".jpeg"]:
                            convert_to_webp(old_image_path, new_image_path)
                        else:
                            shutil.copy2(old_image_path, new_image_path)

                        row[5] = new_image_filename

                    # Process Audio
                    voice = VOICES[voice_index]
                    voice_index = (voice_index + 1) % len(VOICES)

                    word_mp3_filename = os.path.join(
                        media_dir,
                        f"{USERNAME}-{word.replace(' ', '-')}-{current_timestamp}.mp3",
                    )
                    sentence_mp3_filename = os.path.join(
                        media_dir,
                        f"{USERNAME}-{word.replace(' ', '-')}-{current_timestamp}-sentence.mp3",
                    )
                    sentence_blank_mp3_filename = os.path.join(
                        media_dir,
                        f"{USERNAME}-{word.replace(' ', '-')}-{current_timestamp}-sentence-blank.mp3",
                    )

                    # Create temporary .aiff filenames using temp_dir
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

                    row[5] = f'<img src="{new_image_filename}">'  # Add <img> tag
                    new_row = [
                        "",  # guid (empty)
                        row[0],  # Word EN (0)
                        row[1],  # Word JA (1)
                        row[2],  # Sentence JA (2)
                        row[3],  # Sentence EN (3)
                        row[4],  # Sentence EN Pronunciation (4)
                        example,  # Example (5)
                        example_cloze,  # Example Cloze (6)
                        row[5],  # Image (with <img> tag) (7)
                        new_image_filename,  # Image Filename (8)
                        f"[sound:{os.path.basename(word_mp3_filename)}]",  # Word Audio (9)
                        os.path.basename(word_mp3_filename),  # Word Audio Filename (10)
                        f"[sound:{os.path.basename(sentence_mp3_filename)}]",  # Sentence EN Audio (11)
                        os.path.basename(
                            sentence_mp3_filename
                        ),  # Sentence EN Audio Filename (12)
                        f"[sound:{os.path.basename(sentence_blank_mp3_filename)}]",  # Sentence EN Blank Audio (13)
                        os.path.basename(
                            sentence_blank_mp3_filename
                        ),  # Sentence EN Blank Audio Filename(14)
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
