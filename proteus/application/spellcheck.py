# ==========================================================================
# File: spellcheck.py
# Description: Spellchecker utilities for the PROTEUS application.
# Date: 08/05/2024
# Version: 0.1
# Author: José María Delgado Sánchez
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

import re
from typing import List, Tuple

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------

from spellchecker import SpellChecker
from PyQt6.QtGui import (
    QSyntaxHighlighter,
    QTextCharFormat,
)

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.application.utils.abstract_meta import SingletonMeta
from proteus.application.utils.decorators import proteus_action
from proteus.application.resources.themes import Themes


# --------------------------------------------------------------------------
# Class: SpellCheckerWrapper
# Description: Spellchecker wrapper class.
# Date: 08/05/2024
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
class SpellCheckerWrapper(metaclass=SingletonMeta):
    """
    Spellchecker wrapper class. It is used to check the spelling of a text.

    Current implementation uses pyspellchecker library.
    """

    # --------------------------------------------------------------------------
    # Method: __init__
    # Description: Constructor method.
    # Date: 08/05/2024
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    def __init__(self):
        """
        Constructor method.
        """

        self._spellchecker: SpellChecker = None

    
    # --------------------------------------------------------------------------
    # Method: set_language
    # Description: Set the language for spellchecking.
    # Date: 08/05/2024
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    def set_language(self, language: str) -> None:
        """
        Set the language for spellchecking.

        param language: Language to set.
        """
        assert language in SpellChecker.languages(), (
            f"Language '{language}' is not available for spellchecking. "
            f"Available languages are: {', '.join(SpellChecker.languages())}"
        )

        self._spellchecker = SpellChecker(language=language)


    # --------------------------------------------------------------------------
    # Method: check
    # Description: Check the spelling of a word.
    # Date: 08/05/2024
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    def check(self, word: str) -> bool:
        """
        Check the spelling of a word. Returns True if the word is spelled correctly.

        param word: word to check.
        return: True if the word is spelled correctly, False otherwise.
        """
        if self._spellchecker is None:
            return True

        return word in self._spellchecker

    # --------------------------------------------------------------------------
    # Method: suggest
    # Description: Get a list of suggested words for a misspelled word.
    # Date: 08/05/2024
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    # NOTE: Using proteus_action to handle cursor shape in case of long spellcheck
    # some words might not have suggestions and take a while to process
    @proteus_action
    def suggest(self, word: str) -> list[str]:
        """
        Get a list of suggested words for a misspelled word.

        param text: Text to get suggestions.
        return: List of suggested words.
        """
        if self._spellchecker is None:
            return list()

        candidates = self._spellchecker.candidates(word)
        if candidates:
            return list(candidates)
        else:
            return list()
        
    # --------------------------------------------------------------------------
    # Method: list_available_languages (static)
    # Description: List available languages for spellchecking.
    # Date: 08/05/2024
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    @staticmethod
    def list_available_languages() -> list[str]:
        """
        List available languages for spellchecking.

        return: List of available languages dictionaries.
        """
        return list(SpellChecker.languages())

    # --------------------------------------------------------------------------
    # Method: tokenize
    # Description: Tokenize a text into words.
    # Date: 08/05/2024
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    # TODO: Improve code block handling
    def tokenize(self, text: str) -> List[re.Match]:
        """
        Tokenize a text into words.

        NOTE: this method is not static so tokenization can be omitted if
        spellchecking is disabled.

        param text: Text to tokenize.
        return: List of matches.
        """
        if self._spellchecker is None:
            return list()

        tokens: List[re.Match] = list()

        # Look for words with at least 2 characters omitting HTML tags
        tokenize_pattern = re.compile(r"\b(?<!<)(?<!</)[A-Za-z]{2,}(?!>)\b")

        # Store ranges to avoid tokenizing them
        invalid_ranges: List[Tuple[int, int]] = list()

        # Look for URLs
        url_pattern = re.compile(r"https?://[^\s]+")
        for m in url_pattern.finditer(text):
            invalid_ranges.append((m.start(), m.end()))

        # Look for email addresses
        email_pattern = re.compile(r"\b\w{1,}@\w{1,}\.\w{1,}\b")
        for m in email_pattern.finditer(text):
            invalid_ranges.append((m.start(), m.end()))

        # TODO: Handle code markdown code blocks (```... ``` or ` ... `). Pattern "(?s)```(?!```).*```"
        # works when there is only one code block in the text.

        # Exclude invalid matches
        for m in tokenize_pattern.finditer(text):
            if not any(start <= m.start() <= end for start, end in invalid_ranges):
                tokens.append(m)

        return tokens


# --------------------------------------------------------------------------
# Class: SpellCheckHighlighter
# Description: Syntax highlighter for spellchecking.
# Date: 08/05/2024
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
class SpellCheckHighlighter(QSyntaxHighlighter):
    """
    Syntax highlighter for spellchecking. It is used to highlight
    misspelled words in the text.
    """

    # --------------------------------------------------------------------------
    # Method: highlightBlock
    # Description: Highlight misspelled words in the text.
    # Date: 08/05/2024
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    def highlightBlock(self, text: str) -> None:

        if not hasattr(self, "_spellchecker"):
            # SpellCheckerWrapper is a Singleton initialized at startup
            # using user configuration settings.
            self._spellchecker = SpellCheckerWrapper()

        highlight_format = QTextCharFormat()
        highlight_format.setUnderlineStyle(
            QTextCharFormat.UnderlineStyle.SpellCheckUnderline
        )
        # Read the theme token on every highlight pass so the color follows
        # live theme switches without any refresh wiring.
        highlight_format.setUnderlineColor(Themes().color("spellcheck_error"))

        for match in self._spellchecker.tokenize(text):
            word = match.group()
            if not self._spellchecker.check(word):
                self.setFormat(
                    match.start(), match.end() - match.start(), highlight_format
                )
