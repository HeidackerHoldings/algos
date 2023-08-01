import subprocess
from typing import Literal, Optional
from datetime import date, timedelta
import os
from tqdm import tqdm
import contextlib
import io
import sys
import argparse


SEED = 42


@contextlib.contextmanager
def nostdout():
    save_stdout = sys.stdout
    sys.stdout = io.BytesIO()
    yield
    sys.stdout = save_stdout


def format_datetime(dt: date) -> int:
    return int(f"{dt.year}{dt.month:02d}{dt.day:02d}")


def parse_datetime(dt: int) -> date:
    dt = str(dt)
    year = int(dt[:4])
    month = int(dt[4:6])
    day = int(dt[6:])
    return date(year, month, day)


def get_lean_command(**flags):
    command = "lean data generate"
    for k, v in flags.items():
        command += f" --{k.replace('_', '-')}"
        if v is not None:
            command += f" {v}"
    return command


def generate(
    name: str,
    start: date,
    end: date = date.today(),
    density: Literal["Dense", "Sparse", "VerySparse"] = "Dense",
    chain_symbol_count: int = 10,
    delta: timedelta = timedelta(2),
) -> None:
    args = {
        "tickers": name,
        "resolution": "Minute",
        "data_density": density,
        "include_coarse": False,
        "market": "usa",
        "random_seed": SEED,
    }

    dateranges = []
    previous = start
    current = start + delta
    while current <= end:
        dateranges.append((previous, current))
        previous = current
        current += delta

    os.system(
        get_lean_command(
            **args,
            start=format_datetime(start),
            end=format_datetime(end),
            security_type="Equity",
            update=None,
        )
    )
    for start, end in tqdm(dateranges[::-1]):
        with nostdout():
            os.system(
                get_lean_command(
                    **args,
                    start=format_datetime(start),
                    end=format_datetime(end),
                    security_type="Option",
                    chain_symbol_count=chain_symbol_count,
                    verbose=None,
                )
            )


if __name__ == "__main__":
    generate("SPYCC", date.today() - timedelta(90))
