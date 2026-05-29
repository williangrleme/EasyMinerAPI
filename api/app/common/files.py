from io import BytesIO

import pandas as pd


def bytes_to_mb_label(num_bytes: int) -> str:
    return f"{round(num_bytes / (1024 * 1024), 4)}MB"


def read_csv(file_url: str) -> pd.DataFrame:
    return pd.read_csv(file_url)


def dataframe_to_csv_upload(df: pd.DataFrame, filename: str):
    buffer = BytesIO()
    df.to_csv(buffer, header=True, index=False)
    size_label = bytes_to_mb_label(buffer.getbuffer().nbytes)
    buffer.seek(0)
    buffer.filename = filename
    buffer.content_type = "text/csv"
    return buffer, size_label
