def chunk_text(
    text: str,
    min_words: int = 300,
    max_words: int = 500,
) -> list[str]:
    words = text.split()

    if not words:
        return []

    chunks = []

    start = 0

    while start < len(words):
        end = min(
            start + max_words,
            len(words),
        )

        chunk = " ".join(words[start:end])

        chunks.append(chunk)

        start = end

    return chunks