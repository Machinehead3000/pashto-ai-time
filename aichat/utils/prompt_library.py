import os
import json
from typing import List, Dict, Optional

PROMPT_LIBRARY_PATH = os.path.expanduser(os.path.join("~", ".aichat_prompts.json"))

class PromptLibrary:
    def __init__(self, path: Optional[str] = None):
        self.path = path or PROMPT_LIBRARY_PATH
        self.prompts = self._load_prompts()

    def _load_prompts(self) -> List[Dict[str, str]]:
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def _save_prompts(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.prompts, f, indent=2, ensure_ascii=False)

    def get_prompts(self) -> List[Dict[str, str]]:
        return self.prompts

    def add_prompt(self, name: str, text: str):
        self.prompts.append({"name": name, "text": text})
        self._save_prompts()

    def delete_prompt(self, name: str):
        self.prompts = [p for p in self.prompts if p["name"] != name]
        self._save_prompts()

    def rename_prompt(self, old_name: str, new_name: str):
        for p in self.prompts:
            if p["name"] == old_name:
                p["name"] = new_name
        self._save_prompts()

    def update_prompt(self, name: str, new_text: str):
        for p in self.prompts:
            if p["name"] == name:
                p["text"] = new_text
        self._save_prompts() 