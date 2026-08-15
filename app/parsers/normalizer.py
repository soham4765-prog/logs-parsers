import numpy as np
import pandas as pd

from app.parsers.schema import UTS_STANDARD_COLUMNS


class NormalizationEngine:

    @staticmethod
    def normalize_to_uts(
        raw_df: pd.DataFrame,
        target_freq_hz: int = 50
    ) -> pd.DataFrame:
        """
        Resamples and normalizes raw telemetry data into a uniform UTS dataset.
        """

        if 'timestamp_sec' not in raw_df.columns or raw_df.empty:
            raise ValueError(
                "Input DataFrame lacks 'timestamp_sec' column or is empty."
            )

        # Sort and remove duplicate timestamps
        df = (
            raw_df
            .sort_values('timestamp_sec')
            .drop_duplicates(subset=['timestamp_sec'])
        )

        # 1. Timeline normalization
        # Reset time baseline to start at 0.000 seconds
        t_start = df['timestamp_sec'].iloc[0]

        df['time_sec'] = df['timestamp_sec'] - t_start

        # 2. Create uniform resampling time grid
        # Example: 50 Hz = 0.02 second step
        dt = 1.0 / target_freq_hz

        uniform_time_grid = np.arange(
            0.0,
            df['time_sec'].max(),
            dt
        )

        grid_df = pd.DataFrame({
            'time_sec': uniform_time_grid
        })

        # 3. Align raw telemetry onto uniform time grid
        uts_df = pd.merge_asof(
            grid_df,
            df,
            on='time_sec',
            direction='nearest'
        )

        # 4. Fill missing values
        uts_df = uts_df.ffill().bfill()

        # 5. Ensure all standard UTS columns exist
        for col in UTS_STANDARD_COLUMNS:
            if col not in uts_df.columns:
                uts_df[col] = np.nan

        # 6. Select and reorder according to UTS schema
        final_uts = uts_df[UTS_STANDARD_COLUMNS].copy()

        # 7. Clean numerical precision
        final_uts = final_uts.round(4)

        return final_uts