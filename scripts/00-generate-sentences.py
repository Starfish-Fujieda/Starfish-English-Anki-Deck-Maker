from openai import OpenAI
import csv
import os
import sys

# Set your OpenAI API key
openai.api_key = "sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# Function to generate sentences using the OpenAI API
def generate_sentences(word_en, word_ja):
    response = client.chat.completions.create(model="gpt-4o-mini",  # Or your preferred model
    messages=[
        {"role": "system", "content": f"""
            Assume the role of a comedian who is also an ESL teacher for young learners. Your task is to create 10 simple but grammatically correct sentences with subject-verb agreement that will make teenagers, who are learning English as a foreign language, laugh out loud if they were to see a picture depicting the scene described by each sentence. Use comedic techniques such as misdirection, paraprosdokians, non-sequiturs, wordplay, absurdity, and situational irony.

            Each sentence you create should:
            - Be in novice-level ESL English with correct subject-verb agreement.
            - Contain the exact given English word/phrase, which corresponds to the given Japanese word/phrase. This word/phrase should be part of a sentence describing a visually funny scene.
            - Use a variety of sentence structures to ensure diversity (vary subject, verb, object positions, and use different clause types).
            - Be grammatically correct and visually funny, describing a scene that would be amusing in a picture.

            **Output the sentences in a numbered list format**. Each number should be followed by the English sentence and the Japanese translation in the same line, like this:

            1. [English sentence] [Japanese translation]
            2. [English sentence] [Japanese translation]

            Your given English word/phrase is "{word_en}" and its Japanese equivalent is "{word_ja}". The sentences should be humorous but appropriate, and double-check for subject-verb agreement.
            **Also, please make sure to provide accurate Japanese translations for each sentence.**
            Just output the sentences in a numbered list, single-spaced, nothing else.
            """}
    ],
    max_tokens=900,
    n=1,
    stop=None,
    temperature=0.7)

    sentences = response.choices[0].message.content.strip() # Access .message.content
    tokens_used = response.usage.total_tokens
    return sentences, tokens_used

# Main script
if len(sys.argv) != 2:
    print("Usage: python 00-generate-sentences.py <csv_file>")
    sys.exit(1)

csv_file_path = sys.argv[1]

# Extract file name without extension
file_name = os.path.splitext(os.path.basename(csv_file_path))[0]
txt_file = file_name + "-sentences.txt"

with open(csv_file_path, 'r', encoding='utf-8') as csvfile, open(txt_file, 'w', encoding='utf-8') as txtfile:
    reader = csv.reader(csvfile)
    next(reader)  # Skip header row

    for row in reader:
        word_en, word_ja, *_ = row  # *_ will capture all remaining columns
        sentences, tokens_used = generate_sentences(word_en, word_ja)

        txtfile.write(f"{word_en}: {word_ja}\n")  # Print word pair
        txtfile.write(sentences + "\n")
        txtfile.write(f"Tokens used: {tokens_used}\n\n")  # Print token count

print(f"Sentences generated and saved to {txt_file}")

# After choosing which sentences to use, I have Claude.ai or Microsoft Copilot (formerly Bing) double check the Japanese translations. I keep forgetting the exact prompt I've used in the past, but this is what I used the most recent time.
#
# If a translation ends up being particulary shitty, a student will let me know, so in the end it's all good.
#
# I'm using these English-Japanese sentence pairs on Anki vocabulary flashcards for Japanese teens. Please review the Japanese translations. Do they sound natural? Are they humorous translations of the original English sentences? I don't want them to sound corny or condescending. It's OK for them to be dry humor, because example sentences in textbooks are always very dry and usually not funny or interesting at all. I'm trying to counteract that, and I think that sentences that sound matter-of-fact about absurd situations and are accompanied by funny AI art images depicting them, will be more memorable than typical boring sentences about boring situations.
