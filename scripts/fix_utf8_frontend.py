from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

EXTENSIONS = {
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".css",
    ".html",
    ".json",
}


REPLACEMENTS = {
    # Vocales minúsculas
    "Ã¡": "á",
    "Ã©": "é",
    "Ã­": "í",
    "Ã³": "ó",
    "Ãº": "ú",

    # Vocales mayúsculas
    "Ã": "Á",
    "Ã‰": "É",
    "Ã": "Í",
    "Ã“": "Ó",
    "Ãš": "Ú",

    # Eñe
    "Ã±": "ñ",
    "Ã‘": "Ñ",

    # Diéresis
    "Ã¼": "ü",
    "Ãœ": "Ü",

    # Signos
    "Â·": "·",
    "Ã—": "×",
    "Â¿": "¿",
    "Â¡": "¡",
    "Â°": "°",

    # Rayas y comillas
    "â€”": "—",
    "â€“": "–",
    "â€œ": "“",
    "â€": "”",
    "â€˜": "‘",
    "â€™": "’",
    "â€¦": "…",

    # Espacio no separable mal interpretado
    "Â ": " ",
}


def repair_file(path: Path) -> bool:
    try:
        original = path.read_text(
            encoding="utf-8",
        )
    except UnicodeDecodeError:
        print(
            f"[OMITIDO] No es UTF-8 legible: {path}"
        )
        return False

    repaired = original

    for broken, correct in REPLACEMENTS.items():
        repaired = repaired.replace(
            broken,
            correct,
        )

    if repaired == original:
        return False

    path.write_text(
        repaired,
        encoding="utf-8",
        newline="\n",
    )

    print(
        f"[CORREGIDO] {path.relative_to(ROOT)}"
    )

    return True


def main():
    frontend_src = (
        ROOT
        / "frontend"
        / "src"
    )

    if not frontend_src.exists():
        raise SystemExit(
            "No se encontró frontend/src. "
            "Ejecute este script desde el proyecto correcto."
        )

    corrected = 0

    for path in frontend_src.rglob("*"):
        if (
            path.is_file()
            and path.suffix.lower()
            in EXTENSIONS
        ):
            if repair_file(path):
                corrected += 1

    print()
    print(
        "=========================================="
    )
    print(
        "REPARACIÓN UTF-8 FINALIZADA"
    )
    print(
        "=========================================="
    )
    print(
        f"Archivos modificados: {corrected}"
    )
    print(
        "Todos los archivos modificados fueron "
        "guardados nuevamente como UTF-8."
    )


if __name__ == "__main__":
    main()
