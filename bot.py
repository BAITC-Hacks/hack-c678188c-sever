#!/usr/bin/env python3
"""Терминальный FAQ-бот: ближайший вопрос по ключевым словам, иначе «не знаю»."""

from pathlib import Path
import re
import sys

FAQ_PATH = Path(__file__).resolve().parent / "faq.txt"
UNKNOWN = "не знаю"
THRESHOLD = 0.5
SUFFIXES = (
    "ами",
    "ями",
    "ого",
    "ему",
    "ыми",
    "ими",
    "ах",
    "ях",
    "ов",
    "ев",
    "ей",
    "ой",
    "ий",
    "ый",
    "ая",
    "яя",
    "ое",
    "ее",
    "ые",
    "ие",
    "ам",
    "ям",
    "ом",
    "ем",
    "ую",
    "ть",
    "ся",
    "ии",
    "ия",
    "ию",
)
STOPWORDS = {
    "и",
    "в",
    "на",
    "не",
    "что",
    "как",
    "это",
    "для",
    "про",
    "или",
    "а",
    "но",
    "по",
    "с",
    "к",
    "о",
    "от",
    "из",
    "за",
    "до",
    "же",
    "ли",
    "бы",
    "то",
    "ты",
    "мы",
    "вы",
    "он",
    "она",
    "они",
    "есть",
    "быть",
    "этот",
    "эта",
    "эти",
    "какой",
    "какая",
    "какие",
    "the",
    "a",
    "an",
    "is",
    "of",
}


def stem(word: str) -> str:
    for suffix in SUFFIXES:
        if len(word) > len(suffix) + 3 and word.endswith(suffix):
            return word[: -len(suffix)]
    if len(word) > 4 and word.endswith(("а", "я", "у", "ю", "е", "ы", "и", "о")):
        return word[:-1]
    return word


def tokenize(text: str) -> set[str]:
    text = text.lower().replace("ё", "е")
    words = re.findall(r"[a-zа-я0-9]+", text, flags=re.IGNORECASE)
    return {stem(w) for w in words if len(w) >= 2 and w not in STOPWORDS}


def load_faq(path: Path) -> list[dict]:
    entries = []
    question = answer = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith("Q:"):
            if question and answer:
                entries.append(_entry(question, answer))
            question = line[2:].strip()
            answer = None
        elif line.startswith("A:"):
            answer = line[2:].strip()
    if question and answer:
        entries.append(_entry(question, answer))
    if not entries:
        raise SystemExit(f"В {path} нет пар вопрос-ответ.")
    return entries


def _entry(question: str, answer: str) -> dict:
    q_tokens = tokenize(question)
    return {
        "question": question,
        "answer": answer,
        "q_tokens": q_tokens,
        "tokens": q_tokens | tokenize(answer),
    }


def coverage(query_tokens: set[str], faq_tokens: set[str]) -> float:
    if not query_tokens:
        return 0.0
    return len(query_tokens & faq_tokens) / len(query_tokens)


def score(query_tokens: set[str], item: dict) -> float:
    # Ближе к формулировке вопроса важнее, чем совпадение с текстом ответа.
    return 0.7 * coverage(query_tokens, item["q_tokens"]) + 0.3 * coverage(
        query_tokens, item["tokens"]
    )


def find_answer(query: str, faq: list[dict]) -> str:
    query_tokens = tokenize(query)
    if not query_tokens:
        return UNKNOWN
    best = max(faq, key=lambda item: score(query_tokens, item))
    if score(query_tokens, best) < THRESHOLD:
        return UNKNOWN
    return best["answer"]


def main() -> None:
    faq = load_faq(FAQ_PATH)
    print("FAQ-бот репетиции HackAlem. Пишите вопрос. Выход: выход / quit / exit.")
    while True:
        try:
            query = input("\nВы: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not query:
            continue
        if query.lower() in {"выход", "quit", "exit", "q"}:
            break
        print(f"Бот: {find_answer(query, faq)}")


if __name__ == "__main__":
    sys.exit(main())
