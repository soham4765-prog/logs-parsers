from abc import ABC, abstractmethod
import pandas as pd


class BaseParser(ABC):
    """Abstract Base Class that every flight controller parser must implement."""

    @abstractmethod
    def extract_raw_df(self, file_path: str) -> pd.DataFrame:
        """
        Reads the binary log file and extracts raw, un-aligned telemetry fields.
        Must return a DataFrame containing at least a raw timestamp column.
        """
        pass

    @abstractmethod
    def get_fc_type(self) -> str:
        """Returns the flight controller type identifier string."""
        pass