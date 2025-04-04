from transformers import DonutProcessor, VisionEncoderDecoderModel
import torch
from pdf2image import convert_from_path
from PIL import Image

import logging
logging.basicConfig(level=logging.DEBUG)

def pdf_to_image(pdf_path):
    images = convert_from_path(pdf_path, first_page=1, last_page=1, dpi=300)
    return images[0].convert("RGB") if images else None

# Prozessor und Modell vom feinjustierten Modell laden
processor = DonutProcessor.from_pretrained("scharnot/donut-invoices")
model = VisionEncoderDecoderModel.from_pretrained("scharnot/donut-invoices")

# Gerätekonfiguration
device = "cuda" if torch.cuda.is_available() else "cpu"
model.to(device)

def extract_invoice_data(pdf_path):
    image = pdf_to_image(pdf_path)
    if not image:
        return None

    # Manuelle Bildvorverarbeitung mit Pillow
    try:
        processed_image = image.resize((1280, 960))  # Beispielgröße, ggf. anpassen
        pixel_values = processor(images=processed_image, return_tensors="pt").pixel_values
    except Exception as e:
        logging.error(f"Fehler bei der Bildvorverarbeitung: {e}")
        return None  # Oder eine andere Fehlerbehandlung

    # Generierung anpassen (wenn nötig)
    task_prompt = "<s_receipt_de>"  # Oder ein anderes Prompt, je nach Modell
    decoder_input_ids = processor.tokenizer(
        task_prompt,
        add_special_tokens=False,
        return_tensors="pt"
    ).input_ids

    outputs = model.generate(
        pixel_values.to(device),
        decoder_input_ids=decoder_input_ids.to(device),
        max_length=model.decoder.config.max_position_embeddings,
        pad_token_id=processor.tokenizer.pad_token_id,
        eos_token_id=processor.tokenizer.eos_token_id,
        use_cache=True,
        bad_words_ids=[[processor.tokenizer.unk_token_id]],
        return_dict_in_generate=True,
    )

    # Ergebnisformatierung
    sequence = processor.batch_decode(outputs.sequences)[0]
    sequence = sequence.replace(processor.tokenizer.eos_token, "").replace(processor.tokenizer.pad_token, "")
    return processor.token2json(sequence)

# Beispielanwendung
result = extract_invoice_data("/Users/eberl/eberl.cloud/Medmind/Posteingang/Test.pdf")
if result:
    print(f"""
Rechnungsdatum: {result.get('date', 'nicht gefunden')}
Lieferant: {result.get('supplier', 'nicht gefunden')}
Empfänger: {result.get('recipient', 'nicht gefunden')}
""")
else:
    print("Rechnung konnte nicht verarbeitet werden.")