import sys

from fetch import fetch_last_night, fetch_for_date
from storylines import find_storylines
from summarize import summarize
from render import save


def main():
    if len(sys.argv) > 1:
        data = fetch_for_date(sys.argv[1])
    else:
        data = fetch_last_night()
    storylines = find_storylines(data)
    summary = summarize(data, storylines)
    output_path = save(data, summary)
    print(f"Saved to: {output_path}")
    print(f"Open: {output_path.as_uri()}")


if __name__ == "__main__":
    main()