import pdfplumber
import csv
import random
from pypinyin import pinyin, Style
import json
import datetime
import opencc
import sys
import os
import contextlib
import logging

# Suppress the warnings
logging.getLogger('pdfplumber').setLevel(logging.ERROR)
logging.getLogger('pdfminer').setLevel(logging.ERROR)

# Print a loading message
print("Loading...")

# Define the function to get the tone number
def get_tone_number(pinyin_str):
    tone_mapping = {
        'ā': 1, 'á': 2, 'ǎ': 3, 'à': 4,
        'a': 0, 'ō': 1, 'ó': 2, 'ǒ': 3, 'ò': 4,
        'ē': 1, 'é': 2, 'ě': 3, 'è': 4,
        'ī': 1, 'í': 2, 'ǐ': 3, 'ì': 4,
        'ū': 1, 'ú': 2, 'ǔ': 3, 'ù': 4,
        'ǖ': 1, 'ǘ': 2, 'ǚ': 3, 'ǜ': 4,
    }
    
    for char in pinyin_str:
        if char in tone_mapping:
            return tone_mapping[char]
    return 0  # Return 0 if no tone is found

# Get the current working directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Define the path to the PDF file
pdf_file_path = os.path.join(current_dir, 'data', 'CME-1000-Chinese-Characters.pdf')

# Load the characters from the PDF file
with pdfplumber.open(pdf_file_path) as pdf:
    characters = []
    for page in pdf.pages:
        text = page.extract_text()
        lines = text.splitlines()
        for line in lines:
            if line.strip():
                parts = line.split()
                if len(parts) >= 4:
                    pinyin_str = parts[0]
                    character = parts[1]
                    # Check if the character is a Chinese character
                    if len(character) == 1 and ord(character) >= 0x4e00 and ord(character) <= 0x9fff:
                        definition = ' '.join(parts[2:-1])
                        # Decode the pinyin with tone markers
                        pinyin_decoded = pinyin(character, errors='ignore')[0]
                        characters.append({
                            "character": character,
                            "pinyin": pinyin_decoded,
                            "definition": definition
                        })
                else:
                    # Don't print anything for skipped lines
                    pass

# Initialize progress tracker
class ProgressTracker:
    def __init__(self, filename):
        self.filename = filename
        self.progress = self.load_progress()

    def load_progress(self):
        try:
            with open(self.filename, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def save_progress(self):
        with open(self.filename, 'w') as f:
            json.dump(self.progress, f)

    def update_progress(self, character, correct):
        if character not in self.progress:
            self.progress[character] = {'correct': 0, 'incorrect': 0, 'last_repeated': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        if correct:
            self.progress[character]['correct'] += 1
        else:
            self.progress[character]['incorrect'] += 1
        self.progress[character]['last_repeated'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.save_progress()

    def get_progress(self, character):
        if character in self.progress:
            return self.progress[character]
        else:
            return None

# Initialize repetition system
class SpacedRepetition:
    def __init__(self, filename):
        self.filename = filename
        self.performance_data = self.load_performance_data()

    def load_performance_data(self):
        try:
            with open(self.filename, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def save_performance_data(self):
        with open(self.filename, 'w') as f:
            json.dump(self.performance_data, f)

    def update_performance_data(self, character, correct):
        if character not in self.performance_data:
            self.performance_data[character] = {'correct': 0, 'incorrect': 0, 'last_repeated': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        if correct:
            self.performance_data[character]['correct'] += 1
        else:
            self.performance_data[character]['incorrect'] += 1
        self.performance_data[character]['last_repeated'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.save_performance_data()

    def get_repetition_interval(self, character):
        # Implement the formula to determine the repetition interval
        # For example:
        if self.performance_data[character]['correct'] > 3:
            return 7  # days
        elif self.performance_data[character]['incorrect'] > 2:
            return 1  # day
        else:
            return 1  # day

# Initialize progress tracker and spaced repetition system
progress_tracker = ProgressTracker('progress.json')
spaced_repetition = SpacedRepetition('performance_data.json')

# Convert characters to traditional Chinese
def convert_to_traditional_chinese(characters):
    converter = opencc.OpenCC('s2t')
    traditional_characters = []
    for character in characters:
        traditional_character = converter.convert(character['character'])
        traditional_characters.append({
            "character": traditional_character,
            "pinyin": character["pinyin"],
            "definition": character["definition"]
        })
    return traditional_characters

# Add an option to choose between simplified Chinese and traditional Chinese
while True:
    print("Choose a character set:")
    print("1. Simplified Chinese")
    print("2. Traditional Chinese")
    print("3. Exit program")
    choice = input("Enter your choice: ")
    
    if choice == "1":
        # Use the simplified Chinese characters
        char_list = characters
        break  # Exit the character set selection loop
    elif choice == "2":
        # Convert the characters to traditional Chinese
        char_list = convert_to_traditional_chinese(characters)
        break  # Exit the character set selection loop
    elif choice == "3":
        print("Exiting program. Goodbye!")
        sys.exit()  # Exit the program
    else:
        print("Invalid choice. Please try again.")
        continue  # Continue to prompt for a valid choice

# Inside the while loop where you check user input
if char_list:
    while True:
        character = random.choice(char_list)
        print(f"Character: {character['character']}")
        pinyin_input = input("Enter the pinyin (without tone), or type 'exit' to stop: ")
        if pinyin_input.lower() == 'exit':
            break
        tone_input = input("Enter the tone number (1-4): ")
        if tone_input.isdigit() and 1 <= int(tone_input) <= 4:
            tone_number = int(tone_input)
            correct_pinyin_list = pinyin(character["character"], style=Style.TONE, errors='ignore')  # Get pinyin with tone marks
            correct_pinyin = correct_pinyin_list[0][0]  # Get the first pinyin with tone marks

            # Get the tone number from the correct pinyin
            actual_tone_number = get_tone_number(correct_pinyin)

            # Define user_pinyin here
            user_pinyin = pinyin_input  # Use the input directly
            correct_pinyin_without_tone = correct_pinyin[:-1]  # Remove the tone number for comparison

            # Check if the user input matches the correct pinyin without tone
            if user_pinyin == correct_pinyin_without_tone:
                # Check if the tone matches
                if tone_number == actual_tone_number:
                    print("Correct!")
                    progress_tracker.update_progress(character['character'], True)
                    spaced_repetition.update_performance_data(character['character'], True)
                else:
                    print(f"Incorrect tone. The correct tone is {actual_tone_number}. The correct pinyin is {correct_pinyin}.")
                    progress_tracker.update_progress(character['character'], False)
                    spaced_repetition.update_performance_data(character['character'], False)
            else:
                print("Incorrect. The correct pinyin is:", correct_pinyin)
                progress_tracker.update_progress(character['character'], False)
                spaced_repetition.update_performance_data(character['character'], False)

            print(f"Definition: {character['definition']}")
        else:
            print("Invalid tone number. Please enter a number between 1 and 4.")
        print("\n")
