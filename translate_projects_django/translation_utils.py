import polib
import os

def generate_new_file_po(current_po, language, recreate_json, locale_dir):
    # Create a new .po file
    new_po = polib.POFile()

    # Add metadata to the .po file
    new_po.metadata = {
        'Project-Id-Version': '1.0',
        'Content-Type': 'text/plain; charset=utf-8',
        'Content-Transfer-Encoding': '8bit',
        'Language': language,
    }

    # Copy entries from the original file
    new_po.extend(current_po)

    # Update msgstr of entries with the data from recreate_json
    for entry in current_po:
        if entry.msgid in recreate_json:
            entry.msgstr = recreate_json[entry.msgid]

    # Create the necessary directories for the new file
    new_po_file_path = os.path.join(locale_dir, language, 'LC_MESSAGES', 'django.po')
    os.makedirs(os.path.dirname(new_po_file_path), exist_ok=True)

    # Save the .po file with the updates
    new_po.save(new_po_file_path)

    return new_po
