import json
import time
import uuid

from config_paths import mirror_user_ini_to_application_dir
from safe_io import atomic_write_text, backup_path_for, read_text_if_exists, restore_backup


class TODOParser:
    DEFAULT_LIST_NAME = "默认清单"
    SYSTEM_ARCHIVE_LIST = "__archive__"
    SYSTEM_TRASH_LIST = "__trash__"
    SYSTEM_LIST_NAMES = (SYSTEM_ARCHIVE_LIST, SYSTEM_TRASH_LIST)
    VERSION = 4

    @staticmethod
    def generate_todo_id():
        return uuid.uuid4().hex

    @classmethod
    def is_system_list_name(cls, list_name):
        return str(list_name) in cls.SYSTEM_LIST_NAMES

    @staticmethod
    def _normalize_todo_entry(item):
        now = int(time.time())
        if isinstance(item, dict):
            tp_raw = item.get("today_priority", False)
            if isinstance(tp_raw, str):
                today_priority = tp_raw.strip().lower() in ("1", "true", "yes", "y", "on")
            else:
                today_priority = bool(tp_raw)
            origin_raw = str(item.get("origin_list", "")).strip()
            if origin_raw == "" or origin_raw.lower() in ("none", "null"):
                origin_list = None
            else:
                origin_list = origin_raw
            return {
                "id": str(item.get("id", "")).strip() or TODOParser.generate_todo_id(),
                "text": str(item.get("text", "")),
                "done": bool(item.get("done", False)),
                "reminder": item.get("reminder", None),
                "order_key": item.get("order_key", item.get("created_order", None)),
                "completed_rank": item.get("completed_rank", None),
                "created_at": int(item.get("created_at", now)) if isinstance(item.get("created_at", now), (int, float)) else now,
                "today_priority": today_priority,
                "origin_list": origin_list,
                "deleted_at": item.get("deleted_at", None),
                "archived_at": item.get("archived_at", None),
            }
        return {
            "id": TODOParser.generate_todo_id(),
            "text": str(item),
            "done": False,
            "reminder": None,
            "order_key": None,
            "completed_rank": None,
            "created_at": now,
            "today_priority": False,
            "origin_list": None,
            "deleted_at": None,
            "archived_at": None,
        }

    def __init__(self, path):
        self.path = path
        self.todos = []
        self.lists = self._ensure_required_lists({self.DEFAULT_LIST_NAME: []})

        self.read()

    def read(self):
        """
        Read To-Dos from todos.ini
        """
        try:
            lists = self._load_lists_from_path(self.path)
        except (OSError, ValueError):
            bak = backup_path_for(self.path)
            try:
                lists = self._load_lists_from_path(str(bak))
            except (OSError, ValueError):
                lists = self._ensure_required_lists({self.DEFAULT_LIST_NAME: []})
            else:
                restore_backup(self.path)

        self.lists = self._ensure_required_lists(lists)
        self.todos = list(next(iter(self.user_lists().values()), []))

    def write(self):
        """
        Write current To-Do list into todos.ini
        """
        self.lists = self._ensure_required_lists(self.lists)
        serialized = json.dumps(
            {"version": self.VERSION, "lists": self.lists},
            ensure_ascii=False,
            indent=2,
        )
        atomic_write_text(self.path, serialized, encoding="utf-8", keep_backup=True)
        mirror_user_ini_to_application_dir(self.path)

    def add(self, text: str):
        """
        Add new To-Do into self.todos
        :param text: To-Do
        """
        self.todos.append(self._normalize_todo_entry(text))

    def user_lists(self):
        return {
            list_name: todos
            for list_name, todos in self.lists.items()
            if not self.is_system_list_name(list_name)
        }

    def visible_list_names(self):
        return list(self.user_lists().keys())

    def ensure_required_lists(self):
        self.lists = self._ensure_required_lists(self.lists)
        return self.lists

    def find_todo(self, todo_id, include_system_lists=True):
        for list_name, todos in self.lists.items():
            if not include_system_lists and self.is_system_list_name(list_name):
                continue
            for index, todo in enumerate(todos):
                if str(todo.get("id", "")) == str(todo_id):
                    return list_name, index, todo
        return None, None, None

    def next_order_key(self, list_name):
        orders = [
            int(todo.get("order_key", 0))
            for todo in self.lists.get(list_name, [])
            if isinstance(todo.get("order_key", None), (int, float))
        ]
        return max(orders, default=0) + 1

    def next_completed_rank(self, list_name):
        ranks = [
            int(todo.get("completed_rank", 0))
            for todo in self.lists.get(list_name, [])
            if isinstance(todo.get("completed_rank", None), (int, float))
        ]
        return max(ranks, default=0) + 1

    def move_todo_to_system_list(self, todo_id, target_list):
        self.ensure_required_lists()
        source_list, index, todo = self.find_todo(todo_id, include_system_lists=True)
        if todo is None or source_list == target_list:
            return None

        moved = dict(todo)
        self.lists[source_list].pop(index)
        now = int(time.time())
        if target_list == self.SYSTEM_ARCHIVE_LIST:
            moved["origin_list"] = source_list if not self.is_system_list_name(source_list) else moved.get("origin_list")
            moved["archived_at"] = now
            moved["deleted_at"] = None
        elif target_list == self.SYSTEM_TRASH_LIST:
            moved["origin_list"] = source_list if not self.is_system_list_name(source_list) else moved.get("origin_list")
            moved["deleted_at"] = now
            moved["archived_at"] = None
        self.lists[target_list].append(moved)
        return moved

    def restore_todo_from_system_list(self, todo_id, destination_list=None):
        source_list, index, todo = self.find_todo(todo_id, include_system_lists=True)
        if todo is None or not self.is_system_list_name(source_list):
            return None

        self.ensure_required_lists()
        target_list = destination_list or todo.get("origin_list") or self.DEFAULT_LIST_NAME
        if self.is_system_list_name(target_list):
            target_list = self.DEFAULT_LIST_NAME
        if target_list not in self.lists:
            self.lists[target_list] = []

        restored = dict(todo)
        restored["origin_list"] = None
        restored["deleted_at"] = None
        restored["archived_at"] = None
        if restored.get("done", False):
            restored["completed_rank"] = self.next_completed_rank(target_list)
        else:
            restored["completed_rank"] = None
            restored["order_key"] = self.next_order_key(target_list)

        self.lists[source_list].pop(index)
        self.lists[target_list].append(restored)
        return target_list, restored

    def permanently_delete_todo(self, todo_id):
        list_name, index, todo = self.find_todo(todo_id, include_system_lists=True)
        if todo is None:
            return None
        self.lists[list_name].pop(index)
        return list_name, todo

    def archive_completed_in_list(self, list_name):
        if list_name not in self.lists or self.is_system_list_name(list_name):
            return 0

        self.ensure_required_lists()
        archived = []
        remaining = []
        now = int(time.time())
        for todo in self.lists[list_name]:
            item = dict(todo)
            if item.get("done", False):
                item["origin_list"] = list_name
                item["archived_at"] = now
                item["deleted_at"] = None
                archived.append(item)
            else:
                remaining.append(item)

        self.lists[list_name] = remaining
        self.lists[self.SYSTEM_ARCHIVE_LIST].extend(archived)
        return len(archived)

    def _load_lists_from_path(self, path):
        content = read_text_if_exists(path, encoding="utf-8")
        return self._parse_lists_content(content)

    def _parse_lists_content(self, content):
        if content.strip() == "":
            return self._ensure_required_lists({self.DEFAULT_LIST_NAME: []})

        stripped = content.lstrip()
        if stripped.startswith("{"):
            data = json.loads(content)
            if not isinstance(data, dict):
                raise ValueError("invalid todos json payload")
            lists_data = data.get("lists", {})
            normalized_lists = {}
            if isinstance(lists_data, dict):
                for list_name, todos in lists_data.items():
                    name = str(list_name).strip()
                    if name == "":
                        continue
                    if isinstance(todos, list):
                        normalized_lists[name] = [
                            self._normalize_todo_entry(item) for item in todos
                        ]
            return self._ensure_required_lists(normalized_lists or {self.DEFAULT_LIST_NAME: []})

        if "<TODO-START-MARK>" not in content:
            raise ValueError("unrecognized todos format")

        todos = content.split("<TODO-START-MARK>")[1:]
        return self._ensure_required_lists(
            {self.DEFAULT_LIST_NAME: [self._normalize_todo_entry(t) for t in todos]}
        )

    @classmethod
    def _ensure_required_lists(cls, lists_data):
        normalized = {}
        if isinstance(lists_data, dict):
            for list_name, todos in lists_data.items():
                name = str(list_name).strip()
                if name == "":
                    continue
                normalized[name] = [
                    cls._normalize_todo_entry(item) for item in (todos if isinstance(todos, list) else [])
                ]

        if cls.DEFAULT_LIST_NAME not in normalized:
            normalized_with_default = {cls.DEFAULT_LIST_NAME: []}
            normalized_with_default.update(normalized)
            normalized = normalized_with_default

        for system_name in cls.SYSTEM_LIST_NAMES:
            normalized.setdefault(system_name, [])

        return normalized
