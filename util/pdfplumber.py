import pdfplumber
from typing import List, Tuple


def find_text_coordinates(pdf_path: str,
                          search_text: str,
                          padding: int = 10,
                          visualize: bool = False) -> List[Tuple[float]]:
    """
    Findet alle Vorkommen eines Textes im PDF und gibt deren Koordinatenbereiche zurück.

    Parameter:
    pdf_path (str): Pfad zur PDF-Datei
    search_text (str): Zu suchender Text (exakte Übereinstimmung)
    padding (int): Erweiterung des Bereichs in Punkten
    visualize (bool): Markiert Fundstellen als Bild

    Returns:
    List[Tuple]: Liste der Koordinaten-Tupel (x0, top, x1, bottom, page_num)
    """

    results = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            # Extrahiert Wörter mit Koordinaten
            words = page.extract_words(x_tolerance=3, y_tolerance=3, extra_attrs=["size"])

            # Durchsuche alle Wörter
            for word in words:
                if word['text'] == search_text:
                    # Basis-Koordinaten
                    x0 = word['x0']
                    top = word['top']
                    x1 = word['x1']
                    bottom = word['bottom']

                    # Bereich erweitern
                    expanded = (
                        max(0, x0 - padding),
                        max(0, top - padding),
                        x1 + padding,
                        bottom + padding
                    )

                    results.append((*expanded, page_num))

                    # Visualisierung
                    if visualize:
                        img = page.to_image(resolution=150)
                        img.draw_rect((x0, top, x1, bottom), fill=(255, 0, 0, 50), stroke="red")
                        img.draw_rect(expanded, fill=(0, 255, 0, 20), stroke="green")
                        img.save(f"page_{page_num}_match.png")

    return results if results else None
