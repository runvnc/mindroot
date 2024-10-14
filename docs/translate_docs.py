import os
import polib
import logging
from anthropic_translate import translate_text

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def translate_docs(pot_dir: str, languages: list[str]):
    """
    Automate translation of documentation using Anthropic's API.
    
    :param pot_dir: Directory containing .pot files
    :param languages: List of target languages (e.g., ['es', 'fr', 'de', 'ru', 'zh-CN', 'hi', 'ar'])
    """
    for pot_file in os.listdir(pot_dir):
        if pot_file.endswith('.pot'):
            pot_path = os.path.join(pot_dir, pot_file)
            po = polib.pofile(pot_path)
            
            for lang in languages:
                po_dir = os.path.join(pot_dir, lang, 'LC_MESSAGES')
                os.makedirs(po_dir, exist_ok=True)
                po_path = os.path.join(po_dir, pot_file.replace('.pot', '.po'))
                
                if os.path.exists(po_path):
                    po_target = polib.pofile(po_path)
                else:
                    po_target = polib.POFile()
                    po_target.metadata = po.metadata
                
                for entry in po:
                    existing_entry = po_target.find(entry.msgid)
                    if existing_entry and existing_entry.msgstr:
                        continue  # Skip if already translated
                    
                    try:
                        context = entry.msgctxt or 'Technical documentation'
                        # Add surrounding entries for more context
                        surrounding_entries = po.find_surrounding_entries(entry)
                        if surrounding_entries:
                            context += "\n\nSurrounding text:\n" + "\n".join([e.msgid for e in surrounding_entries])
                        
                        translated = translate_text('English', lang, context, entry.msgid)
                        if existing_entry:
                            existing_entry.msgstr = translated
                        else:
                            new_entry = polib.POEntry(
                                msgid=entry.msgid,
                                msgstr=translated,
                                msgctxt=entry.msgctxt
                            )
                            po_target.append(new_entry)
                        logging.info(f'Translated: {entry.msgid[:30]}... to {lang}')
                    except Exception as e:
                        logging.error(f'Error translating {entry.msgid[:30]}... to {lang}: {str(e)}')
                
                po_target.save(po_path)
                logging.info(f'Saved translations for {lang} in {po_path}')

if __name__ == '__main__':
    translate_docs('/files/ah/docs/_build/gettext', ['es', 'fr', 'de', 'ru', 'zh-CN', 'hi', 'ar'])
