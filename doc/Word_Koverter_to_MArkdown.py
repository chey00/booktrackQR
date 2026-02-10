from markitdown import MarkItDown
from pathlib import Path

def docx_to_markdown(input_path: str, output_path: str = "README.md") -> None:
    """
    Konvertiert eine .docx-Datei in Markdown und speichert das Ergebnis.
    """
    input_file = Path(input_path)
    if not input_file.exists():
        raise FileNotFoundError(f"Datei nicht gefunden: {input_file}")

    md = MarkItDown()
    result = md.convert(str(input_file))

    # result.text enthält den Markdown-Text
    output_file = Path(output_path)
    output_file.write_text(result.markdown, encoding="utf-8")
    print(f"Markdown gespeichert in: {output_file.resolve()}")

if __name__ == "__main__":
    # HIER den Namen deiner Word-Datei anpassen:
    docx_to_markdown("/Users/studentfs/PycharmProjects/booktrackQR/doc/READme_Bücherapp_1.1.docx", "README_1.1.md")
