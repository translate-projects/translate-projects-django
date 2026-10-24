from .hashing import generate_short_hash


def recreate_json(original_translations, data_result_translations):
    new_json_recreate = {}
    for key, value in original_translations.items():
        simple_hash = generate_short_hash(key)
        if simple_hash in data_result_translations:
            new_json_recreate[key] = data_result_translations[simple_hash]
    return new_json_recreate
