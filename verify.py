"""Check the source references in a synthetic procurement extraction."""

import argparse
import json
from pathlib import Path
import unicodedata


def normalize(text):
    return " ".join(unicodedata.normalize("NFC", text).casefold().split())


def build_index(pages):
    index = {}
    for page in pages:
        key = (page["document"], page["page"])
        if key in index:
            raise ValueError(f"Повтор страницы: {key}")
        index[key] = normalize(page["text"])
    return index


def check_reference(claim, pages):
    """Return a verdict and matching pages in the cited document."""
    document = claim["document"]
    reference = (document, claim["page"])
    quote = normalize(claim["quote"])
    if not quote:
        return "empty_quote", []
    if quote in pages.get(reference, ""):
        return "verified", [claim["page"]]
    matches = sorted(page for (name, page), text in pages.items()
                     if name == document and quote in text)
    if matches:
        return "wrong_page", matches
    return "unverified", []


def audit(case):
    pages = build_index(case["pages"])
    findings = []
    for claim in case["claims"]:
        status, matches = check_reference(claim, pages)
        findings.append({**claim, "status": status, "matched_pages": matches})
    return findings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", nargs="?", type=Path,
                        default=Path(__file__).with_name("example.json"))
    parser.add_argument("--json", action="store_true", help="Print a JSON report")
    parser.add_argument("--strict", action="store_true",
                        help="Exit with code 1 if a reference is unverified")
    args = parser.parse_args()
    with args.case.open(encoding="utf-8") as source:
        findings = audit(json.load(source))
    if args.json:
        print(json.dumps(findings, ensure_ascii=False, indent=2))
    else:
        labels = {"verified": "подтверждено", "wrong_page": "неверная страница",
                  "empty_quote": "цитата пуста", "unverified": "цитата не найдена"}
        for item in findings:
            location = f"{item['document']}, стр. {item['page']}"
            print(f"{item['field']} | {location} | {labels[item['status']]}")
            if item["status"] == "wrong_page":
                print("  Цитата найдена на стр.", ", ".join(map(str, item["matched_pages"])))
    return int(args.strict and any(item["status"] != "verified" for item in findings))


if __name__ == "__main__":
    raise SystemExit(main())
