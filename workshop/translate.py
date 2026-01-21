import xml.etree.ElementTree as ET
import argparse
import sys

def translate_to_english(text, client):
    result = client.translate(text, target_language='en', source_language='as')
    return result['translatedText']

def translate_to_assamese(text):
    from google.cloud import translate_v2 as translate

    client = translate.Client()
    result = client.translate(text, target_language='as')
    return result['translatedText']


def load_pages(xml_path: str):
    tree = ET.parse(xml_path)
    root = tree.getroot()  # <document>
    pages = []
    for page in root.findall(".//page"):
        page_no_text = page.findtext("page_no", default="").strip()
        content_text = page.findtext("content", default="").strip()
        pages.append((page_no_text, content_text))
    return pages


def update_xml_content_in_place(root):
    for page in root.findall(".//page"):
        content_el = page.find("content")
        if content_el is None:
            continue

        original_text = "".join(content_el.itertext()).strip()
        #translated_text = translate_to_assamese(original_text)

        #for child in list(content_el):
        #    content_el.remove(child)
        #content_el.text = translated_text


def write_xml(root, output_path: str):
    if output_path == "-":
        xml_text = ET.tostring(root, encoding="unicode")
        sys.stdout.write(xml_text)
        if not xml_text.endswith("\n"):
            sys.stdout.write("\n")
        return

    tree = ET.ElementTree(root)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="Path to the input XML file")
    parser.add_argument(
        "-o",
        "--output",
        default="-",
        help="Path to write translated text (default: stdout). Use '-' for stdout.",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Maximum number of <page> elements to translate (default: translate all).",
    )

    args = parser.parse_args(argv)

    tree = ET.parse(args.input)
    root = tree.getroot()

    pages = root.findall(".//page")
    if args.max_pages is not None:
        pages = pages[: args.max_pages]

    for idx, page in enumerate(pages):
        sys.stderr.write(f"page===== {idx}\n")
        
        content_el = page.find("content")
        if content_el is None:
            continue

        original_text = "".join(content_el.itertext()).strip()
        translated_text = translate_to_assamese(original_text)

        content_el.text = translated_text

    write_xml(root, args.output)


if __name__ == "__main__":
    main()
