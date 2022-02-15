"""
References to spans of text, used by annotations.
"""


class Selector():
    """
    A `Selector` represent one of potentially multiple spans targeted by an `Annotation`.
    """

    def __init__(self, start: int, end: int, text: str):
        self.start = start
        self.end = end
        self.covered_text = text[start:end]

    def __repr__(self):
        return f"Selector(start={self.start}, end={self.end}, covered_text={self.covered_text})"
