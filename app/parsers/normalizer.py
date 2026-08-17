# app/parsers/normalizer.py
import numpy as np
import pandas as pd

try:
    from app.parsers.schema1 import UTS_STANDARD_COLUMNS
except ImportError:
    from schema1 import UTS_STANDARD_COLUMNS


class NormalizationEngine:
    @staticmethod
    def normalize_to_uts(
        raw_df: pd.DataFrame,
        target_freq_hz: int = 50
    ) -> pd.DataFrame:
        """
        Resamples raw telemetry onto a uniform 50 Hz time grid and orders columns
        strictly matching UTS_STANDARD_COLUMNS.
        """
        if raw_df.empty or "timestamp_sec" not in raw_df.columns:
            raise ValueError("Input raw DataFrame lacks 'timestamp_sec' or is empty.")

        # 1. Sort & drop timestamp duplicates
        df = (
            raw_df
            .sort_values("timestamp_sec")
            .drop_duplicates(subset=["timestamp_sec"])
            .reset_index(drop=True)
        )

        # 2. Reset time baseline to 0.000s
        t_start = df["timestamp_sec"].iloc[0]
        df["time_sec"] = df["timestamp_sec"] - t_start

        # 3. Create 50 Hz uniform time grid (0.02s step)
        dt = 1.0 / target_freq_hz
        t_max = df["time_sec"].max()
        if t_max <= 0:
            t_max = dt
        uniform_time_grid = np.arange(0.0, t_max + dt, dt)
        grid_df = pd.DataFrame({"time_sec": uniform_time_grid})

        # 4. As-of join to align asynchronous sensor messages to nearest time step
        uts_df = pd.merge_asof(
            grid_df,
            df,
            on="time_sec",
            direction="nearest"
        )

        # 5. Forward-fill then backward-fill sparse values
        uts_df = uts_df.ffill().bfill()

        # 6. Ensure all schema1 columns exist (fill missing sensors with NaN)
        for col in UTS_STANDARD_COLUMNS:
            if col not in uts_df.columns:
                uts_df[col] = np.nan

        # 7. Select & reorder strictly matching schema1.py
        final_uts = uts_df[UTS_STANDARD_COLUMNS].copy()

        # Round numeric values for storage efficiency
        num_cols = [c for c in final_uts.columns if c != "flight_mode"]
        final_uts[num_cols] = final_uts[num_cols].apply(pd.to_numeric, errors="coerce").round(4)

        return final_uts