import os

from app.parsers.base_parser import BaseParser
from app.parsers.px4_parser import PX4Parser
from app.parsers.ardupilot_parser import ArduPilotParser
from app.parsers.betaflight_parser import BetaflightParser


class LogParserFactory:
    """Factory class to select parser based on file extension or structure."""

    @staticmethod
    def get_parser(file_path: str) -> BaseParser:

        ext = os.path.splitext(file_path)[1].lower()

        if ext == ".ulg":
            return PX4Parser()

        elif ext == ".bin":
            return ArduPilotParser()

        elif ext in [".bfl", ".bbl"]:
            return BetaflightParser()

        else:
            raise ValueError(
                f"Unsupported log file extension: '{ext}'"
            )