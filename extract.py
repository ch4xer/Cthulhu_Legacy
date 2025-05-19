#!/usr/bin/env python
# filepath: /home/ch4ser/Projects/Cthulhu/extract.py
# extract chapters from epub with given chapter title

import os

import ebooklib
from bs4 import BeautifulSoup, Tag
from ebooklib import epub


def clean_html(html_content):
    """Remove HTML tags and extract text content"""
    soup = BeautifulSoup(html_content, "html.parser")
    text = soup.get_text("\n")
    return text


def sanitize_filename(name):
    """Replace spaces with underscores in the filename"""
    return name.replace(" ", "_")


def extract_chapters(epub_path, titles, output_dir):
    """Extract chapters from epub file based on provided titles"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Dictionary to store chapter content by title
    chapters = {}

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
                potential_headings.extend(soup.find_all(["h1", "h2", "h3", "h4", "h5"]))

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
                        # Check if the heading contains or matches our title (case insensitive)
                        if title.lower() == heading_text.lower():
                            print(f"Match found for title: {title}")

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
                                print(chapter_content)

            except Exception as e:
                print(f"Error processing document: {e}")

    # Save extracted chapters as markdown files
    for index, title in enumerate(titles):
        if title in chapters:
            content = clean_html(chapters[title])
            filename = f"{index+1}-{sanitize_filename(title)}.md"
            output_path = os.path.join(output_dir, filename)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(f"# {title}\n\n")
                f.write(content)

            print(f"Extracted '{title}' to {output_path}")
        else:
            print(f"Title '{title}' not found in the epub.")


def main():
    # Define the titles you want to extract - put your desired titles here
    # 定义一个数组，每一个元素都是一个标题名
    titles = [
        "The Muse of Hyperborea",
        "The Coming of the White Worm",
    ]

    # Specify the epub file and output directory
    epub_path0 = os.path.join(
        "ref",
        "The Ultimate Weird Tales Collection - 133 stories (Clark Ashton Smith) (Z-Library).epub",
        # "The Dark Eidolon and other fantasies (Clark Ashton Smith) (Z-Library).epub",
    )
    epub_path1 = os.path.join(
        "ref",
        # "The Ultimate Weird Tales Collection - 133 stories (Clark Ashton Smith) (Z-Library).epub",
        "The Dark Eidolon and other fantasies (Clark Ashton Smith) (Z-Library).epub",
    )
    output_dir = "C.A.Smith"

    # Extract the chapters based on titles
    print(f"Extracting chapters from {epub_path0}...")
    extract_chapters(epub_path0, titles, output_dir)
    extract_chapters(epub_path1, titles, output_dir)


if __name__ == "__main__":
    main()
