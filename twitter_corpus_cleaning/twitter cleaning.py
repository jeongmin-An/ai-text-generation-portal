from pathlib import Path
import random
import re
import html
import shutil

# ---------------------------
# Settings
# ---------------------------
INPUT_FILE = Path("corrupt_twitter_corpus.txt")
OUTPUT_DIR = Path("twitter_cleaning_deliverable")
SAMPLE_SIZE = 10
RANDOM_SEED = 42

random.seed(RANDOM_SEED)

# ---------------------------
# Regex patterns
# ---------------------------
HTML_TAG_RE = re.compile(r"<[^>]+>")
URL_RE = re.compile(r"https?://\S+|www\.\S+")
NOISE_TOKEN_RE = re.compile(r"(?<!\S)(?:\^\^|\$|%|@)(?!\S)")  # remove standalone ^^, $, %, @
EXTRA_SPACE_RE = re.compile(r"\s+")
MULTI_PUNCT_RE = re.compile(r"([!?.,])\1{2,}")

# Emoji / symbol ranges
EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001F5FF"  
    "\U0001F600-\U0001F64F"  
    "\U0001F680-\U0001F6FF"  
    "\U0001F700-\U0001F77F"
    "\U0001F780-\U0001F7FF"
    "\U0001F800-\U0001F8FF"
    "\U0001F900-\U0001F9FF"  
    "\U0001FA00-\U0001FAFF"
    "\U00002700-\U000027BF"
    "\U00002600-\U000026FF"
    "]+",
    flags=re.UNICODE
)


REMOVE_EMOJIS = True


def load_lines(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        return [line.rstrip("\n") for line in f]


def write_lines(path: Path, lines: list[str]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for line in lines:
            f.write(line + "\n")


def analyze_lines(lines: list[str]) -> dict:
    total_lines = len(lines)
    nonempty_lines = sum(1 for line in lines if line.strip())

    html_tag_count = sum(len(HTML_TAG_RE.findall(line)) for line in lines)
    url_count = sum(len(URL_RE.findall(line)) for line in lines)
    noise_token_count = sum(len(NOISE_TOKEN_RE.findall(line)) for line in lines)
    emoji_count = sum(len(EMOJI_RE.findall(line)) for line in lines)

    return {
        "total_lines": total_lines,
        "nonempty_lines": nonempty_lines,
        "html_tag_count": html_tag_count,
        "url_count": url_count,
        "noise_token_count": noise_token_count,
        "emoji_count": emoji_count,
    }


def clean_text(text: str) -> str:
    text = html.unescape(text)

    # Convert to lowercase
    text = text.lower()
    # Remove URLs
    text = URL_RE.sub(" ", text)
    # Remove HTML tags
    text = HTML_TAG_RE.sub(" ", text)
    # Remove standalone noise tokens
    text = NOISE_TOKEN_RE.sub(" ", text)
    # Remove emojis
    if REMOVE_EMOJIS:
        text = EMOJI_RE.sub(" ", text)
    # Normalize repeated punctuation
    text = MULTI_PUNCT_RE.sub(r"\1\1", text)
    # Remove extra spaces
    text = EXTRA_SPACE_RE.sub(" ", text).strip()
    # Remove space before punctuation
    text = re.sub(r"\s+([?.!,;:])", r"\1", text)

    return text


def clean_lines(lines: list[str], remove_empty: bool = True) -> list[str]:
    cleaned = []
    for line in lines:
        cleaned_line = clean_text(line)
        if remove_empty:
            if cleaned_line:
                cleaned.append(cleaned_line)
        else:
            cleaned.append(cleaned_line)
    return cleaned


def make_random_sample(lines: list[str], n: int) -> list[str]:
    n = min(n, len(lines))
    return random.sample(lines, n)


def save_analysis_report(path: Path, stats: dict) -> None:
    report_lines = [
        "Dataset analysis summary",
        "------------------------",
        f"Total lines: {stats['total_lines']}",
        f"Non-empty lines: {stats['nonempty_lines']}",
        f"HTML tag occurrences: {stats['html_tag_count']}",
        f"URL occurrences: {stats['url_count']}",
        f"Noise token occurrences (^^, $, %, @): {stats['noise_token_count']}",
        f"Emoji occurrences: {stats['emoji_count']}",
        "",
        "Observed issues:",
        "- HTML tags mixed into the text",
        "- Random standalone symbols such as ^^, $, %, @",
        "- Emojis and special symbols",
        "- Extra whitespace / inconsistent spacing",
        "- Informal conversational language and slang",
    ]
    write_lines(path, report_lines)


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_FILE}")

    OUTPUT_DIR.mkdir(exist_ok=True)

    dirty_copy_path = OUTPUT_DIR / "dirty_input.txt"
    sample_dirty_path = OUTPUT_DIR / "sample_dirty.txt"
    sample_clean_path = OUTPUT_DIR / "sample_cleaned.txt"
    cleaned_output_path = OUTPUT_DIR / "cleaned_output.txt"
    analysis_report_path = OUTPUT_DIR / "analysis_report.txt"

    # Read original data
    lines = load_lines(INPUT_FILE)

    # Save a copy of dirty input into deliverable folder
    shutil.copy2(INPUT_FILE, dirty_copy_path)

    # Analyze dataset
    stats = analyze_lines(lines)
    save_analysis_report(analysis_report_path, stats)

    print("=== DATASET SUMMARY ===")
    print(f"Total lines: {stats['total_lines']}")
    print(f"Non-empty lines: {stats['nonempty_lines']}")
    print(f"HTML tag occurrences: {stats['html_tag_count']}")
    print(f"URL occurrences: {stats['url_count']}")
    print(f"Noise token occurrences: {stats['noise_token_count']}")
    print(f"Emoji occurrences: {stats['emoji_count']}")
    print()

    # Print first 10 lines 
    print("=== FIRST 10 ORIGINAL LINES ===")
    for i, line in enumerate(lines[:10], start=1):
        print(f"{i}. {line}")
    print()

    # Random 10-line sample
    sample_lines = make_random_sample(lines, SAMPLE_SIZE)
    write_lines(sample_dirty_path, sample_lines)

    cleaned_sample_lines = clean_lines(sample_lines)
    write_lines(sample_clean_path, cleaned_sample_lines)

    # Clean full dataset
    cleaned_lines = clean_lines(lines)
    write_lines(cleaned_output_path, cleaned_lines)

    print("=== FILES CREATED ===")
    print(f"Dirty input copy:   {dirty_copy_path}")
    print(f"Sample dirty file:  {sample_dirty_path}")
    print(f"Sample clean file:  {sample_clean_path}")
    print(f"Cleaned output:     {cleaned_output_path}")
    print(f"Analysis report:    {analysis_report_path}")
    print()
    print("Done.")


if __name__ == "__main__":
    main()