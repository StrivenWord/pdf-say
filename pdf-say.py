#!/usr/bin/env python3

import pdfplumber
import sys
import argparse
from collections import Counter
import subprocess
import tempfile
import os

def extract_main_text(pdf_file):
    main_text = []
    with pdfplumber.open(pdf_file) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            # Extract all words with their font sizes
            words = page.extract_words(use_text_flow=True, keep_blank_chars=False, extra_attrs=["size"])

            if not words:
                continue  # Skip pages with no words

            # Get the most common font size on this page (assumed to be the main text font size)
            font_sizes = [float(w['size']) for w in words if 'size' in w]
            if not font_sizes:
                continue  # Skip pages where 'size' is not available

            most_common_size = Counter(font_sizes).most_common(1)[0][0]

            # Filter words with font size equal to the most common size
            main_words = [w for w in words if float(w.get('size', 0)) == most_common_size]

            # Sort words by their position on the page
            main_words.sort(key=lambda w: (w['top'], w['x0']))

            # Join the words into lines
            lines = []
            current_line = []
            last_top = None
            for word in main_words:
                if last_top is None or abs(word['top'] - last_top) <= 2:
                    current_line.append(word['text'])
                else:
                    lines.append(' '.join(current_line))
                    current_line = [word['text']]
                last_top = word['top']
            if current_line:
                lines.append(' '.join(current_line))

            page_text = '\n'.join(lines)
            main_text.append(page_text)

    # Join all page texts
    full_text = '\n\n'.join(main_text)

    # Remove references section by looking for keywords
    ref_keywords = ['References', 'Bibliography', 'REFERENCES', 'BIBLIOGRAPHY']
    for keyword in ref_keywords:
        index = full_text.find(keyword)
        if index != -1:
            full_text = full_text[:index]
            break

    return full_text

def narrate_text(text, voice=None):
    say_command = ['say']

    if voice:
        say_command.extend(['-v', voice])

    # Create a temporary file to store the text
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_file:
        temp_file.write(text)
        temp_file_path = temp_file.name

    say_command.extend(['-f', temp_file_path])

    try:
        subprocess.run(say_command)
    except Exception as e:
        print(f"Error running 'say' command: {e}")
    finally:
        # Remove the temporary file
        os.remove(temp_file_path)

def main():
    parser = argparse.ArgumentParser(description='Extract main body text from a PDF and narrate it using macOS text-to-speech.')
    parser.add_argument('pdf_file', help='Path to the PDF file')
    parser.add_argument('-v', '--voice', help='Voice to use from installed voices')
    args = parser.parse_args()

    pdf_file = args.pdf_file
    voice = args.voice

    if not os.path.isfile(pdf_file):
        print(f"Error: File '{pdf_file}' not found.")
        sys.exit(1)

    try:
        text = extract_main_text(pdf_file)
        if not text.strip():
            print("No main text found in the PDF.")
            sys.exit(1)
        narrate_text(text, voice)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()

