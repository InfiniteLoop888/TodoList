from config_paths import _default_options_ini_text, mirror_user_ini_to_application_dir
from safe_io import atomic_write_text, backup_path_for, read_text_if_exists, restore_backup


class SettingsParser:
    DEFAULT_TEXT = _default_options_ini_text()

    def __init__(self, path):
        self.ini_path = path
        self.options = {}

        self.load()

    def load(self):
        """
        Load keys and values from .ini file
        """
        options = dict(self._parse_ini_text(self.DEFAULT_TEXT))
        loaded = self._load_with_backup()
        options.update(loaded)
        self.options.update(options)

    def modify(self, key, value):
        """
        Modify the dict instead of using valuation
        :param key: key
        :param value: value
        """
        self.options[key] = value

    def write(self):
        """
        Write current options dict into .ini file
        """
        lines = [f"{key} = {value}\n" for key, value in self.options.items()]
        atomic_write_text(self.ini_path, "".join(lines), encoding="utf-8", keep_backup=True)
        mirror_user_ini_to_application_dir(self.ini_path)

    def _load_with_backup(self):
        try:
            return self._parse_primary_file(self.ini_path)
        except (OSError, ValueError):
            bak = backup_path_for(self.ini_path)
            try:
                options = self._parse_primary_file(str(bak))
            except (OSError, ValueError):
                return {}
            restore_backup(self.ini_path)
            return options

    def _parse_primary_file(self, path: str):
        text = read_text_if_exists(path, encoding="utf-8")
        options, has_data, has_legal_line = self._parse_ini_text(text, with_meta=True)
        if has_data and not has_legal_line:
            raise ValueError(f"invalid ini file: {path}")
        return options

    @staticmethod
    def _match_type(string: str):
        """
        If possible, convert string input into type it should be.\n
        Instances:
            str(1.234) -> float(1.234)\n
            str(False) -> bool(False)\n
            str(name) -> str(name)  (this method does nothing)\n
        :return: result of converting
        """
        if string == "True":
            return True

        if string == "False":
            return False

        try:
            if float(string) % 1 == 0:
                return int(float(string))
            else:
                return float(string)
        except ValueError:
            return string

    @staticmethod
    def _is_a_legal_line(line: str):
        """
        To check whether the line is a legal one which contains a key and a value
        :param line: a line in .ini file
        """
        if line.count("=") != 1:
            return False

        key, value = line.split("=")
        key = key.strip()
        value = value.strip()

        if key == "" or value == "":
            return False

        return True

    @classmethod
    def _parse_ini_text(cls, text: str, with_meta: bool = False):
        options = {}
        has_data = False
        has_legal_line = False

        for raw_line in text.splitlines():
            line = raw_line.strip()
            if line == "" or line.startswith("#") or line.startswith(";"):
                continue

            has_data = True
            if cls._is_a_legal_line(line) is False:
                continue

            key, value = line.split("=")
            options[key.strip()] = cls._match_type(value.strip())
            has_legal_line = True

        if with_meta:
            return options, has_data, has_legal_line
        return options
