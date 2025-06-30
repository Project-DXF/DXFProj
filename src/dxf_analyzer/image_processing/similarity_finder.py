import os
from typing import List, Dict, Any
from pathlib import Path
from .image_analyzer import ImageAnalyzer


class SimilarityFinder:
    
    def __init__(self, database_path: str = None):
        self.database_path = database_path or os.path.join(os.path.dirname(__file__), "..", "..", "data")
        self.image_analyzer = ImageAnalyzer()
        
    def set_database_path(self, path: str):
        self.database_path = path
        
    def find_similar_dxfs(self, image_path: str, max_results: int = 5) -> List[Dict[str, Any]]:
        if not self.image_analyzer.load_image(image_path):
            return []
            
        results = []
        
        for root, _, files in os.walk(self.database_path):
            for file in files:
                if file.lower().endswith('.dxf'):
                    dxf_path = os.path.join(root, file)
                    similarity = self.image_analyzer.compare_with_dxf(dxf_path)
                    
                    if similarity > 0:
                        results.append({
                            'path': dxf_path,
                            'filename': file,
                            'similarity': round(similarity * 100, 2),
                            'id': self._generate_id(dxf_path)
                        })
        
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:max_results]
        
    def _generate_id(self, file_path: str) -> str:
        rel_path = os.path.relpath(file_path, self.database_path)
        return f"DB{hash(rel_path) & 0xFFFFFF:06x}" 