import json


def file_path(sub_dir: str, filename: str) -> str:
    return (
        f"tests/test_files/{sub_dir}/{filename}"
        if sub_dir
        else f"tests/test_files/{filename}"
    )


def write_json_file(sub_dir: str, filename: str, result: str):
    with open(file_path(sub_dir, filename), "w", encoding="utf-8") as f:
        f.write(json.dumps(json.loads(result), indent=2))


def read_json_file(sub_dir: str, filename: str):
    with open(file_path(sub_dir, filename), "r") as f:
        return json.dumps(
            json.load(f)
        )  # Odd, but doing it for consistency of processing
