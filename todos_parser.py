import json


class TODOParser:
    DEFAULT_LIST_NAME = "默认清单"

    @staticmethod
    def _normalize_todo_entry(item):
        if isinstance(item, dict):
            return {
                "text": str(item.get("text", "")),
                "done": bool(item.get("done", False)),
                "reminder": item.get("reminder", None),
            }
        return {"text": str(item), "done": False, "reminder": None}

    def __init__(self, path):
        self.path = path
        self.todos = []
        self.lists = {self.DEFAULT_LIST_NAME: []}

        self.read()

    def read(self):
        """
        Read To-Dos from todos.ini
        """
        with open(self.path, encoding="utf-8") as file:
            content = file.read()

        if content.strip() == "":
            self.todos = []
            self.lists = {self.DEFAULT_LIST_NAME: []}
            return

        # 新格式：JSON（支持多清单）
        try:
            data = json.loads(content)
            if isinstance(data, dict):
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

                if not normalized_lists:
                    normalized_lists = {self.DEFAULT_LIST_NAME: []}

                self.lists = normalized_lists
                self.todos = list(next(iter(self.lists.values())))
                return
        except json.JSONDecodeError:
            pass

        # 兼容旧格式：<TODO-START-MARK>
        todos = content.split("<TODO-START-MARK>")[1:]
        self.todos = todos
        self.lists = {
            self.DEFAULT_LIST_NAME: [self._normalize_todo_entry(t) for t in todos]
        }

    def write(self):
        """
        Write current To-Do list into todos.ini
        """
        if not self.lists:
            self.lists = {self.DEFAULT_LIST_NAME: []}

        with open(self.path, "w", encoding="utf-8") as file:
            json.dump(
                {"version": 2, "lists": self.lists},
                file,
                ensure_ascii=False,
                indent=2
            )

    def add(self, text: str):
        """
        Add new To-Do into self.todos
        :param text: To-Do
        """
        self.todos.append(text)
