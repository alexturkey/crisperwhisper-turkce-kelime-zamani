"""transkript: verbatim speech-to-text with word timestamps.

CrisperWhisper 2.0 Turbo (CTranslate2, CUDA int8) for the text, wav2vec2 CTC forced alignment for the
word times. Two subprocesses (ASR, then alignment) so that a 4 GB GPU never holds both models at once.
"""

__version__ = "0.1.0"
