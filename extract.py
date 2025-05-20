#!/usr/bin/env python
# filepath: /home/ch4ser/Projects/Cthulhu/extract.py
# extract chapters from epub with given chapter title

import json
import os

import ebooklib
from bs4 import BeautifulSoup
from ebooklib import epub


def clean_html(html_content):
    """Remove HTML tags and extract text content"""
    soup = BeautifulSoup(html_content, "html.parser")
    text = soup.get_text("\n")
    return text


def sanitize_filename(name):
    """Replace spaces with underscores in the filename"""
    return name.replace(" ", "_")


def extract_chapters(epub_paths, titles, output_dir) -> tuple[list[str], list[str]]:
    """Extract chapters from epub file based on provided titles"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Dictionary to store chapter content by title
    chapters = {}

    for epub_path in epub_paths:
        # Open the epub file using ebooklib
        book = epub.read_epub(epub_path)

        # Process each document in the epub
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                try:
                    content = item.get_content().decode("utf-8")
                    soup = BeautifulSoup(content, "html.parser")

                    # Look for potential title elements
                    # This includes both traditional headings and p tags that might contain titles
                    # Also include p elements with class 'calibre8'
                    potential_headings = []

                    # First add all heading elements and regular p elements
                    potential_headings.extend(
                        soup.find_all(["h1", "h2", "h3", "h4", "h5"])
                    )

                    # Then add span element whose parent is p elements with class calibre7
                    calibre7_elements = soup.find_all("p", class_="calibre7")
                    for elem in calibre7_elements:
                        heading_elem = elem.find_next("span")
                        if heading_elem not in potential_headings:
                            potential_headings.append(heading_elem)

                    for heading in potential_headings:
                        heading_text = heading.get_text().strip()

                        # Check this heading against our titles
                        for title in titles:
                            if title in chapters:
                                continue
                            # Check if the heading contains or matches our title (case insensitive)
                            if title.lower() == heading_text.lower():

                                # For this title, get all content until the next potential heading
                                chapter_content = []
                                current = heading.find_next()
                                while current:
                                    current_content = current.get_text().strip()
                                    if current_content not in chapter_content:
                                        chapter_content.append(current_content)

                                    current = current.find_next()

                                # Store the chapter content
                                if title not in chapters:
                                    chapters[title] = "\n".join(chapter_content)

                except Exception as e:
                    print(f"Error processing document: {e}")

    find = []
    missed = []
    # Save extracted chapters as markdown files
    for index, title in enumerate(titles):
        if title in chapters:
            content = clean_html(chapters[title])
            filename = f"{index+1}-{sanitize_filename(title)}.md"
            output_path = os.path.join(output_dir, filename)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(f"# {title}\n\n")
                f.write(content)
            find.append(title)
        else:
            missed.append(title)

    return (find, missed)


def title_file_convert(json_file: str):
    """Load titles from a JSON file"""
    import json

    titles = []
    another_data = []
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        for k, v in data.items():
            temp_data = {}
            temp_data["chinese"] = k
            temp_data["english"] = v
            another_data.append(temp_data)
            print(another_data)
    json.dump(another_data, open("C.A.Smith_1.json", "w"), ensure_ascii=False, indent=4)
    return titles


def load_titles_from_json(json_file: str):
    """Load english titles from a JSON file"""
    titles = []
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        for item in data:
            titles.append(item["english"])
    return titles


def main():
    titles_file = "C.A.Smith.json"
    titles = load_titles_from_json(titles_file)

    refs = [
        "The Ultimate Weird Tales Collection - 133 stories (Clark Ashton Smith) (Z-Library).epub",
        "The Dark Eidolon and other fantasies (Clark Ashton Smith) (Z-Library).epub",
        "Complete Works of Clark Ashton Smith (Clark Ashton Smith) (Z-Library).epub",
    ]

    ref_paths = []
    ref_dir = "ref"
    for ref in refs:
        abs_path = os.path.join(ref_dir, ref)
        if os.path.exists(abs_path):
            ref_paths.append(abs_path)
        else:
            print(f"File {abs_path} does not exist.")

    output_dir = "C.A.Smith"

    matched_titles, missed_titles = extract_chapters(ref_paths, titles, output_dir)
    print(missed_titles)


if __name__ == "__main__":
    main()
