from faster_whisper import WhisperModel


_model: WhisperModel | None = None


def get_model() -> WhisperModel:
    global _model

    if _model is None:
        _model = WhisperModel(
            "small",
            device="cpu",
            compute_type="int8",
        )

    return _model


def transcribe_audio(path: str) -> str:
    model = get_model()

    segments, _ = model.transcribe(
        path,
        vad_filter=True,
    )

    texts = []

    for segment in segments:
        text = segment.text.strip()

        if text:
            texts.append(text)

    return " ".join(texts)