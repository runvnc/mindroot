import os
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import shutil
import logging

logging.basicConfig(filename='pptx_stateless_editor.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class PresentationManager:
    def __init__(self):
        self.presentations = {}
        self.last_accessed = {}
        self.timeout = timedelta(minutes=30)  # Auto-close after 30 minutes of inactivity

    def _cleanup(self):
        now = datetime.now()
        for path, last_access in list(self.last_accessed.items()):
            if now - last_access > self.timeout:
                self.close_presentation(path)

    def _get_presentation(self, pptx_path):
        logging.debug(f"Getting presentation: {pptx_path}")
        self._cleanup()
        if pptx_path not in self.presentations:
            self.open_presentation(pptx_path)
        self.last_accessed[pptx_path] = datetime.now()
        return self.presentations[pptx_path]

    def open_presentation(self, pptx_path):
        logging.debug(f"Opening presentation: {pptx_path}")
        if not os.path.exists(pptx_path):
            raise FileNotFoundError(f"File not found: {pptx_path}")
        self.presentations[pptx_path] = zipfile.ZipFile(pptx_path, 'a')
        self.last_accessed[pptx_path] = datetime.now()
        return True

    def close_presentation(self, pptx_path):
        logging.debug(f"Closing presentation: {pptx_path}")
        if pptx_path in self.presentations:
            self.presentations[pptx_path].close()
            del self.presentations[pptx_path]
            del self.last_accessed[pptx_path]
        return True

    def save_presentation(self, pptx_path):
        logging.debug(f"Saving presentation: {pptx_path}")
        if pptx_path in self.presentations:
            self.presentations[pptx_path].close()
            temp_file = pptx_path + '.tmp'
            try:
                logging.debug(f"Creating temporary file: {temp_file}")
                with zipfile.ZipFile(self.presentations[pptx_path].filename, 'r') as zin:
                    with zipfile.ZipFile(temp_file, 'w') as zout:
                        for item in zin.infolist():
                            zout.writestr(item, zin.read(item.filename))
                logging.debug(f"Temporary file created successfully")
                try:
                    logging.debug(f"Attempting to replace {pptx_path} with {temp_file}")
                    os.replace(temp_file, pptx_path)
                    logging.debug(f"File replaced successfully")
                except OSError as e:
                    logging.warning(f"os.replace failed: {str(e)}. Trying shutil.move")
                    shutil.move(temp_file, pptx_path)
                    logging.debug(f"File moved successfully using shutil.move")
            except Exception as e:
                logging.error(f"Error saving presentation: {str(e)}")
                if os.path.exists(temp_file):
                    logging.debug(f"Removing temporary file: {temp_file}")
                    os.remove(temp_file)
                raise
            finally:
                logging.debug(f"Reopening presentation: {pptx_path}")
                self.presentations[pptx_path] = zipfile.ZipFile(pptx_path, 'a')
                self.last_accessed[pptx_path] = datetime.now()
        return True

presentation_manager = PresentationManager()

def open_presentation(pptx_path):
    return presentation_manager.open_presentation(pptx_path)

def close_presentation(pptx_path):
    return presentation_manager.close_presentation(pptx_path)

def save_presentation(pptx_path):
    return presentation_manager.save_presentation(pptx_path)

def extract_slide_xml(pptx_path, slide_number):
    pptx = presentation_manager._get_presentation(pptx_path)
    slide_path = f'ppt/slides/slide{slide_number}.xml'
    return pptx.read(slide_path).decode('utf-8')

def update_slide_xml(pptx_path, slide_number, new_xml):
    pptx = presentation_manager._get_presentation(pptx_path)
    slide_path = f'ppt/slides/slide{slide_number}.xml'
    pptx.writestr(slide_path, new_xml)
    return True

def clear_slide(pptx_path, slide_number):
    empty_slide_xml = """<?xml version='1.0' encoding='UTF-8' standalone='yes'?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm/></p:grpSpPr></p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>"""
    return update_slide_xml(pptx_path, slide_number, empty_slide_xml)

def append_to_slide(pptx_path, slide_number, xml_fragment):
    current_xml = extract_slide_xml(pptx_path, slide_number)
    root = ET.fromstring(current_xml)
    sp_tree = root.find('.//{http://schemas.openxmlformats.org/presentationml/2006/main}spTree')
    
    fragment_root = ET.fromstring(xml_fragment)
    for element in fragment_root:
        sp_tree.append(element)
    
    new_xml = ET.tostring(root, encoding='unicode')
    return update_slide_xml(pptx_path, slide_number, new_xml)
