import os
import json
import uuid
import time
from typing import List, Dict, Any, Optional

HISTORY_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chat_history.json")

class ChatHistoryManager:
    """Manages local chat history persistent storage."""
    def __init__(self, storage_file: str = HISTORY_FILE):
        self.storage_file = storage_file
        self._ensure_storage()

    def _ensure_storage(self):
        if not os.path.exists(self.storage_file):
            self._save_data({"sessions": {}})

    def _load_data(self) -> Dict[str, Any]:
        try:
            with open(self.storage_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"sessions": {}}

    def _save_data(self, data: Dict[str, Any]):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def list_sessions(self) -> List[Dict[str, Any]]:
        data = self._load_data()
        sessions = list(data.get("sessions", {}).values())
        return sorted(sessions, key=lambda x: x.get("updated_at", 0), reverse=True)

    def create_session(self, title: str = "Chat Baru") -> Dict[str, Any]:
        data = self._load_data()
        session_id = str(uuid.uuid4())
        now = time.time()
        session = {
            "id": session_id,
            "title": title,
            "created_at": now,
            "updated_at": now,
            "messages": []
        }
        data["sessions"][session_id] = session
        self._save_data(data)
        return session

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        data = self._load_data()
        return data.get("sessions", {}).get(session_id)

    def add_message(self, session_id: str, role: str, content: str, reasoning: str = "") -> Dict[str, Any]:
        data = self._load_data()
        if session_id not in data.get("sessions", {}):
            session = self.create_session()
            session_id = session["id"]
            data = self._load_data()

        session = data["sessions"][session_id]
        msg_id = str(uuid.uuid4())
        message = {
            "id": msg_id,
            "role": role,
            "content": content,
            "reasoning": reasoning,
            "timestamp": time.time()
        }
        session["messages"].append(message)
        session["updated_at"] = time.time()

        # Update title if it's default and first user message
        if session["title"] in ["Chat Baru", "Untitled Chat"] and role == "user":
            session["title"] = content[:30] + ("..." if len(content) > 30 else "")

        self._save_data(data)
        return message

    def delete_session(self, session_id: str) -> bool:
        data = self._load_data()
        if session_id in data.get("sessions", {}):
            del data["sessions"][session_id]
            self._save_data(data)
            return True
        return False

    def clear_all(self):
        self._save_data({"sessions": {}})
