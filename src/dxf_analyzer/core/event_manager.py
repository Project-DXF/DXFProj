from PyQt5.QtCore import QObject, pyqtSignal


class EventManager(QObject):
    
    dxf_loaded = pyqtSignal(str, object)
    dxf_processed = pyqtSignal(dict)  
    theme_changed = pyqtSignal(bool)  
    
    def __init__(self):
        super().__init__()
        self._current_dxf_file = None
        self._current_dxf_doc = None
        
    @property
    def current_dxf_file(self):
        return self._current_dxf_file
        
    @property
    def current_dxf_doc(self):
        return self._current_dxf_doc
    
    def update_dxf(self, file_path: str, doc: object):
        self._current_dxf_file = file_path
        self._current_dxf_doc = doc
        self.dxf_loaded.emit(file_path, doc)
    
    def notify_dxf_processed(self, results: dict):
        self.dxf_processed.emit(results)
    
    def notify_theme_changed(self, is_dark: bool):
        self.theme_changed.emit(is_dark) 