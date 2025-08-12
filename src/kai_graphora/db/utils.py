from pathlib import Path


def parse_time(time: str) -> float:
    r"""
    Examples:
    - "123.456µs" => 0.123456
    - "1.939083ms" => 1.939083
    - "1ms" => 1
    - "1.2345s" => 1234.5
    """
    import re

    regex = re.compile(r"(\d+\.?\d*)s")
    match = regex.match(time)
    if match:
        return float(match.group(1)) * 1000
    regex = re.compile(r"(\d+\.?\d*)ms")
    match = regex.match(time)
    if match:
        return float(match.group(1))
    regex = re.compile(r"(\d+\.?\d*)µs")
    match = regex.match(time)
    if match:
        return float(match.group(1)) / 1000
    raise ValueError(f"Invalid time format: {time}")


def load_surql(filename: str) -> str:
    file_path = Path(__file__).parent / "surql" / filename
    with open(file_path, "r") as file:
        return file.read()
