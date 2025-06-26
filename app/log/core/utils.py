def clean(doc: dict) -> dict:
    doc.pop("_id", None)
    return doc

