import os
import calendar
from datetime import datetime, date, timedelta

from components import ThemedOptionCardPlane
from icons import IconDictionary
from PyQt5.Qt import QColor, QPoint
from PyQt5.QtCore import (
    QByteArray,
    QCoreApplication,
    QEvent,
    QEventLoop,
    QEasingCurve,
    QRect,
    QRectF,
    QSize,
    Qt,
    QTimer,
    QVariantAnimation,
    pyqtSignal,
)
from PyQt5.QtGui import QFont, QFontMetrics, QIcon, QPainter, QPixmap
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QComboBox,
    QDialog,
    QGraphicsDropShadowEffect,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSlider,
    QStyle,
    QSystemTrayIcon,
    QTabWidget,
    QGridLayout,
    QHBoxLayout,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from config_paths import ensure_user_ini_files
from settings_parser import SettingsParser
from windows_startup import is_startup_enabled, set_startup_enabled, startup_supported
from todos_parser import TODOParser

from siui.components.widgets import (
    SiCheckBox,
    SiDenseHContainer,
    SiDenseVContainer,
    SiLabel,
    SiSimpleButton,
    SiSvgLabel,
    SiSwitch,
    SiToggleButton,
)
from siui.core.animation import SiExpAnimation
from siui.core.color import Color
from siui.core.globals import NewGlobal, SiGlobal
from siui.gui.tooltip import ToolTipWindow

SiGlobal.todo_list = NewGlobal()

# 创建锁定位置变量
SiGlobal.todo_list.position_locked = False

# 创建设置文件解析器并写入全局变量（持久化在「文档/TodoList」，首次从程序目录复制）
_options_ini_path, _todos_ini_path = ensure_user_ini_files()
SiGlobal.todo_list.settings_parser = SettingsParser(_options_ini_path)
SiGlobal.todo_list.todos_parser = TODOParser(_todos_ini_path)


def todo_item_font_px():
    opts = SiGlobal.todo_list.settings_parser.options
    v = opts.get("TODO_ITEM_FONT_PX", 12)
    try:
        px = int(v)
    except (TypeError, ValueError):
        px = 12
    return max(8, min(24, px))


def todo_item_font_qfont():
    f = QFont(SiGlobal.siui.fonts["S_NORMAL"])
    f.setPixelSize(todo_item_font_px())
    return f


def apply_todo_item_font_setting():
    main_window = SiGlobal.siui.windows.get("MAIN_WINDOW")
    if main_window is not None and hasattr(main_window, "todo_list_panel"):
        main_window.todo_list_panel.refresh_todo_item_typography()


def lock_position(state):
    SiGlobal.todo_list.position_locked = state


def set_translucent_mode(state):
    SiGlobal.todo_list.settings_parser.modify("TRANSLUCENT_MODE", bool(state))
    main_window = SiGlobal.siui.windows.get("MAIN_WINDOW")
    if main_window is not None:
        main_window.applyWindowOpacity(enabled=bool(state))


def set_translucent_opacity(opacity_percent):
    percent = max(10, min(95, int(opacity_percent)))
    SiGlobal.todo_list.settings_parser.modify("TRANSLUCENT_OPACITY", percent)
    main_window = SiGlobal.siui.windows.get("MAIN_WINDOW")
    if main_window is not None:
        main_window.applyWindowOpacity()


# 主题颜色
def load_colors(is_dark=True):
    if is_dark is True:  # 深色主题
        # 加载图标
        SiGlobal.siui.icons.update(IconDictionary(color="#e1d9e8").icons)

        # 设置颜色
        SiGlobal.siui.colors["THEME"] = "#e1d9e8"
        SiGlobal.siui.colors["PANEL_THEME"] = "#0F85D3"
        SiGlobal.siui.colors["BACKGROUND_COLOR"] = "#252229"
        SiGlobal.siui.colors["BACKGROUND_DARK_COLOR"] = SiGlobal.siui.colors["INTERFACE_BG_A"]
        SiGlobal.siui.colors["BORDER_COLOR"] = "#3b373f"
        SiGlobal.siui.colors["TOOLTIP_BG"] = "ef413a47"
        SiGlobal.siui.colors["SVG_A"] = SiGlobal.siui.colors["THEME"]

        SiGlobal.siui.colors["THEME_TRANSITION_A"] = "#52389a"
        SiGlobal.siui.colors["THEME_TRANSITION_B"] = "#9c4e8b"

        SiGlobal.siui.colors["TEXT_A"] = "#FFFFFF"
        SiGlobal.siui.colors["TEXT_B"] = "#e1d9e8"
        SiGlobal.siui.colors["TEXT_C"] = Color.transparency(SiGlobal.siui.colors["THEME"], 0.75)
        SiGlobal.siui.colors["TEXT_D"] = Color.transparency(SiGlobal.siui.colors["THEME"], 0.6)
        SiGlobal.siui.colors["TEXT_E"] = Color.transparency(SiGlobal.siui.colors["THEME"], 0.5)

        SiGlobal.siui.colors["SWITCH_DEACTIVATE"] = "#D2D2D2"
        SiGlobal.siui.colors["SWITCH_ACTIVATE"] = "#100912"

        SiGlobal.siui.colors["BUTTON_HOVER"] = "#10FFFFFF"
        SiGlobal.siui.colors["BUTTON_FLASH"] = "#20FFFFFF"

        SiGlobal.siui.colors["SIMPLE_BUTTON_BG"] = Color.transparency(SiGlobal.siui.colors["THEME"], 0.1)

        SiGlobal.siui.colors["TOGGLE_BUTTON_OFF_BG"] = Color.transparency(SiGlobal.siui.colors["THEME"], 0)
        SiGlobal.siui.colors["TOGGLE_BUTTON_ON_BG"] = Color.transparency(SiGlobal.siui.colors["THEME"], 0.1)

    else:  # 亮色主题
        # 加载图标
        SiGlobal.siui.icons.update(IconDictionary(color="#0F85D3").icons)

        # 设置颜色
        SiGlobal.siui.colors["THEME"] = "#0F85D3"
        SiGlobal.siui.colors["PANEL_THEME"] = "#0F85D3"
        SiGlobal.siui.colors["BACKGROUND_COLOR"] = "#F3F3F3"
        SiGlobal.siui.colors["BACKGROUND_DARK_COLOR"] = "#e8e8e8"
        SiGlobal.siui.colors["BORDER_COLOR"] = "#d0d0d0"
        SiGlobal.siui.colors["TOOLTIP_BG"] = "#F3F3F3"
        SiGlobal.siui.colors["SVG_A"] = SiGlobal.siui.colors["THEME"]

        SiGlobal.siui.colors["THEME_TRANSITION_A"] = "#2abed8"
        SiGlobal.siui.colors["THEME_TRANSITION_B"] = "#2ad98e"

        SiGlobal.siui.colors["TEXT_A"] = "#1f1f2f"
        SiGlobal.siui.colors["TEXT_B"] = Color.transparency(SiGlobal.siui.colors["TEXT_A"], 0.85)
        SiGlobal.siui.colors["TEXT_C"] = Color.transparency(SiGlobal.siui.colors["TEXT_A"], 0.75)
        SiGlobal.siui.colors["TEXT_D"] = Color.transparency(SiGlobal.siui.colors["TEXT_A"], 0.6)
        SiGlobal.siui.colors["TEXT_E"] = Color.transparency(SiGlobal.siui.colors["TEXT_A"], 0.5)

        SiGlobal.siui.colors["SWITCH_DEACTIVATE"] = "#bec1c7"
        SiGlobal.siui.colors["SWITCH_ACTIVATE"] = "#F3F3F3"

        SiGlobal.siui.colors["BUTTON_HOVER"] = Color.transparency(SiGlobal.siui.colors["THEME"], 0.0625)
        SiGlobal.siui.colors["BUTTON_FLASH"] = Color.transparency(SiGlobal.siui.colors["THEME"], 0.43)

        SiGlobal.siui.colors["SIMPLE_BUTTON_BG"] = Color.transparency(SiGlobal.siui.colors["THEME"], 0.6)

        SiGlobal.siui.colors["TOGGLE_BUTTON_OFF_BG"] = Color.transparency(SiGlobal.siui.colors["THEME"], 0)
        SiGlobal.siui.colors["TOGGLE_BUTTON_ON_BG"] = Color.transparency(SiGlobal.siui.colors["THEME"], 0.1)

    SiGlobal.siui.reloadAllWindowsStyleSheet()


# 加载主题颜色
load_colors(is_dark=False)


def apply_popup_menu_appearance(menu):
    """与顶栏/设置项一致的圆角卡片风：托盘与侧栏右键菜单共用。"""
    menu_font = SiGlobal.siui.fonts.get("S_NORMAL", QApplication.font())
    menu.setFont(menu_font)
    sel_bg = Color.transparency(SiGlobal.siui.colors["PANEL_THEME"], 0.22)
    ta = SiGlobal.siui.colors["THEME_TRANSITION_A"]
    tb = SiGlobal.siui.colors["THEME_TRANSITION_B"]
    switch_off = SiGlobal.siui.colors["SWITCH_DEACTIVATE"]
    menu.setStyleSheet(
        """
        QMenu {{
            background-color: {bg};
            color: {text};
            border: 1px solid {border};
            border-radius: 8px;
            padding: 8px 0;
        }}
        QMenu::item {{
            padding: 8px 30px 8px 26px;
            margin: 2px 0;
            border-radius: 6px;
        }}
        QMenu::item:selected {{
            background-color: {sel};
            color: {text};
        }}
        QMenu::item:disabled {{
            color: {muted};
        }}
        QMenu::separator {{
            height: 1px;
            margin: 8px 10px;
            background: {border};
        }}
        QMenu::indicator {{
            width: 18px;
            height: 18px;
            margin-left: 10px;
            margin-right: 6px;
        }}
        QMenu::indicator:unchecked,
        QMenu::indicator:non-exclusive:unchecked {{
            border: 1px solid {switch_off};
            border-radius: 5px;
            background-color: {bg};
        }}
        QMenu::indicator:checked,
        QMenu::indicator:non-exclusive:checked {{
            border: none;
            border-radius: 5px;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {ta}, stop:1 {tb});
        }}
        """.format(
            bg=SiGlobal.siui.colors["BACKGROUND_DARK_COLOR"],
            text=SiGlobal.siui.colors["TEXT_B"],
            border=SiGlobal.siui.colors["BORDER_COLOR"],
            sel=sel_bg,
            muted=SiGlobal.siui.colors["TEXT_E"],
            ta=ta,
            tb=tb,
            switch_off=switch_off,
        )
    )


def theme_reminder_like_messagebox_stylesheet():
    theme = SiGlobal.siui.colors["PANEL_THEME"]
    bg = SiGlobal.siui.colors["BACKGROUND_COLOR"]
    bg_deep = SiGlobal.siui.colors["BACKGROUND_DARK_COLOR"]
    text = SiGlobal.siui.colors["TEXT_B"]
    border = SiGlobal.siui.colors["BORDER_COLOR"]
    hover = SiGlobal.siui.colors["BUTTON_HOVER"]
    return f"""
        QMessageBox {{
            background-color: {bg};
            color: {text};
        }}
        QMessageBox QLabel {{
            color: {text};
            font-size: 14px;
        }}
        QMessageBox QPushButton {{
            border: 1px solid {border};
            border-radius: 6px;
            padding: 8px 24px;
            background-color: {bg_deep};
            color: {text};
            font-size: 14px;
            min-width: 72px;
        }}
        QMessageBox QPushButton:hover {{
            background-color: {hover};
        }}
        QMessageBox QPushButton:default {{
            background-color: {theme};
            color: #ffffff;
            border: none;
        }}
    """


def show_theme_question(parent, title, text, default_no=True):
    mb = QMessageBox(parent)
    mb.setWindowTitle(title)
    mb.setIcon(QMessageBox.Question)
    mb.setText(text)
    mb.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    mb.setDefaultButton(QMessageBox.No if default_no else QMessageBox.Yes)
    mb.setWindowFlags(mb.windowFlags() & ~Qt.WindowContextHelpButtonHint)
    mb.setStyleSheet(theme_reminder_like_messagebox_stylesheet())
    return mb.exec_()


def show_theme_information(parent, title, text):
    mb = QMessageBox(parent)
    mb.setWindowTitle(title)
    mb.setIcon(QMessageBox.Information)
    mb.setText(text)
    mb.setStandardButtons(QMessageBox.Ok)
    mb.setWindowFlags(mb.windowFlags() & ~Qt.WindowContextHelpButtonHint)
    mb.setStyleSheet(theme_reminder_like_messagebox_stylesheet())
    mb.exec_()


class TodoEditDialog(QDialog):
    def __init__(self, parent=None, title="编辑待办", label_text="内容：", initial_text=""):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedWidth(360)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        theme = SiGlobal.siui.colors["PANEL_THEME"]
        bg = SiGlobal.siui.colors["BACKGROUND_COLOR"]
        bg_deep = SiGlobal.siui.colors["BACKGROUND_DARK_COLOR"]
        text = SiGlobal.siui.colors["TEXT_B"]
        border = SiGlobal.siui.colors["BORDER_COLOR"]

        self.setStyleSheet(f"""
            QDialog {{ background-color: {bg}; color: {text}; }}
            QLabel {{ color: {text}; font-size: 14px; }}
            QLineEdit {{
                border: 1px solid {border}; border-radius: 6px; padding: 6px 10px;
                background-color: {bg_deep}; color: {text}; font-size: 14px;
            }}
            QPushButton {{
                border: 1px solid {border}; border-radius: 6px; padding: 8px 24px;
                background-color: {bg_deep}; color: {text}; font-size: 14px;
            }}
            QPushButton:hover {{ background-color: {SiGlobal.siui.colors["BUTTON_HOVER"]}; }}
            QPushButton#btn_confirm {{ background-color: {theme}; color: #ffffff; border: none; }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        layout.addWidget(QLabel(label_text))
        self.edit = QLineEdit(self)
        self.edit.setText(initial_text)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_cancel = QPushButton("取消", self)
        btn_cancel.clicked.connect(self.reject)
        btn_ok = QPushButton("确定", self)
        btn_ok.setObjectName("btn_confirm")
        btn_ok.setDefault(True)
        btn_ok.clicked.connect(self.accept)
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_ok)
        layout.addWidget(self.edit)
        layout.addLayout(btn_layout)

    def showEvent(self, event):
        super().showEvent(event)
        self.edit.setFocus()
        self.edit.selectAll()

    def text(self):
        return self.edit.text()


def show_theme_text_input(parent, title, label, text=""):
    dlg = TodoEditDialog(parent, title=title, label_text=label, initial_text=text)
    if dlg.exec_() == QDialog.Accepted:
        return dlg.text(), True
    return "", False


def themed_icon_from_svg_key(icon_key, menu_left_pad=0):
    svg_data = SiGlobal.siui.icons.get(icon_key)
    if not svg_data:
        return QIcon()
    renderer = QSvgRenderer(QByteArray(svg_data))
    if not renderer.isValid():
        return QIcon()
    icon_w, icon_h = 16, 16
    pad = int(menu_left_pad)
    pixmap = QPixmap(QSize(icon_w + pad, icon_h))
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter, QRectF(float(pad), 0.0, float(icon_w), float(icon_h)))
    painter.end()
    return QIcon(pixmap)


class SingleSettingOption(SiDenseVContainer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setSpacing(2)

        self.title = SiLabel(self)
        self.title.setFont(SiGlobal.siui.fonts["S_BOLD"])
        self.title.setAutoAdjustSize(True)

        self.description = SiLabel(self)
        self.description.setFont(SiGlobal.siui.fonts["S_NORMAL"])
        self.description.setAutoAdjustSize(True)

        self.addWidget(self.title)
        self.addWidget(self.description)
        self.addPlaceholder(4)

    def setTitle(self, title: str, description: str):
        self.title.setText(title)
        self.description.setText(description)

    def reloadStyleSheet(self):
        super().reloadStyleSheet()

        self.title.setStyleSheet("color: {}".format(SiGlobal.siui.colors["TEXT_B"]))
        self.description.setStyleSheet("color: {}".format(SiGlobal.siui.colors["TEXT_D"]))


class SingleTODOOption(SiDenseHContainer):
    # 打勾框与右侧正文的间距（SiDenseHContainer.spacing，默认 16 偏大）
    TODO_ROW_SPACING = 6
    # SiCheckBox 内部：方框与内置占位文字的间距（默认 8）
    TODO_CHECKBOX_TEXT_GAP = 3
    # 有提醒图标时，给文本额外留出的安全右边距，避免贴到图标
    TODO_REMINDER_TEXT_RIGHT_PADDING = 10

    def __init__(self, todo_panel, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.todo_panel = todo_panel
        self.setShrinking(True)
        self.setSpacing(self.TODO_ROW_SPACING)
        self.setAlignCenter(True)

        # 鼠标拖动排序相关变量
        self._dragging = False
        self._drag_start_pos = None

        px = todo_item_font_px()
        self.check_box = SiCheckBox(
            self,
            indicator_size=px,
            text_gap=self.TODO_CHECKBOX_TEXT_GAP,
        )
        self.check_box.setText("")
        self.check_box.text_label.setFont(todo_item_font_qfont())
        cb_h = max(24, px + 14)
        self.check_box.resize(px, cb_h)
        self.check_box.toggled.connect(self._onChecked)

        self.text_label = SiLabel(self)
        self.text_label.setFont(todo_item_font_qfont())
        self.text_label.resize(500 - 48 - 48 - 32, 32)
        self.text_label.setWordWrap(True)
        self.text_label.setAutoAdjustSize(False)
        self.text_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.text_label.setFixedStyleSheet("padding-top: 0px; padding-bottom: 0px")

        self.clock_icon = SiSvgLabel(self)
        icon_size = max(14, px + 2)
        self.clock_icon.setSvgSize(icon_size, icon_size)
        self.clock_icon.resize(icon_size + 8, icon_size + 8)
        self.clock_icon.hide()

        self.addWidget(self.check_box)
        self.addWidget(self.text_label)
        self.addWidget(self.clock_icon, "right")

        self.reminder_data = None
        self.order_key = 0
        self.completed_rank = None
        
        self.move = self.moveTo

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._on_context_menu_requested)

        # 初始化时自动载入样式表
        self.reloadStyleSheet()

        self._inline_edit = None

    def apply_todo_typography(self):
        px = todo_item_font_px()
        f = todo_item_font_qfont()
        self.text_label.setFont(f)
        self.check_box.text_label.setFont(f)
        self.check_box.setIndicatorSize(px)
        cb_h = max(24, px + 14)
        self.check_box.resize(px, cb_h)
        
        icon_size = max(14, px + 2)
        self.clock_icon.setSvgSize(icon_size, icon_size)
        self.clock_icon.resize(icon_size + 8, icon_size + 8)

        self._relayout_text_and_height()

    def _relayout_text_and_height(self, total_width=None):
        if total_width is None:
            total_width = self.width()
        reserve = self.check_box.width() + self.spacing
        if not self.clock_icon.isHidden():
            reserve += self.clock_icon.width() + self.spacing + self.TODO_REMINDER_TEXT_RIGHT_PADDING
        text_width = max(1, int(total_width) - reserve)
        self.text_label.setFixedWidth(text_width)

        metrics = QFontMetrics(self.text_label.font())
        text = self.text_label.text() or ""
        text_rect = metrics.boundingRect(
            QRect(0, 0, text_width, 100000),
            int(Qt.TextWordWrap | Qt.AlignLeft | Qt.AlignTop),
            text,
        )
        text_height = max(metrics.height(), text_rect.height()) + 4
        self.text_label.setFixedHeight(text_height)

        if self._inline_edit is not None:
            self._inline_edit.setGeometry(self.text_label.geometry())
        self.adjustSize()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragging = False
            self._drag_start_pos = event.globalPos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton):
            super().mouseMoveEvent(event)
            return

        global_pos = event.globalPos()
        if not self._dragging:
            if self._drag_start_pos and (global_pos - self._drag_start_pos).manhattanLength() > 5:
                self._dragging = True
            else:
                super().mouseMoveEvent(event)
                return

        # 获取鼠标所在位置相对于容器的坐标
        local_pos = self.todo_panel.todo_content.mapFromGlobal(global_pos)
        todos = self.todo_panel._todoWidgets()
        if self not in todos:
            return

        current_idx = todos.index(self)
        target_idx = current_idx

        # 找到鼠标悬停在哪个元素的矩形中心上方/下方来决定替换位置
        for i, todo in enumerate(todos):
            if i == current_idx:
                continue
            rect = todo.geometry()
            # 扩展可判定的纵向区域，使得拖动更顺滑
            if rect.top() <= local_pos.y() <= rect.bottom():
                # 判断当前是向上还是向下拖动，以中线为界，防止反复横跳
                if current_idx > i and local_pos.y() < rect.center().y():
                    target_idx = i
                    break
                elif current_idx < i and local_pos.y() > rect.center().y():
                    target_idx = i
                    break

        if target_idx != current_idx:
            self.todo_panel._move_todo_in_list(self, target_idx)

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self._dragging:
                self._dragging = False
                self.todo_panel._syncCurrentListFromUI()
        super().mouseReleaseEvent(event)

    def reloadStyleSheet(self):
        super().reloadStyleSheet()

        self.setStyleSheet("background: transparent;")
        self.text_label.setFont(todo_item_font_qfont())
        self.check_box.text_label.setFont(todo_item_font_qfont())
        self._refresh_done_appearance()
        self.clock_icon.load('<?xml version="1.0" encoding="UTF-8"?><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M12,0C5.383,0,0,5.383,0,12s5.383,12,12,12,12-5.383,12-12S18.617,0,12,0Zm0,22c-5.514,0-10-4.486-10-10S6.486,2,12,2s10,4.486,10,10-4.486,10-10,10Zm5-10h-4V6c0-.552-.448-1-1-1s-1,.448-1,1v7c0,.552,.448,1,1,1h5c.552,0,1-.448,1-1s-.448-1-1-1Z" fill="{}" /></svg>'.format(SiGlobal.siui.colors["TEXT_C"]).encode())

    def _refresh_done_appearance(self):
        if self.check_box.isChecked():
            self.text_label.setStyleSheet(
                "color: {}; text-decoration: line-through; padding-top: 0px; padding-bottom: 0px".format(
                    SiGlobal.siui.colors["TEXT_D"]
                )
            )
        else:
            self.text_label.setStyleSheet(
                "color: {}; padding-top: 0px; padding-bottom: 0px".format(
                    SiGlobal.siui.colors["TEXT_B"]
                )
            )

    def _onChecked(self, state):
        self._refresh_done_appearance()
        if self.todo_panel is not None and self.todo_panel.current_list_name:
            self.todo_panel._handleTodoCheckedStateChanged(self)

    def _on_context_menu_requested(self, pos):
        if self.todo_panel is not None:
            self.todo_panel._show_todo_context_menu(self, pos)

    def setText(self, text: str):
        self.text_label.setText(text)
        self._relayout_text_and_height()

    def setOrderData(self, order_key, completed_rank=None):
        try:
            self.order_key = int(order_key)
        except (TypeError, ValueError):
            self.order_key = 0
        if completed_rank is None:
            self.completed_rank = None
        else:
            try:
                self.completed_rank = int(completed_rank)
            except (TypeError, ValueError):
                self.completed_rank = None

    def setDone(self, done: bool):
        self.check_box.blockSignals(True)
        self.check_box.setChecked(done)
        self.check_box.blockSignals(False)
        self._refresh_done_appearance()

    def setReminder(self, reminder_data):
        self.reminder_data = reminder_data
        self._popup_shown = False
        if reminder_data:
            self.clock_icon.show()
            t = datetime.fromtimestamp(reminder_data.get("timestamp", 0))
            self.clock_icon.setHint("提醒时间: " + t.strftime("%Y-%m-%d %H:%M"))
        else:
            self.clock_icon.hide()
        self._relayout_text_and_height()

    def adjustSize(self):
        heights = [self.text_label.height(), self.check_box.height()]
        if not self.clock_icon.isHidden():
            heights.append(self.clock_icon.height())
        self.setFixedHeight(max(heights))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._relayout_text_and_height(event.size().width())

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton and not self._dragging:
            self._startInlineEdit()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    def _startInlineEdit(self):
        if self._inline_edit is not None:
            return
        current_text = self.text_label.text()
        self._inline_edit = QLineEdit(self)
        self._inline_edit.setText(current_text)
        self._inline_edit.setFont(self.text_label.font())
        self._inline_edit.setGeometry(self.text_label.geometry())
        self._inline_edit.setStyleSheet(
            "border: 1px solid {}; background-color: {}; color: {}; "
            "border-radius: 4px; padding: 1px 4px;".format(
                SiGlobal.siui.colors["BORDER_COLOR"],
                SiGlobal.siui.colors["BACKGROUND_DARK_COLOR"],
                SiGlobal.siui.colors["TEXT_B"],
            )
        )
        self.text_label.hide()
        self._inline_edit.show()
        self._inline_edit.setFocus()
        self._inline_edit.selectAll()
        self._inline_edit.returnPressed.connect(self._finishInlineEdit)
        self._inline_edit.installEventFilter(self)

    def _finishInlineEdit(self):
        if self._inline_edit is None:
            return
        new_text = self._inline_edit.text().strip()
        if new_text:
            self.text_label.setText(new_text)
        self.text_label.show()
        self._inline_edit.removeEventFilter(self)
        self._inline_edit.deleteLater()
        self._inline_edit = None
        self.text_label.adjustSize()
        self.adjustSize()
        if self.todo_panel:
            self.todo_panel._syncCurrentListFromUI()
            self.todo_panel.adjustSize()

    def _cancelInlineEdit(self):
        if self._inline_edit is None:
            return
        self.text_label.show()
        self._inline_edit.removeEventFilter(self)
        self._inline_edit.deleteLater()
        self._inline_edit = None

    def eventFilter(self, obj, event):
        if obj is self._inline_edit:
            if event.type() == QEvent.FocusOut:
                self._finishInlineEdit()
                return True
            if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Escape:
                self._cancelInlineEdit()
                return True
        return super().eventFilter(obj, event)


class AppHeaderPanel(SiLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.background_label = SiLabel(self)
        self.background_label.setFixedStyleSheet("border-radius: 8px")

        self.container_h = SiDenseHContainer(self)
        self.container_h.setAlignCenter(True)
        self.container_h.setFixedHeight(48)
        self.container_h.setSpacing(0)

        self.icon = SiSvgLabel(self)
        self.icon.resize(32, 32)
        self.icon.setSvgSize(16, 16)

        self.unfold_button = SiToggleButton(self)
        self.unfold_button.setFixedHeight(32)
        self.unfold_button.attachment().setText("0个待办事项")
        self.unfold_button.setChecked(True)

        self.calendar_button = SiSimpleButton(self)
        self.calendar_button.resize(32, 32)
        self.calendar_button.setHint("日历")

        self.settings_button = SiToggleButton(self)
        self.settings_button.resize(32, 32)
        self.settings_button.setHint("设置")
        self.settings_button.setChecked(False)

        self.container_h.addPlaceholder(16)
        self.container_h.addWidget(self.icon)
        self.container_h.addPlaceholder(4)
        self.container_h.addWidget(self.unfold_button)

        self.container_h.addPlaceholder(16, "right")
        self.container_h.addWidget(self.settings_button, "right")
        self.container_h.addPlaceholder(8, "right")
        self.container_h.addWidget(self.calendar_button, "right")

        # 按钮加入全局变量
        SiGlobal.todo_list.todo_list_unfold_button = self.unfold_button
        SiGlobal.todo_list.settings_unfold_button = self.settings_button
        SiGlobal.todo_list.calendar_unfold_button = self.calendar_button

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.background_label.resize(event.size().width(), 48)
        self.container_h.resize(event.size().width(), 48)

    def reloadStyleSheet(self):
        super().reloadStyleSheet()
        # 按钮颜色
        self.unfold_button.setStateColor(SiGlobal.siui.colors["TOGGLE_BUTTON_OFF_BG"],
                                         SiGlobal.siui.colors["TOGGLE_BUTTON_ON_BG"])
        self.settings_button.setStateColor(SiGlobal.siui.colors["TOGGLE_BUTTON_OFF_BG"],
                                           SiGlobal.siui.colors["TOGGLE_BUTTON_ON_BG"])

        # svg 图标
        self.settings_button.attachment().load(SiGlobal.siui.icons["fi-rr-menu-burger"])
        self.calendar_button.attachment().load(SiGlobal.siui.icons.get("fi-rr-calendar", SiGlobal.siui.icons["fi-rr-menu-burger"]))
        self.icon.load('<?xml version="1.0" encoding="UTF-8"?><svg xmlns="http://www.w3.org/2000/svg" id="Layer_1" '
                       'data-name="Layer 1" viewBox="0 0 24 24" width="512" height="512"><path d="M0,8v-1C0,4.243,'
                       '2.243,2,5,2h1V1c0-.552,.447-1,1-1s1,.448,1,1v1h8V1c0-.552,.447-1,1-1s1,.448,1,1v1h1c2.757,0,'
                       '5,2.243,5,5v1H0Zm24,2v9c0,2.757-2.243,5-5,5H5c-2.757,0-5-2.243-5-5V10H24Zm-6.168,'
                       '3.152c-.384-.397-1.016-.409-1.414-.026l-4.754,4.582c-.376,.376-1.007,'
                       '.404-1.439-.026l-2.278-2.117c-.403-.375-1.035-.354-1.413,.052-.376,.404-.353,1.037,.052,'
                       '1.413l2.252,2.092c.566,.567,1.32,.879,2.121,.879s1.556-.312,2.108-.866l4.74-4.568c.397-.383,'
                       '.409-1.017,.025-1.414Z" fill="{}" /></svg>'.format(SiGlobal.siui.colors["SVG_A"]).encode())

        self.background_label.setStyleSheet("""background-color: {}; border: 1px solid {}""".format(
            SiGlobal.siui.colors["BACKGROUND_COLOR"], SiGlobal.siui.colors["BORDER_COLOR"]))
        self.unfold_button.setStyleSheet("color: {}".format(SiGlobal.siui.colors["TEXT_B"]))


class TODOListPanel(ThemedOptionCardPlane):
    todoAmountChanged = pyqtSignal(int)

    # 侧栏条目：字号与行高（原 8px / 12px，按比例放大）
    SIDEBAR_FONT_PX = 10
    SIDEBAR_ROW_HEIGHT = (12 * SIDEBAR_FONT_PX + 7) // 8  # 15
    # 悬停时宽度增加、布局右对齐，左侧「伸出」；右侧与卡片接缝不变
    SIDEBAR_HOVER_SHIFT = 8
    # 按钮宽度 = 文字测量宽 + 此项；亦为省略号可用宽度 = bw - 此项（原 10，略收紧）
    SIDEBAR_TEXT_H_PADDING = 6
    SIDEBAR_PLUS_LABEL = "+ "

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTitle("")
        self.setSpacing(16)
        self.setUseSignals(True)
        self.todo_lists = {}
        self.current_list_name = ""
        self.list_buttons = {}
        self.sidebar_host = self

        self.body().setUseMoveTo(False)
        self.body().setShrinking(True)
        self.body().setAdjustWidgetsSize(True)
        self.body().setSpacing(0)

        self.list_sidebar = SiDenseVContainer(self)
        self.list_sidebar.setShrinking(True)
        self.list_sidebar.setAdjustWidgetsSize(True)
        self.list_sidebar.setSpacing(2)

        self.list_items_container = QWidget(self.list_sidebar)
        self._list_buttons_layout = QVBoxLayout(self.list_items_container)
        self._list_buttons_layout.setContentsMargins(0, 0, 0, 0)
        self._list_buttons_layout.setSpacing(2)
        self._list_buttons_layout.setAlignment(Qt.AlignTop)

        # 「新建」与清单按钮放在同一 QVBoxLayout 内；若作为 SiDenseVContainer
        # 第二个子控件，易被高度/裁剪算错而只显示清单、不显示「新建」
        self.new_list_button = SiSimpleButton(self.list_items_container)
        self.new_list_button.setFixedHeight(self.SIDEBAR_ROW_HEIGHT)
        self.new_list_button.attachment().setText(self.SIDEBAR_PLUS_LABEL)
        self.new_list_button.setHint("新建清单")
        self.new_list_button.clicked.connect(self._onCreateListClicked)

        self.list_sidebar.addWidget(self.list_items_container)
        self._new_list_row = self._make_sidebar_row(self.new_list_button)
        self._list_buttons_layout.addWidget(self._new_list_row)

        self._apply_sidebar_si_icon_label(self.new_list_button.attachment())
        self.new_list_button.attachment().text_label.setFont(self._sidebar_font_plus_bold())
        nw = self._width_for_sidebar_plus()
        self.new_list_button._sidebar_rest_width = nw
        self.new_list_button.setFixedSize(nw, self.SIDEBAR_ROW_HEIGHT)
        self.new_list_button.attachment().resize(nw, self.SIDEBAR_ROW_HEIGHT)
        self._sidebar_sync_attachment_right(self.new_list_button)
        self.new_list_button.installEventFilter(self)

        self.todo_scroll_area = QScrollArea(self.body())
        self.todo_scroll_area.setWidgetResizable(False)
        self.todo_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.todo_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.todo_scroll_area.setFrameShape(QScrollArea.NoFrame)
        self.todo_scroll_area.setStyleSheet("background: transparent; border: none;")
        self.todo_scroll_area.viewport().setAutoFillBackground(False)

        self.todo_content = SiDenseVContainer()
        self.todo_content.setShrinking(True)
        self.todo_content.setAdjustWidgetsSize(True)
        self.todo_content.setSpacing(6)
        self.todo_scroll_area.setWidget(self.todo_content)
        self.body().addWidget(self.todo_scroll_area)

        # 底部拖动调整高度
        self._user_body_height = None
        self._resizing_bottom = False
        self._resizing_right = False
        self._resizing_corner = False
        self._resize_start_y = 0
        self._resize_start_x = 0
        self._resize_start_height = 0
        self._resize_start_window_width = 0
        self._resize_handle = QWidget(self)
        self._resize_handle.setCursor(Qt.SizeVerCursor)
        self._resize_handle.setMouseTracking(True)
        self._resize_handle.setStyleSheet("background: transparent;")
        self._resize_handle.installEventFilter(self)
        self._right_resize_handle = QWidget(self)
        self._right_resize_handle.setCursor(Qt.SizeHorCursor)
        self._right_resize_handle.setMouseTracking(True)
        self._right_resize_handle.setStyleSheet("background: transparent;")
        self._right_resize_handle.installEventFilter(self)
        self._corner_resize_handle = QWidget(self)
        self._corner_resize_handle.setCursor(Qt.SizeFDiagCursor)
        self._corner_resize_handle.setMouseTracking(True)
        self._corner_resize_handle.setStyleSheet("background: transparent;")
        self._corner_resize_handle.installEventFilter(self)

        self.no_todo_placeholder = SiLabel(self.todo_content)
        self.no_todo_placeholder.setVisible(False)
        self.no_todo_placeholder.setFixedHeight(0)

        self.no_todo_label = SiLabel(self.no_todo_placeholder)
        self.no_todo_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.no_todo_label.setAutoAdjustSize(True)
        self.no_todo_label.setText("当前没有待办哦")
        self.no_todo_label.setAlignment(Qt.AlignCenter)
        self.no_todo_label.hide()

        self.add_todo_button = SiSimpleButton(self)
        self.add_todo_button.resize(32, 32)
        self.add_todo_button.setHint("添加新待办")
        self.add_todo_button.clicked.connect(self._onInlineAddButtonClicked)
        self.header().addWidget(self.add_todo_button, "right")

        self.inline_add_container = SiDenseVContainer(self.todo_content)
        self.inline_add_container.setShrinking(True)
        self.inline_add_container.setAdjustWidgetsSize(True)
        self.inline_add_container.setSpacing(6)

        self.inline_add_text_edit = QTextEdit(self.inline_add_container)
        self.inline_add_text_edit.setFixedHeight(70)
        self.inline_add_text_edit.setFont(todo_item_font_qfont())
        self.inline_add_text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.inline_add_text_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.inline_add_text_edit.lineWrapMode()

        self.inline_add_actions = SiDenseHContainer(self.inline_add_container)
        self.inline_add_actions.setAlignCenter(True)
        self.inline_add_actions.setFixedHeight(36)
        self.inline_add_actions.setSpacing(8)

        self.inline_add_confirm_button = SiSimpleButton(self.inline_add_container)
        self.inline_add_confirm_button.resize(32, 32)
        self.inline_add_confirm_button.setHint("确认并添加")
        self.inline_add_confirm_button.clicked.connect(self._onInlineAddConfirmButtonClicked)

        self.inline_add_cancel_button = SiSimpleButton(self.inline_add_container)
        self.inline_add_cancel_button.resize(32, 32)
        self.inline_add_cancel_button.setHint("取消")
        self.inline_add_cancel_button.clicked.connect(self._onInlineAddCancelButtonClicked)

        self.inline_add_actions.addPlaceholder(1)
        self.inline_add_actions.addWidget(self.inline_add_cancel_button, "right")
        self.inline_add_actions.addWidget(self.inline_add_confirm_button, "right")

        self.inline_add_container.addWidget(self.inline_add_text_edit)
        self.inline_add_container.addWidget(self.inline_add_actions)
        self.todo_content.addWidget(self.inline_add_container, index=0)
        self.todo_content.addWidget(self.no_todo_placeholder, index=1)
        self._setInlineAddVisible(False)

        self.footer().setFixedHeight(64)
        self.footer().setSpacing(8)
        self.footer().setAlignCenter(True)

        self.complete_all_button = SiSimpleButton(self)
        self.complete_all_button.resize(32, 32)
        self.complete_all_button.setHint("全部完成")
        self.complete_all_button.clicked.connect(self._onCompleteAllButtonClicked)

        self.footer().addWidget(self.complete_all_button, "right")

        # 全局方法
        SiGlobal.todo_list.addTODO = self.addTODO
        self.loadLists({})

    def updateTODOAmount(self):
        todo_amount = len(self._todoWidgets())
        self.todoAmountChanged.emit(todo_amount)

        if todo_amount == 0:
            self.no_todo_placeholder.setFixedHeight(150)
            self.no_todo_placeholder.show()
            self.no_todo_label.show()
        else:
            self.no_todo_label.hide()
            self.no_todo_placeholder.setFixedHeight(0)
            self.no_todo_placeholder.hide()

        self._updateNoTodoLabelGeometry()
        self.adjustSize()

    def reloadStyleSheet(self):
        self.setThemeColor(SiGlobal.siui.colors["PANEL_THEME"])
        super().reloadStyleSheet()

        self._apply_sidebar_text_color_styles()
        for button in self.list_buttons.values():
            self._apply_sidebar_si_icon_label(button.attachment())
        self._apply_sidebar_si_icon_label(self.new_list_button.attachment())
        self.new_list_button.attachment().text_label.setFont(self._sidebar_font_plus_bold())
        for button in self.list_buttons.values():
            self._sidebar_sync_attachment_right(button)
        self._sidebar_sync_attachment_right(self.new_list_button)
        self.no_todo_label.setStyleSheet("color: {}".format(SiGlobal.siui.colors["TEXT_E"]))
        self.add_todo_button.attachment().load(SiGlobal.siui.icons["fi-rr-apps-add"])
        self.complete_all_button.attachment().load(SiGlobal.siui.icons["fi-rr-list-check"])
        self.inline_add_confirm_button.attachment().load(SiGlobal.siui.icons["fi-rr-check"])
        self.inline_add_cancel_button.attachment().load(SiGlobal.siui.icons["fi-rr-cross"])
        self.inline_add_text_edit.setFont(todo_item_font_qfont())
        self.inline_add_text_edit.setStyleSheet(
            """
            border: 1px solid {};
            background-color: {};
            border-radius: 4px;
            padding-left: 8px; padding-right: 2px;
            color: {}
            """.format(
                SiGlobal.siui.colors["BORDER_COLOR"],
                SiGlobal.siui.colors["BACKGROUND_DARK_COLOR"],
                SiGlobal.siui.colors["TEXT_B"],
            )
        )
        self.todo_content.setStyleSheet("background: transparent;")
        self.todo_scroll_area.viewport().setStyleSheet("background: transparent; border: none;")
        self.todo_scroll_area.setStyleSheet(
            """
            QScrollArea {{
                background: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: 8px;
                margin: 2px 0 2px 0;
            }}
            QScrollBar::handle:vertical {{
                background: {};
                border-radius: 4px;
                min-height: 28px;
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical,
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {{
                background: transparent;
                height: 0px;
            }}
            """.format(Color.transparency(SiGlobal.siui.colors["TEXT_D"], 0.7))
        )

    def _onCompleteAllButtonClicked(self):
        for obj in self._todoWidgets():
            obj.check_box.setChecked(True)

    def refresh_todo_item_typography(self):
        self.inline_add_text_edit.setFont(todo_item_font_qfont())
        for w in self._todoWidgets():
            w.apply_todo_typography()
        self.adjustSize()

    def _sync_todo_scroll_area(self):
        for _ in range(2):
            viewport_width = max(1, self.todo_scroll_area.viewport().width())
            if self.todo_content.width() != viewport_width:
                self.todo_content.setFixedWidth(viewport_width)
            self.todo_content.adjustSize()

    def _target_body_height(self):
        natural_height = max(20, self.todo_content.height())
        user_body_height = getattr(self, "_user_body_height", None)
        if user_body_height is not None:
            return max(20, user_body_height)
        return natural_height

    def _setInlineAddVisible(self, visible):
        if visible:
            self.inline_add_container.show()
            required_height = (
                self.inline_add_text_edit.height()
                + self.inline_add_actions.height()
                + self.inline_add_container.spacing
                + 8
            )
            self.inline_add_container.setFixedHeight(required_height)
            self.inline_add_text_edit.setFocus()
        else:
            self.inline_add_text_edit.setText("")
            self.inline_add_container.setFixedHeight(0)
            self.inline_add_container.hide()
        self._updateNoTodoLabelGeometry()
        self.adjustSize()

    def _onInlineAddButtonClicked(self):
        self._setInlineAddVisible(not self.inline_add_container.isVisible())

    def _onInlineAddConfirmButtonClicked(self):
        text = self.inline_add_text_edit.toPlainText()
        while text[-1:] == "\n":
            text = text[:-1]

        if text == "":
            return

        self.addTODO(text)
        self._setInlineAddVisible(False)

    def _onInlineAddCancelButtonClicked(self):
        self._setInlineAddVisible(False)

    def _addTODOWidget(self, text, done=False, reminder=None, order_key=0, completed_rank=None):
        new_todo = SingleTODOOption(self, self.todo_content)
        self.todo_content.addWidget(new_todo)
        new_todo.setText(text)
        new_todo.setOrderData(order_key, completed_rank)
        new_todo.setDone(done)
        new_todo.setReminder(reminder)
        new_todo.show()
        new_todo.adjustSize()
        return new_todo

    def addTODO(self, text):
        new_todo = self._addTODOWidget(text, order_key=self._next_order_key())
        self._reposition_todo_by_rule(new_todo)
        self._syncCurrentListFromUI()
        self.adjustSize()
        self.updateTODOAmount()

    def _todoWidgets(self):
        return [widget for widget in self.todo_content.widgets_top if isinstance(widget, SingleTODOOption)]

    def _syncCurrentListFromUI(self, save_to_disk=True):
        if self.current_list_name == "":
            return
        self.todo_lists[self.current_list_name] = [
            {
                "text": widget.text_label.text(),
                "done": widget.check_box.isChecked(),
                "reminder": getattr(widget, "reminder_data", None),
                "order_key": getattr(widget, "order_key", 0),
                "completed_rank": getattr(widget, "completed_rank", None),
            }
            for widget in self._todoWidgets()
        ]
        if save_to_disk:
            self._save_lists_to_disk()

    def _save_lists_to_disk(self):
        todo_lists_copy = {list_name: list(todos) for list_name, todos in self.todo_lists.items()}
        SiGlobal.todo_list.todos_parser.lists = todo_lists_copy
        SiGlobal.todo_list.todos_parser.todos = list(next(iter(todo_lists_copy.values()))) if todo_lists_copy else []
        SiGlobal.todo_list.todos_parser.write()

    def _clearTodosInUI(self):
        for widget in list(self._todoWidgets()):
            self.todo_content.removeWidget(widget)
            widget.close()

    def _next_order_key(self):
        orders = []
        for todo in self.todo_lists.get(self.current_list_name, []):
            if isinstance(todo, dict):
                order_key = todo.get("order_key", None)
                if isinstance(order_key, (int, float)):
                    orders.append(int(order_key))
        for widget in self._todoWidgets():
            order_key = getattr(widget, "order_key", None)
            if isinstance(order_key, (int, float)):
                orders.append(int(order_key))
        return max(orders, default=0) + 1

    def _next_completed_rank(self):
        ranks = []
        for todo in self.todo_lists.get(self.current_list_name, []):
            if isinstance(todo, dict):
                completed_rank = todo.get("completed_rank", None)
                if isinstance(completed_rank, (int, float)):
                    ranks.append(int(completed_rank))
        for widget in self._todoWidgets():
            completed_rank = getattr(widget, "completed_rank", None)
            if isinstance(completed_rank, (int, float)):
                ranks.append(int(completed_rank))
        return max(ranks, default=0) + 1

    def _reposition_todo_by_rule(self, widget):
        todos = self._todoWidgets()
        if widget not in todos:
            return False

        other_todos = [todo for todo in todos if todo is not widget]
        if widget.check_box.isChecked():
            current_completed_rank = getattr(widget, "completed_rank", 0) or 0
            target_idx = (
                sum(1 for todo in other_todos if not todo.check_box.isChecked())
                + sum(
                    1
                    for todo in other_todos
                    if todo.check_box.isChecked() and (getattr(todo, "completed_rank", 0) or 0) > current_completed_rank
                )
            )
        else:
            current_order_key = getattr(widget, "order_key", 0)
            target_idx = sum(
                1
                for todo in other_todos
                if not todo.check_box.isChecked() and getattr(todo, "order_key", 0) > current_order_key
            )

        return self._reinsert_todo_widget(widget, target_idx)

    def _handleTodoCheckedStateChanged(self, widget):
        if widget not in self._todoWidgets():
            return
        if widget.check_box.isChecked():
            widget.completed_rank = self._next_completed_rank()
        else:
            widget.completed_rank = None
        self._reposition_todo_by_rule(widget)
        self._refresh_completed_ranks_from_ui()
        self._syncCurrentListFromUI()
        self.adjustSize()
        self.updateTODOAmount()

    def _refresh_completed_ranks_from_ui(self):
        checked_widgets = [widget for widget in self._todoWidgets() if widget.check_box.isChecked()]
        next_rank = len(checked_widgets)
        for widget in self._todoWidgets():
            if widget.check_box.isChecked():
                widget.completed_rank = next_rank
                next_rank -= 1
            else:
                widget.completed_rank = None

    def _refresh_order_keys_from_ui(self):
        todos = self._todoWidgets()
        next_order = len(todos)
        for widget in todos:
            widget.order_key = next_order
            next_order -= 1

    def _refreshListButtonsState(self):
        for list_name, button in self.list_buttons.items():
            is_current = list_name == self.current_list_name
            button.setChecked(is_current)
            self._apply_sidebar_button_theme(button, is_current)

    def _make_sidebar_row(self, inner_widget):
        """横向 stretch + 按钮，宽度变化时从左侧伸出，右缘始终贴齐容器（与卡片接缝）。"""
        row = QWidget(self.list_items_container)
        row.setStyleSheet("background: transparent;")
        hl = QHBoxLayout(row)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(0)
        hl.addStretch(1)
        hl.addWidget(inner_widget, 0, Qt.AlignRight | Qt.AlignVCenter)
        return row

    def _sidebar_sync_attachment_right(self, btn):
        """
        让文字跟随背景一起向左弹出：
        使 attachment 的宽度保持为 rest_width，并且始终贴齐按钮的左缘 (x=0)。
        这样当按钮变宽（向左延展）时，文字会同步向左移动。
        """
        w0 = btn.width()
        h0 = btn.height()
        att = btn.attachment()
        
        rw = getattr(btn, "_sidebar_rest_width", w0)
        
        att.resize(rw, h0)
        aw = att.width()
        
        shift_x = -((w0 - aw) // 2)
        btn.setAttachmentShifting(shift_x, 0)
        
        sh = btn.attachment_shifting
        y = (h0 - att.height()) // 2 + int(sh[1])
        att.move(0, y)

    def _clear_list_buttons_layout(self):
        layout = self._list_buttons_layout
        to_remove = []
        for i in range(layout.count()):
            item = layout.itemAt(i)
            w = item.widget()
            if w is not None and w is not self._new_list_row:
                to_remove.append(w)
        for w in to_remove:
            layout.removeWidget(w)
            w.setParent(None)
            w.deleteLater()

    def _rebuildListButtons(self):
        # 重建期间不刷新绘制，避免 deleteLater 与连续两次 adjustSize 之间出现「全挤在一起」的中间态
        self.list_sidebar.setUpdatesEnabled(False)
        self.list_items_container.setUpdatesEnabled(False)
        try:
            self._list_buttons_layout.removeWidget(self._new_list_row)
            self._clear_list_buttons_layout()
            self.list_buttons = {}

            for list_name in self.todo_lists.keys():
                button = SiToggleButton(self.list_items_container)
                bw = self._width_for_sidebar_text(list_name)
                button._sidebar_rest_width = bw
                button.setFixedSize(bw, self.SIDEBAR_ROW_HEIGHT)
                
                fm = QFontMetrics(self._sidebar_font())
                pad = TODOListPanel.SIDEBAR_TEXT_H_PADDING
                elided_name = fm.elidedText(list_name, Qt.ElideRight, bw - pad)
                button.attachment().setText(elided_name)
                
                button.setHint(list_name)
                self._apply_sidebar_si_icon_label(button.attachment())
                button.attachment().resize(bw, self.SIDEBAR_ROW_HEIGHT)
                button.clicked.connect(lambda _, name=list_name: self._onListButtonClicked(name))
                button.setContextMenuPolicy(Qt.CustomContextMenu)
                button.customContextMenuRequested.connect(
                    lambda pos, name=list_name, b=button: self._show_list_context_menu(name, b, pos)
                )
                button.installEventFilter(self)
                self._sidebar_sync_attachment_right(button)
                self._list_buttons_layout.addWidget(self._make_sidebar_row(button))
                self.list_buttons[list_name] = button

            self._list_buttons_layout.addWidget(self._new_list_row)

            self._refreshListButtonsState()
            self._apply_sidebar_text_color_styles()
        finally:
            self.list_items_container.setUpdatesEnabled(True)
            self.list_sidebar.setUpdatesEnabled(True)

        # 让待删除控件尽快从事件队列清掉，减轻下一帧布局抖动
        QApplication.processEvents(QEventLoop.ExcludeUserInputEvents)

        # 宽度与侧栏位置只由随后的 adjustSize（如 _setCurrentList）统一算一次，避免与 _rebuild 末尾重复排板

    def _apply_sidebar_text_color_styles(self):
        # 统一由按钮状态控制侧栏条目的背景与文字颜色
        self._apply_sidebar_button_theme(self.new_list_button, False, is_new_button=True)
        for button in self.list_buttons.values():
            self._apply_sidebar_button_theme(button)

    def _apply_sidebar_button_theme(self, button, is_checked=None, is_new_button=False):
        if is_checked is None:
            is_checked = bool(button.isChecked())

        if is_new_button:
            button.setStateColor("#00FFFFFF", "#00FFFFFF")
            text_color = SiGlobal.siui.colors["TEXT_B"]
        else:
            sidebar_selected_bg = Color.transparency(
                SiGlobal.siui.colors["THEME_TRANSITION_A"],
                0.38,
            )
            button.setStateColor(
                "#00FFFFFF",
                sidebar_selected_bg,
            )
            text_color = "#FFFFFF" if is_checked else SiGlobal.siui.colors["TEXT_B"]

        button.attachment().setStyleSheet(f"color: {text_color};")

    def _setCurrentList(self, list_name, sync_before_switch=True, save_to_disk=True):
        if list_name not in self.todo_lists:
            return

        if sync_before_switch:
            self._syncCurrentListFromUI(save_to_disk=False)

        self.current_list_name = list_name
        self._clearTodosInUI()
        self._setInlineAddVisible(False)
        for todo in self.todo_lists.get(list_name, []):
            if isinstance(todo, dict):
                text = str(todo.get("text", ""))
                done = bool(todo.get("done", False))
                reminder = todo.get("reminder", None)
                order_key = int(todo.get("order_key", 0))
                completed_rank = todo.get("completed_rank", None)
            else:
                text = str(todo)
                done = False
                reminder = None
                order_key = 0
                completed_rank = None
            self._addTODOWidget(text, done, reminder, order_key, completed_rank)

        self._refreshListButtonsState()
        self._update_panel_title()
        self.adjustSize()
        self.updateTODOAmount()
        if save_to_disk:
            self._save_lists_to_disk()

    def _update_panel_title(self):
        name = (self.current_list_name or "").strip()
        if name and name in self.todo_lists:
            self.setTitle(name)
        elif self.todo_lists:
            self.setTitle(next(iter(self.todo_lists.keys())))
        else:
            self.setTitle("")

    def _onListButtonClicked(self, list_name):
        self._setCurrentList(list_name)

    @staticmethod
    def _menu_icon_from_svg_key(icon_key):
        return themed_icon_from_svg_key(icon_key, menu_left_pad=8)

    def _show_list_context_menu(self, list_name, button, pos):
        if list_name not in self.todo_lists:
            return

        keys = list(self.todo_lists.keys())
        idx = keys.index(list_name)
        last_i = len(keys) - 1

        menu = QMenu(self)
        apply_popup_menu_appearance(menu)

        act_edit = QAction(self._menu_icon_from_svg_key("fi-rr-edit"), "编辑分类", self)
        act_edit.triggered.connect(lambda: self._rename_list_from_context(list_name))
        menu.addAction(act_edit)

        act_clear = QAction(self._menu_icon_from_svg_key("fi-rr-trash"), "清除内容", self)
        act_clear.triggered.connect(lambda: self._clear_list_contents(list_name))
        menu.addAction(act_clear)

        act_delete = QAction(self._menu_icon_from_svg_key("fi-rr-cross"), "删除分类", self)
        act_delete.triggered.connect(lambda: self._delete_list_from_context(list_name))
        menu.addAction(act_delete)

        menu.addSeparator()

        act_top = QAction(self._menu_icon_from_svg_key("fi-rr-angle-up"), "分类置顶", self)
        act_top.setEnabled(idx > 0)
        act_top.triggered.connect(lambda: self._move_list_to_edge(list_name, to_top=True))
        menu.addAction(act_top)

        act_up = QAction(self._menu_icon_from_svg_key("fi-rr-angle-up"), "分类上移", self)
        act_up.setEnabled(idx > 0)
        act_up.triggered.connect(lambda: self._move_list_by_delta(list_name, -1))
        menu.addAction(act_up)

        act_down = QAction(self._menu_icon_from_svg_key("fi-rr-angle-down"), "分类下移", self)
        act_down.setEnabled(idx < last_i)
        act_down.triggered.connect(lambda: self._move_list_by_delta(list_name, 1))
        menu.addAction(act_down)

        act_bottom = QAction(self._menu_icon_from_svg_key("fi-rr-angle-down"), "分类置底", self)
        act_bottom.setEnabled(idx < last_i)
        act_bottom.triggered.connect(lambda: self._move_list_to_edge(list_name, to_top=False))
        menu.addAction(act_bottom)

        menu.exec_(button.mapToGlobal(pos))

    def _edit_todo_from_context(self, widget):
        if widget not in self._todoWidgets():
            return
        current = widget.text_label.text()
        new_text, ok = show_theme_text_input(self.window(), "编辑待办", "内容：", current)
        if not ok:
            return
        new_text = new_text.strip()
        while new_text[-1:] == "\n":
            new_text = new_text[:-1]
        if new_text == "":
            return
        widget.setText(new_text)
        widget.adjustSize()
        self.adjustSize()
        self._syncCurrentListFromUI()

    def _remove_todo_widget(self, widget):
        if widget not in self._todoWidgets():
            return
        self.todo_content.removeWidget(widget)
        widget.close()
        self._syncCurrentListFromUI()
        self.adjustSize()
        self.updateTODOAmount()

    def _remove_reminder_from_context(self, widget):
        if widget not in self._todoWidgets():
            return
        widget.setReminder(None)
        self._syncCurrentListFromUI()
        self.adjustSize()

    def _set_reminder_from_context(self, widget):
        if widget not in self._todoWidgets():
            return
        dlg = ReminderDialog(self.window(), getattr(widget, "reminder_data", None))
        if dlg.exec_() == QDialog.Accepted:
            reminder_data = dlg.get_reminder_data()
            widget.setReminder(reminder_data)
            self._syncCurrentListFromUI()
            self.adjustSize()

    def _move_todo_in_list(self, widget, new_list_index):
        todos = self._todoWidgets()
        if widget not in todos:
            return
        new_list_index = self._clamp_todo_target_index(widget, new_list_index, todos)
        if not self._reinsert_todo_widget(widget, new_list_index):
            return
        self._refresh_order_keys_from_ui()
        self._refresh_completed_ranks_from_ui()
        self._syncCurrentListFromUI()
        self.adjustSize()
        self.updateTODOAmount()

    def _clamp_todo_target_index(self, widget, new_list_index, todos=None):
        if todos is None:
            todos = self._todoWidgets()
        other_todos = [todo for todo in todos if todo is not widget]
        if widget.check_box.isChecked():
            lower_bound = sum(1 for todo in other_todos if not todo.check_box.isChecked())
            upper_bound = len(other_todos)
        else:
            lower_bound = 0
            upper_bound = sum(1 for todo in other_todos if not todo.check_box.isChecked())
        return max(lower_bound, min(int(new_list_index), upper_bound))

    def _reinsert_todo_widget(self, widget, new_list_index):
        todos = self._todoWidgets()
        if widget not in todos:
            return False
        old_i = todos.index(widget)
        if old_i == new_list_index:
            return False
        self.todo_content.removeWidget(widget)
        wtop = self.todo_content.widgets_top
        base = None
        for i, w in enumerate(wtop):
            if isinstance(w, SingleTODOOption):
                base = i
                break
        if base is None:
            base = 2
        insert_at = base + max(0, new_list_index)
        self.todo_content.addWidget(widget, side="top", index=insert_at)
        # 高度未变时不会触发 resizeEvent，需手动按 widgets_top 新顺序重排子控件位置
        self.todo_content.adjustWidgetsGeometry()
        return True

    def _show_todo_context_menu(self, widget, pos):
        todos = self._todoWidgets()
        if widget not in todos:
            return
        idx = todos.index(widget)
        last_i = len(todos) - 1

        menu = QMenu(self)
        apply_popup_menu_appearance(menu)

        act_edit = QAction(self._menu_icon_from_svg_key("fi-rr-edit"), "编辑", self)
        act_edit.triggered.connect(lambda: self._edit_todo_from_context(widget))
        menu.addAction(act_edit)

        act_delete = QAction(self._menu_icon_from_svg_key("fi-rr-trash"), "删除", self)
        act_delete.triggered.connect(lambda: self._remove_todo_widget(widget))
        menu.addAction(act_delete)

        menu.addSeparator()

        act_set_reminder = QAction(self._menu_icon_from_svg_key("fi-rr-bell"), "设置提醒", self)
        act_set_reminder.triggered.connect(lambda: self._set_reminder_from_context(widget))
        menu.addAction(act_set_reminder)

        if getattr(widget, "reminder_data", None):
            act_remove_reminder = QAction(self._menu_icon_from_svg_key("fi-rr-cross"), "删除提醒", self)
            act_remove_reminder.triggered.connect(lambda: self._remove_reminder_from_context(widget))
            menu.addAction(act_remove_reminder)

        menu.addSeparator()

        act_top = QAction(self._menu_icon_from_svg_key("fi-rr-angle-up"), "置顶", self)
        act_top.setEnabled(idx > 0)
        act_top.triggered.connect(lambda: self._move_todo_in_list(widget, 0))
        menu.addAction(act_top)

        act_up = QAction(self._menu_icon_from_svg_key("fi-rr-angle-up"), "上移", self)
        act_up.setEnabled(idx > 0)
        act_up.triggered.connect(lambda: self._move_todo_in_list(widget, idx - 1))
        menu.addAction(act_up)

        act_down = QAction(self._menu_icon_from_svg_key("fi-rr-angle-down"), "下移", self)
        act_down.setEnabled(idx < last_i)
        act_down.triggered.connect(lambda: self._move_todo_in_list(widget, idx + 1))
        menu.addAction(act_down)

        menu.exec_(widget.mapToGlobal(pos))

    def _reorder_todo_lists(self, ordered_keys):
        self.todo_lists = {k: self.todo_lists[k] for k in ordered_keys}

    def _move_list_to_edge(self, list_name, to_top):
        self._syncCurrentListFromUI()
        keys = list(self.todo_lists.keys())
        if list_name not in keys:
            return
        i = keys.index(list_name)
        if to_top:
            if i == 0:
                return
            keys.pop(i)
            keys.insert(0, list_name)
        else:
            if i == len(keys) - 1:
                return
            keys.pop(i)
            keys.append(list_name)
        self._reorder_todo_lists(keys)
        self._rebuildListButtons()
        self._setCurrentList(list_name, sync_before_switch=False)

    def _move_list_by_delta(self, list_name, delta):
        self._syncCurrentListFromUI()
        keys = list(self.todo_lists.keys())
        if list_name not in keys:
            return
        i = keys.index(list_name)
        j = i + delta
        if j < 0 or j >= len(keys):
            return
        keys[i], keys[j] = keys[j], keys[i]
        self._reorder_todo_lists(keys)
        self._rebuildListButtons()
        self._setCurrentList(list_name, sync_before_switch=False)

    def _rename_list_from_context(self, old_name):
        if old_name not in self.todo_lists:
            return

        new_name, ok = show_theme_text_input(
            self.window(), "编辑分类", "清单名称：", old_name
        )
        if not ok:
            return
        new_name = new_name.strip()
        if new_name == "" or new_name == old_name:
            return

        base_name = new_name
        suffix = 2
        while new_name in self.todo_lists:
            new_name = f"{base_name}{suffix}"
            suffix += 1

        self._syncCurrentListFromUI()
        new_dict = {}
        for k, v in self.todo_lists.items():
            if k == old_name:
                new_dict[new_name] = v
            else:
                new_dict[k] = v
        self.todo_lists = new_dict
        if self.current_list_name == old_name:
            self.current_list_name = new_name

        self._rebuildListButtons()
        self._setCurrentList(self.current_list_name, sync_before_switch=False)

    def _clear_list_contents(self, list_name):
        if list_name not in self.todo_lists:
            return
        self._syncCurrentListFromUI()
        self.todo_lists[list_name] = []
        if self.current_list_name == list_name:
            self._setCurrentList(list_name, sync_before_switch=False)

    def _delete_list_from_context(self, list_name):
        if list_name not in self.todo_lists:
            return
        if len(self.todo_lists) <= 1:
            show_theme_information(self.window(), "提示", "至少保留一个清单。")
            return

        reply = show_theme_question(
            self.window(),
            "删除分类",
            f"确定删除清单「{list_name}」吗？此操作不可恢复。",
            default_no=True,
        )
        if reply != QMessageBox.Yes:
            return

        self._syncCurrentListFromUI()
        keys = list(self.todo_lists.keys())
        idx = keys.index(list_name)
        del self.todo_lists[list_name]

        if self.current_list_name == list_name:
            if idx >= len(self.todo_lists):
                idx = len(self.todo_lists) - 1
            self.current_list_name = list(self.todo_lists.keys())[max(0, idx)]

        self._rebuildListButtons()
        self._setCurrentList(self.current_list_name, sync_before_switch=False)

    def _onCreateListClicked(self):
        list_name, ok = show_theme_text_input(self.window(), "新建清单", "请输入清单名称：", "")
        if not ok:
            return

        list_name = list_name.strip()
        if list_name == "":
            return

        base_name = list_name
        suffix = 2
        while list_name in self.todo_lists:
            list_name = f"{base_name}{suffix}"
            suffix += 1

        self.todo_lists[list_name] = []
        self._rebuildListButtons()
        self._setCurrentList(list_name, sync_before_switch=False)

    def loadLists(self, todo_lists):
        normalized_lists = {}
        if isinstance(todo_lists, dict):
            for list_name, todos in todo_lists.items():
                name = str(list_name).strip()
                if name == "":
                    continue
                if isinstance(todos, list):
                    normalized_lists[name] = []
                    fallback_order_key = len(todos)
                    for todo in todos:
                        if isinstance(todo, dict):
                            order_key = todo.get("order_key", None)
                            if not isinstance(order_key, (int, float)):
                                order_key = todo.get("created_order", None)
                            if not isinstance(order_key, (int, float)):
                                order_key = fallback_order_key
                            completed_rank = todo.get("completed_rank", None)
                            normalized_lists[name].append(
                                {
                                    "text": str(todo.get("text", "")),
                                    "done": bool(todo.get("done", False)),
                                    "reminder": todo.get("reminder", None),
                                    "order_key": int(order_key),
                                    "completed_rank": int(completed_rank) if isinstance(completed_rank, (int, float)) else None,
                                }
                            )
                        else:
                            normalized_lists[name].append(
                                {
                                    "text": str(todo),
                                    "done": False,
                                    "reminder": None,
                                    "order_key": fallback_order_key,
                                    "completed_rank": None,
                                }
                            )
                        fallback_order_key -= 1

                    checked_widgets = [todo for todo in normalized_lists[name] if todo.get("done", False)]
                    next_completed_rank = len(checked_widgets)
                    for item in normalized_lists[name]:
                        if item.get("done", False):
                            if item.get("completed_rank", None) is None:
                                item["completed_rank"] = next_completed_rank
                            next_completed_rank -= 1
                        else:
                            item["completed_rank"] = None

                    undone = [todo for todo in normalized_lists[name] if not todo.get("done", False)]
                    done = [todo for todo in normalized_lists[name] if todo.get("done", False)]
                    undone.sort(key=lambda item: int(item.get("order_key", 0)), reverse=True)
                    done.sort(key=lambda item: int(item.get("completed_rank", 0)), reverse=True)
                    normalized_lists[name] = undone + done

        if not normalized_lists:
            normalized_lists = {"默认清单": []}

        self.todo_lists = normalized_lists
        self.current_list_name = ""
        self._rebuildListButtons()
        first_list_name = next(iter(self.todo_lists.keys()))
        self._setCurrentList(first_list_name, sync_before_switch=False, save_to_disk=False)

    def exportLists(self):
        self._syncCurrentListFromUI()
        return {list_name: list(todos) for list_name, todos in self.todo_lists.items()}

    @staticmethod
    def _sidebar_font():
        # 与卡片标题（当前清单名）同源：M_BOLD（Microsoft YaHei 等），侧栏用较小字号与常规字重
        f = QFont(SiGlobal.siui.fonts["M_BOLD"])
        f.setPixelSize(TODOListPanel.SIDEBAR_FONT_PX)
        f.setWeight(QFont.Normal)
        return f

    @staticmethod
    def _sidebar_font_plus_bold():
        """「+」按钮：与 UI 粗体档同源（S_BOLD），小字号加粗"""
        f = QFont(SiGlobal.siui.fonts["S_BOLD"])
        f.setPixelSize(TODOListPanel.SIDEBAR_FONT_PX)
        return f

    def _width_for_sidebar_plus(self):
        fm = QFontMetrics(self._sidebar_font_plus_bold())
        pad = TODOListPanel.SIDEBAR_TEXT_H_PADDING
        return max(20, fm.horizontalAdvance(self.SIDEBAR_PLUS_LABEL) + pad)

    def _width_for_sidebar_text(self, text):
        fm = QFontMetrics(self._sidebar_font())
        
        max_w = 156
        if self.sidebar_host is not self and hasattr(self.sidebar_host, "width"):
            anchor = self.mapTo(self.sidebar_host, QPoint(0, 0))
            if anchor.x() > 10:
                max_w = anchor.x() - 4
                
        pad = TODOListPanel.SIDEBAR_TEXT_H_PADDING
        return min(max_w, max(20, fm.horizontalAdvance(text) + pad))

    def _compute_sidebar_width(self):
        width = self._width_for_sidebar_plus()
        for name in self.todo_lists.keys():
            width = max(width, self._width_for_sidebar_text(name))
        min_w = max(32, (28 * self.SIDEBAR_FONT_PX + 7) // 8)
        # 加上悬停时的偏移量，保证悬停延展时宽度不会超出容器导致右对齐布局向右挤出
        return max(min_w, width) + self.SIDEBAR_HOVER_SHIFT

    @staticmethod
    def _apply_sidebar_si_icon_label(icon_label):
        icon_label.text_label.setFont(TODOListPanel._sidebar_font())
        icon_label.text_label.setFixedHeight(TODOListPanel.SIDEBAR_ROW_HEIGHT)
        icon_label.text_label.setWordWrap(False)
        icon_label.text_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

    def _sidebar_stretch_attachments(self):
        """每个按钮宽度已按各自文字计算，这里只同步 attachment 与按钮同宽。"""
        h_btn = self.SIDEBAR_ROW_HEIGHT
        max_sidebar_w = self._compute_sidebar_width()
        for list_name, btn in self.list_buttons.items():
            bw = max(1, self._width_for_sidebar_text(list_name))
            if bw > max_sidebar_w:
                bw = max_sidebar_w
            btn._sidebar_rest_width = bw
            tw = bw + (self.SIDEBAR_HOVER_SHIFT if btn.underMouse() else 0)
            btn.setFixedSize(tw, h_btn)
            btn.attachment().resize(tw, h_btn)
            self._sidebar_sync_attachment_right(btn)
        nw = self._width_for_sidebar_plus()
        self.new_list_button._sidebar_rest_width = nw
        tw = nw + (self.SIDEBAR_HOVER_SHIFT if self.new_list_button.underMouse() else 0)
        self.new_list_button.setFixedSize(tw, h_btn)
        self.new_list_button.attachment().resize(tw, h_btn)
        self._sidebar_sync_attachment_right(self.new_list_button)

    def _sidebar_hover_anim_to(self, w, target_w):
        """宽度动画：右对齐布局下增宽等价于整体向左伸出。"""
        target_w = int(target_w)
        if w.width() == target_w:
            return
        prev = getattr(w, "_sidebar_width_anim", None)
        if prev is not None:
            prev.stop()
            prev.deleteLater()

        anim = QVariantAnimation(w)
        anim.setDuration(150)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.setStartValue(float(w.width()))
        anim.setEndValue(float(target_w))

        def _on_val(v):
            w0 = int(round(v))
            if w0 == w.width():
                return
            w.setFixedWidth(w0)
            w.attachment().resize(w0, w.height())
            self._sidebar_sync_attachment_right(w)

        anim.valueChanged.connect(_on_val)

        def _on_done():
            w._sidebar_width_anim = None
            w.setFixedWidth(target_w)
            w.attachment().resize(target_w, w.height())
            self._sidebar_sync_attachment_right(w)

        anim.finished.connect(_on_done)
        w._sidebar_width_anim = anim
        anim.start()

    def eventFilter(self, obj, event):
        if hasattr(self, '_resize_handle') and obj is self._resize_handle:
            if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                self._resizing_bottom = True
                self._resize_start_y = event.globalPos().y()
                self._resize_start_height = self.body().height()
                obj.grabMouse()
                return True
            elif event.type() == QEvent.MouseMove and self._resizing_bottom:
                delta = event.globalPos().y() - self._resize_start_y
                self._user_body_height = max(20, self._resize_start_height + delta)
                self.adjustSize()
                return True
            elif event.type() == QEvent.MouseButtonRelease and event.button() == Qt.LeftButton:
                self._resizing_bottom = False
                obj.releaseMouse()
                return True
            elif event.type() == QEvent.MouseButtonDblClick:
                self._user_body_height = None
                self.adjustSize()
                return True

        if hasattr(self, '_right_resize_handle') and obj is self._right_resize_handle:
            if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                self._resizing_right = True
                self._resize_start_x = event.globalPos().x()
                self._resize_start_window_width = getattr(self.window(), "container_v", self).width()
                obj.grabMouse()
                return True
            elif event.type() == QEvent.MouseMove and self._resizing_right:
                delta_x = event.globalPos().x() - self._resize_start_x
                self._apply_main_window_width(self._resize_start_window_width + delta_x)
                return True
            elif event.type() == QEvent.MouseButtonRelease and event.button() == Qt.LeftButton:
                self._resizing_right = False
                obj.releaseMouse()
                return True

        if hasattr(self, '_corner_resize_handle') and obj is self._corner_resize_handle:
            if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                self._resizing_corner = True
                self._resize_start_x = event.globalPos().x()
                self._resize_start_y = event.globalPos().y()
                self._resize_start_window_width = getattr(self.window(), "container_v", self).width()
                self._resize_start_height = self.body().height()
                obj.grabMouse()
                return True
            elif event.type() == QEvent.MouseMove and self._resizing_corner:
                delta_x = event.globalPos().x() - self._resize_start_x
                delta_y = event.globalPos().y() - self._resize_start_y
                self._apply_main_window_width(self._resize_start_window_width + delta_x)
                self._user_body_height = max(20, self._resize_start_height + delta_y)
                self.adjustSize()
                return True
            elif event.type() == QEvent.MouseButtonRelease and event.button() == Qt.LeftButton:
                self._resizing_corner = False
                obj.releaseMouse()
                return True

        if event.type() == QEvent.Enter:
            rw = getattr(obj, "_sidebar_rest_width", None)
            if rw is not None:
                self._sidebar_hover_anim_to(obj, rw + self.SIDEBAR_HOVER_SHIFT)
        elif event.type() == QEvent.Leave:
            rw = getattr(obj, "_sidebar_rest_width", None)
            if rw is not None:
                self._sidebar_hover_anim_to(obj, rw)
        return False

    def _sync_list_items_container_geometry(self, sidebar_width):
        if sidebar_width <= 0:
            return
        self.list_items_container.setFixedWidth(sidebar_width)
        self._list_buttons_layout.activate()
        self.list_items_container.updateGeometry()
        h = max(1, self._list_buttons_layout.sizeHint().height())
        self.list_items_container.setFixedHeight(h)

    def attachSidebarHost(self, host_widget):
        self.sidebar_host = host_widget if host_widget is not None else self
        if self.list_sidebar.parentWidget() is not self.sidebar_host:
            self.list_sidebar.setParent(self.sidebar_host)
        self.list_sidebar.show()
        self._updateSplitLayout()

    def setSidebarVisible(self, visible):
        self.list_sidebar.setVisible(bool(visible))

    def _updateSplitLayout(self):
        sidebar_width = self._compute_sidebar_width()
        self._sync_list_items_container_geometry(sidebar_width)
        # 宽度随内容自适应：取文案测量与布局 sizeHint 的较大者（避免裁字或边距偏差）
        hint_w = self.list_items_container.sizeHint().width()
        if hint_w > sidebar_width:
            sidebar_width = hint_w
            self._sync_list_items_container_geometry(sidebar_width)
        self.list_sidebar.setFixedWidth(sidebar_width)
        self.list_sidebar.adjustSize()
        # 与卡片控件外轮廓左缘对齐（x=0），侧栏完全在卡片左侧，不与圆角/白底重叠
        align_x = 0
        if self.sidebar_host is self:
            anchor = QPoint(align_x, self.header().height() + 8)
        else:
            anchor = self.mapTo(self.sidebar_host, QPoint(align_x, self.header().height() + 8))
        # 侧栏右缘 = 卡片 widget 左缘，相接不叠入
        sidebar_x = anchor.x() - sidebar_width
        sidebar_y = anchor.y()

        # 当窗口靠屏幕左侧时，限制侧栏不超出屏幕，避免被系统裁切
        host_global_origin = self.sidebar_host.mapToGlobal(QPoint(0, 0))
        sidebar_global_x = host_global_origin.x() + sidebar_x
        screen = QApplication.screenAt(QPoint(sidebar_global_x, host_global_origin.y()))
        if screen is None:
            screen = QApplication.primaryScreen()
        if screen is not None:
            left_limit = screen.availableGeometry().left() + 4
            if sidebar_global_x < left_limit:
                sidebar_x += left_limit - sidebar_global_x

        self.list_sidebar.move(sidebar_x, sidebar_y)
        self.list_sidebar.raise_()
        self._sidebar_stretch_attachments()

    def _apply_main_window_width(self, container_width):
        main_window = self.window()
        if main_window is None or not hasattr(main_window, "_apply_container_width"):
            return
        main_window._apply_container_width(container_width)
        main_window.adjustSize()

    def adjustSize(self):
        self._updateSplitLayout()
        self._sync_todo_scroll_area()
        self.todo_scroll_area.setFixedHeight(self._target_body_height())
        self.body().adjustSize()
        super().adjustSize()
        self._sync_todo_scroll_area()
        self._updateNoTodoLabelGeometry()
        self._update_resize_handle()

    def _update_resize_handle(self):
        if hasattr(self, '_resize_handle'):
            self._resize_handle.setGeometry(0, self.height() - 8, max(1, self.width() - 10), 8)
            self._resize_handle.raise_()
        if hasattr(self, '_right_resize_handle'):
            self._right_resize_handle.setGeometry(self.width() - 8, 0, 8, max(1, self.height() - 10))
            self._right_resize_handle.raise_()
        if hasattr(self, '_corner_resize_handle'):
            self._corner_resize_handle.setGeometry(self.width() - 10, self.height() - 10, 10, 10)
            self._corner_resize_handle.raise_()

    def _updateNoTodoLabelGeometry(self):
        self.no_todo_placeholder.resize(self.todo_scroll_area.viewport().width(), self.no_todo_placeholder.height())
        self.no_todo_label.move(0, 0)
        self.no_todo_label.resize(self.no_todo_placeholder.width(), self.no_todo_placeholder.height())

    def leaveEvent(self, event):
        super().leaveEvent(event)

        if SiGlobal.todo_list.todo_list_unfold_button.isChecked() is True:
            self.adjustSize()
            self.updateTODOAmount()

    def showEvent(self, a0):
        super().showEvent(a0)
        self.updateTODOAmount()
        self.setForceUseAnimations(True)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._updateSplitLayout()
        self._sync_todo_scroll_area()
        self._updateNoTodoLabelGeometry()
        self._update_resize_handle()


class AddNewTODOPanel(ThemedOptionCardPlane):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTitle("添加新待办")
        self.setUseSignals(True)

        self.confirm_button = SiSimpleButton(self)
        self.confirm_button.resize(32, 32)
        self.confirm_button.setHint("确认并添加")

        self.cancel_button = SiSimpleButton(self)
        self.cancel_button.resize(32, 32)
        self.cancel_button.setHint("取消")

        self.header().addWidget(self.cancel_button, "right")
        self.header().addWidget(self.confirm_button, "right")

        self.text_edit = QTextEdit(self)
        self.text_edit.setFixedHeight(70)
        self.text_edit.setFont(SiGlobal.siui.fonts["S_NORMAL"])
        self.text_edit.lineWrapMode()

        self.body().setAdjustWidgetsSize(True)
        self.body().setSpacing(4)
        self.body().addWidget(self.text_edit)

    def adjustSize(self):
        self.resize(self.width(), 200)

    def reloadStyleSheet(self):
        self.setThemeColor(SiGlobal.siui.colors["PANEL_THEME"])
        super().reloadStyleSheet()

        self.confirm_button.attachment().load(SiGlobal.siui.icons["fi-rr-check"])
        self.cancel_button.attachment().load(SiGlobal.siui.icons["fi-rr-cross"])
        self.text_edit.setStyleSheet(
            """
            border: 1px solid {};
            background-color: {};
            border-radius: 4px;
            padding-left: 8px; padding-right: 8px;
            color: {}
            """.format(SiGlobal.siui.colors["BORDER_COLOR"],
                       SiGlobal.siui.colors["BACKGROUND_DARK_COLOR"],
                       SiGlobal.siui.colors["TEXT_B"])
        )

    def showEvent(self, a0):
        super().showEvent(a0)
        self.setForceUseAnimations(True)


class ReminderDialog(QDialog):
    def __init__(self, parent=None, current_reminder=None):
        super().__init__(parent)
        self.setWindowTitle("设置提醒")
        self.setFixedSize(360, 480)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        # Style
        theme = SiGlobal.siui.colors["PANEL_THEME"]
        bg = SiGlobal.siui.colors["BACKGROUND_COLOR"]
        bg_deep = SiGlobal.siui.colors["BACKGROUND_DARK_COLOR"]
        text = SiGlobal.siui.colors["TEXT_B"]
        border = SiGlobal.siui.colors["BORDER_COLOR"]

        self.setStyleSheet(f"""
            QDialog {{ background-color: {bg}; color: {text}; }}
            QLabel {{ color: {text}; font-size: 14px; }}
            QTabWidget::pane {{ border: 1px solid {border}; border-radius: 8px; top: -1px; }}
            QTabBar::tab {{
                background: {bg}; color: {text}; padding: 8px 32px;
                border: 1px solid transparent; border-bottom: 1px solid {border};
                font-size: 16px;
            }}
            QTabBar::tab:selected {{ color: {theme}; border-bottom: 2px solid {theme}; }}
            QRadioButton {{ color: {text}; font-size: 14px; padding: 8px 0; }}
            QRadioButton::indicator {{ width: 16px; height: 16px; border-radius: 8px; border: 2px solid {border}; }}
            QRadioButton::indicator:checked {{ border: 5px solid {theme}; background-color: {bg}; }}
            QComboBox {{
                border: 1px solid {border}; border-radius: 6px; padding: 6px 10px;
                background-color: {bg_deep}; color: {text}; font-size: 14px;
            }}
            QComboBox::drop-down {{ border: none; }}
            QComboBox QAbstractItemView {{
                background-color: {bg_deep}; color: {text};
                selection-background-color: {theme};
            }}
            QLineEdit {{
                border: 1px solid {border}; border-radius: 6px; padding: 6px 10px;
                background-color: {bg_deep}; color: {text}; font-size: 14px;
            }}
            QPushButton {{
                border: 1px solid {border}; border-radius: 6px; padding: 8px 24px;
                background-color: {bg_deep}; color: {text}; font-size: 14px;
            }}
            QPushButton:hover {{ background-color: {SiGlobal.siui.colors["BUTTON_HOVER"]}; }}
            QPushButton#btn_confirm {{ background-color: {theme}; color: #ffffff; border: none; }}
            QPushButton#btn_quick {{ border: none; background: transparent; color: {theme}; padding: 4px; }}
            QPushButton#btn_quick:hover {{ background: {SiGlobal.siui.colors["BUTTON_HOVER"]}; border-radius: 4px; }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        self.tabs = QTabWidget(self)
        layout.addWidget(self.tabs)

        self.tab_select = QWidget()
        self.tab_settings = QWidget()
        self.tabs.addTab(self.tab_select, "选择")
        self.tabs.addTab(self.tab_settings, "设置")

        self._init_tab_select()
        self._init_tab_settings()

        # Bottom buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_cancel = QPushButton("取消", self)
        btn_cancel.clicked.connect(self.reject)
        self.btn_confirm = QPushButton("确定", self)
        self.btn_confirm.setObjectName("btn_confirm")
        self.btn_confirm.clicked.connect(self.accept)
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(self.btn_confirm)
        layout.addLayout(btn_layout)

        if current_reminder:
            self._load_reminder(current_reminder)

    def _init_tab_select(self):
        layout = QVBoxLayout(self.tab_select)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 24, 16, 16)

        self.radio_group = []
        now = datetime.now()

        def add_opt(text, right_text, t):
            h = QHBoxLayout()
            rb = QRadioButton(text)
            self.radio_group.append((rb, t))
            h.addWidget(rb)
            h.addStretch()
            lbl = QLabel(right_text)
            lbl.setStyleSheet(f"color: {SiGlobal.siui.colors['TEXT_D']}; font-size: 13px;")
            h.addWidget(lbl)
            layout.addLayout(h)
            line = QWidget()
            line.setFixedHeight(1)
            line.setStyleSheet(f"background: {SiGlobal.siui.colors['BORDER_COLOR']};")
            layout.addWidget(line)

        # 30分钟后
        t_30 = now + timedelta(minutes=30)
        add_opt("30分钟后", t_30.strftime("%H:%M"), t_30)

        # 明天9点
        t_tmr = (now + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
        add_opt("明天9点", t_tmr.strftime("%m-%d %H:%M"), t_tmr)

        # Ai提取时间 (Mock)
        add_opt("Ai提取时间", "", None)

        # 本周日
        days_ahead = 6 - now.weekday()
        if days_ahead <= 0: days_ahead += 7
        t_sun = (now + timedelta(days=days_ahead)).replace(hour=9, minute=0, second=0, microsecond=0)
        add_opt("本周日", t_sun.strftime("%m-%d %H:%M"), t_sun)

        # 下周一
        days_ahead = 7 - now.weekday()
        if days_ahead <= 0: days_ahead += 7
        t_mon = (now + timedelta(days=days_ahead)).replace(hour=9, minute=0, second=0, microsecond=0)
        add_opt("下周一", t_mon.strftime("%m-%d %H:%M"), t_mon)

        layout.addStretch()

        for rb, t in self.radio_group:
            rb.toggled.connect(self._on_radio_toggled)

    def _on_radio_toggled(self, checked):
        if not checked: return
        for rb, t in self.radio_group:
            if rb.isChecked() and t:
                self.date_input.setText(t.strftime("%Y-%m-%d"))
                self.hour_cb.setCurrentText(f"{t.hour:02d}")
                self.min_cb.setCurrentText(f"{t.minute:02d}")
                break

    def _init_tab_settings(self):
        layout = QGridLayout(self.tab_settings)
        layout.setVerticalSpacing(24)
        layout.setContentsMargins(16, 24, 16, 16)

        # 提醒日期
        layout.addWidget(QLabel("提醒日期"), 0, 0)
        self.date_input = QLineEdit()
        self.date_input.setText(datetime.now().strftime("%Y-%m-%d"))
        layout.addWidget(self.date_input, 0, 1)

        # 提醒时间
        layout.addWidget(QLabel("提醒时间"), 1, 0)
        time_layout = QHBoxLayout()
        self.hour_cb = QComboBox()
        self.hour_cb.addItems([f"{i:02d}" for i in range(24)])
        self.hour_cb.setCurrentText("12")
        self.min_cb = QComboBox()
        self.min_cb.addItems([f"{i:02d}" for i in range(60)])
        self.min_cb.setCurrentText("00")
        time_layout.addWidget(self.hour_cb)
        time_layout.addWidget(QLabel(":"))
        time_layout.addWidget(self.min_cb)
        layout.addLayout(time_layout, 1, 1)

        # 快捷时间
        quick_layout = QHBoxLayout()
        for t in ["08:00", "12:00", "18:00", "21:00"]:
            btn = QPushButton(t)
            btn.setObjectName("btn_quick")
            btn.clicked.connect(lambda _, text=t: (self.hour_cb.setCurrentText(text[:2]), self.min_cb.setCurrentText(text[3:])))
            quick_layout.addWidget(btn)
        quick_layout.addStretch()
        layout.addLayout(quick_layout, 2, 1)

        # 是否重复
        layout.addWidget(QLabel("是否重复"), 3, 0)
        self.repeat_cb = QComboBox()
        self.repeat_cb.addItems(["不重复", "每天", "每周", "每月"])
        layout.addWidget(self.repeat_cb, 3, 1)

        # 重要事项
        layout.addWidget(QLabel("重要事项"), 4, 0)
        self.priority_cb = QComboBox()
        self.priority_cb.addItems(["不重要", "重要", "紧急"])
        layout.addWidget(self.priority_cb, 4, 1)

        layout.setRowStretch(5, 1)

    def _load_reminder(self, data):
        self.tabs.setCurrentIndex(1)
        if "timestamp" in data:
            t = datetime.fromtimestamp(data["timestamp"])
            self.date_input.setText(t.strftime("%Y-%m-%d"))
            self.hour_cb.setCurrentText(f"{t.hour:02d}")
            self.min_cb.setCurrentText(f"{t.minute:02d}")
        if "repeat" in data:
            self.repeat_cb.setCurrentText(data["repeat"])
        if "priority" in data:
            self.priority_cb.setCurrentText(data["priority"])

    def get_reminder_data(self):
        try:
            d_str = self.date_input.text()
            h_str = self.hour_cb.currentText()
            m_str = self.min_cb.currentText()
            dt = datetime.strptime(f"{d_str} {h_str}:{m_str}", "%Y-%m-%d %H:%M")
        except:
            dt = datetime.now()
        return {
            "timestamp": int(dt.timestamp()),
            "repeat": self.repeat_cb.currentText(),
            "priority": self.priority_cb.currentText()
        }


class YearMonthPickerDialog(QDialog):
    def __init__(self, parent=None, current_year=None, current_month=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(420, 180)

        bg = SiGlobal.siui.colors["BACKGROUND_COLOR"]
        bg_dark = SiGlobal.siui.colors["BACKGROUND_DARK_COLOR"]
        border = SiGlobal.siui.colors["BORDER_COLOR"]
        text_a = SiGlobal.siui.colors["TEXT_A"]
        text_b = SiGlobal.siui.colors["TEXT_B"]
        text_c = SiGlobal.siui.colors["TEXT_C"]
        theme = SiGlobal.siui.colors["PANEL_THEME"]

        self._container = QWidget(self)
        self._container.setGeometry(0, 0, 420, 180)
        self._container.setStyleSheet(
            f"background-color: {bg}; border: 1px solid {border}; border-radius: 10px;")

        shadow = QGraphicsDropShadowEffect()
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 2)
        shadow.setBlurRadius(16)
        self._container.setGraphicsEffect(shadow)

        main_layout = QVBoxLayout(self._container)
        main_layout.setContentsMargins(24, 16, 24, 16)
        main_layout.setSpacing(16)

        title_layout = QHBoxLayout()
        title_lbl = QLabel("选择年月")
        title_lbl.setStyleSheet(f"color: {text_a}; font-size: 15px; font-weight: bold; border: none; background: transparent;")
        close_btn = QPushButton("×")
        close_btn.setFixedSize(28, 28)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(self.reject)
        close_btn.setStyleSheet(
            f"QPushButton {{ color: {text_c}; font-size: 18px; border: none; border-radius: 14px; background: transparent; }}"
            f"QPushButton:hover {{ background-color: {border}; }}")
        title_layout.addWidget(title_lbl)
        title_layout.addStretch()
        title_layout.addWidget(close_btn)
        main_layout.addLayout(title_layout)

        import tempfile as _tf
        _tmp = _tf.gettempdir().replace("\\", "/")
        _down_svg = (
            '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="6">'
            f'<polygon points="0,0 10,0 5,6" fill="{text_c}"/></svg>')
        _up_svg = (
            '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="6">'
            f'<polygon points="5,0 10,6 0,6" fill="{theme}"/></svg>')
        _down_path = f"{_tmp}/todo_arrow_down.svg"
        _up_path = f"{_tmp}/todo_arrow_up.svg"
        with open(_down_path, "w", encoding="utf-8") as _f:
            _f.write(_down_svg)
        with open(_up_path, "w", encoding="utf-8") as _f:
            _f.write(_up_svg)

        combo_ss = """
            QComboBox {{
                border: 1px solid {border};
                border-radius: 6px;
                padding: 6px 12px;
                background-color: {bg_dark};
                color: {text};
                font-size: 14px;
                min-width: 80px;
            }}
            QComboBox:hover {{
                border: 1px solid {theme};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 28px;
            }}
            QComboBox::down-arrow {{
                image: url({down_path});
                width: 10px;
                height: 6px;
            }}
            QComboBox::down-arrow:on {{
                image: url({up_path});
                width: 10px;
                height: 6px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {bg_dark};
                color: {text};
                border: 1px solid {border};
                border-radius: 4px;
                selection-background-color: {theme};
                selection-color: #ffffff;
                outline: 0;
                padding: 4px;
            }}
        """.format(
            border=border, bg_dark=bg_dark, text=text_b,
            text_c=text_c, theme=theme,
            down_path=_down_path, up_path=_up_path,
        )
        label_ss = f"color: {text_b}; font-size: 14px; border: none; background: transparent;"

        row = QHBoxLayout()
        row.setSpacing(10)

        self.year_cb = QComboBox()
        self.year_cb.setStyleSheet(combo_ss)
        for y in range(2000, 2051):
            self.year_cb.addItem(str(y), y)
        if current_year is not None:
            idx = self.year_cb.findData(current_year)
            if idx >= 0:
                self.year_cb.setCurrentIndex(idx)

        self.month_cb = QComboBox()
        self.month_cb.setStyleSheet(combo_ss)
        for m in range(1, 13):
            self.month_cb.addItem(str(m), m)
        if current_month is not None:
            idx = self.month_cb.findData(current_month)
            if idx >= 0:
                self.month_cb.setCurrentIndex(idx)

        year_label = QLabel("年份")
        year_label.setStyleSheet(label_ss)
        month_label = QLabel("月份")
        month_label.setStyleSheet(label_ss)

        row.addWidget(year_label)
        row.addWidget(self.year_cb, 1)
        row.addSpacing(16)
        row.addWidget(month_label)
        row.addWidget(self.month_cb, 1)
        main_layout.addLayout(row)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_ss = """
            QPushButton {{
                border: 1px solid {border};
                border-radius: 6px;
                padding: 7px 24px;
                background-color: {bg_dark};
                color: {text};
                font-size: 13px;
            }}
            QPushButton:hover {{
                border: 1px solid {theme};
                background-color: {bg_dark};
            }}
        """.format(border=border, bg_dark=bg_dark, text=text_b, theme=theme)
        btn_confirm_ss = """
            QPushButton {{
                border: 1px solid {theme};
                border-radius: 6px;
                padding: 7px 24px;
                background-color: {theme};
                color: #ffffff;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {theme_h};
            }}
        """.format(theme=theme, theme_h=theme)

        btn_cancel = QPushButton("取消")
        btn_cancel.setStyleSheet(btn_ss)
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_confirm = QPushButton("确定")
        btn_confirm.setStyleSheet(btn_confirm_ss)
        btn_confirm.setCursor(Qt.PointingHandCursor)
        btn_cancel.clicked.connect(self.reject)
        btn_confirm.clicked.connect(self.accept)
        btn_confirm.setDefault(True)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_confirm)
        main_layout.addLayout(btn_layout)

        self._drag_pos = None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() & Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    def get_year_month(self):
        return self.year_cb.currentData(), self.month_cb.currentData()


class CalendarDayWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.date = None
        self.is_current_month = False
        self.todo_items = []
        self._calendar_panel = None

        self.setCursor(Qt.PointingHandCursor)
        self.setAttribute(Qt.WA_Hover, True)

        self.bg_label = SiLabel(self)
        self.bg_label.setFixedStyleSheet("border-radius: 6px;")

        self.date_label = SiLabel(self)
        f = QFont(SiGlobal.siui.fonts["S_NORMAL"])
        self.date_label.setFont(f)
        self.date_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.date_label.setAttribute(Qt.WA_TransparentForMouseEvents)

        self.today_badge = SiLabel(self)
        self.today_badge.setText("今")
        self.today_badge.setAlignment(Qt.AlignCenter)
        self.today_badge.setFixedSize(22, 22)
        self.today_badge.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.today_badge.hide()

        self._todo_labels = []

        self.add_btn = SiSimpleButton(self)
        self.add_btn.resize(20, 20)
        self.add_btn.setHint("添加待办")
        self.add_btn.hide()
        self.add_btn.clicked.connect(self._on_add_clicked)

    def set_calendar_panel(self, panel):
        self._calendar_panel = panel

    def set_date(self, d, is_current):
        self.date = d
        self.is_current_month = is_current
        self.date_label.setText(str(d.day))
        today = date.today()
        if d == today:
            self.today_badge.show()
        else:
            self.today_badge.hide()
        self.reloadStyleSheet()

    def set_todos(self, todos):
        self.todo_items = todos
        for lbl in self._todo_labels:
            lbl.setParent(None)
            lbl.deleteLater()
        self._todo_labels = []

        max_show = 3
        for i, todo in enumerate(todos[:max_show]):
            lbl = QLabel(self)
            lbl.setCursor(Qt.PointingHandCursor)
            f = QFont(SiGlobal.siui.fonts["S_NORMAL"])
            f.setPixelSize(11)
            lbl.setFont(f)
            lbl.setContextMenuPolicy(Qt.CustomContextMenu)
            todo_ref = todo
            lbl.customContextMenuRequested.connect(
                lambda pos, t=todo_ref, l=lbl: self._on_todo_context_menu(t, l.mapToGlobal(pos)))
            lbl.show()
            self._todo_labels.append(lbl)

        self._update_todo_label_text()
        self._layout_children()

    def _update_todo_label_text(self):
        for i, lbl in enumerate(self._todo_labels):
            if i >= len(self.todo_items):
                break
            todo = self.todo_items[i]
            dot_color = "#52c41a" if todo.get("done", False) else "#ff4d4f"
            text = todo.get("text", "")
            fm = QFontMetrics(lbl.font())
            available_w = max(1, self.width() - 20)
            elided = fm.elidedText(text, Qt.ElideRight, available_w)
            lbl.setText(f"● {elided}")
            lbl.setStyleSheet(f"color: {dot_color}; background: transparent;")

    def _layout_children(self):
        w, h = self.width(), self.height()
        if w <= 0 or h <= 0:
            return
        self.bg_label.resize(w, h)
        self.date_label.resize(w - 8, 20)
        self.date_label.move(8, 4)
        self.today_badge.move(w - 26, 2)

        y_offset = 24
        for lbl in self._todo_labels:
            lbl.setGeometry(4, y_offset, w - 8, 14)
            y_offset += 16

        self.add_btn.move(w - 24, h - 24)

    def _on_todo_context_menu(self, todo_data, global_pos):
        if not self._calendar_panel:
            return
        self._calendar_panel._show_calendar_todo_context_menu(todo_data, global_pos)

    def enterEvent(self, e):
        super().enterEvent(e)
        self.add_btn.show()
        self._refresh_bg(hover=True)

    def leaveEvent(self, e):
        super().leaveEvent(e)
        self.add_btn.hide()
        self._refresh_bg(hover=False)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._update_todo_label_text()
        self._layout_children()

    def _on_add_clicked(self):
        if not self.date or not self._calendar_panel:
            return
        text, ok = show_theme_text_input(self.window(), "添加待办", "内容：")
        if not ok or not text.strip():
            return
        ts = int(datetime.combine(self.date, datetime.min.time().replace(hour=9)).timestamp())
        parser = SiGlobal.todo_list.todos_parser
        first_list = next(iter(parser.lists.keys()), None)
        if first_list is None:
            return
        parser.lists[first_list].append({
            "text": text.strip(),
            "done": False,
            "reminder": {"timestamp": ts, "repeat": "不重复", "priority": "不重要"}
        })
        parser.write()
        self._calendar_panel.update_calendar()
        self._calendar_panel._refresh_main_panel()

    def _refresh_bg(self, hover=False):
        if not self.date:
            return
        today = date.today()
        if self.date == today:
            self.bg_label.setStyleSheet(f"background-color: {SiGlobal.siui.colors['PANEL_THEME']}; border-radius: 6px;")
            self.date_label.setStyleSheet("color: #ffffff; font-weight: bold; background-color: transparent;")
        else:
            if hover:
                self.bg_label.setStyleSheet(f"background-color: {SiGlobal.siui.colors['BUTTON_HOVER']}; border-radius: 6px;")
            else:
                self.bg_label.setStyleSheet("background-color: transparent; border-radius: 6px;")

            if self.is_current_month:
                self.date_label.setStyleSheet(f"color: {SiGlobal.siui.colors['TEXT_B']}; font-weight: normal; background-color: transparent;")
            else:
                self.date_label.setStyleSheet(f"color: {SiGlobal.siui.colors['TEXT_E']}; font-weight: normal; background-color: transparent;")

    def reloadStyleSheet(self):
        if not self.date: return
        self.add_btn.attachment().load(SiGlobal.siui.icons.get("fi-rr-plus", SiGlobal.siui.icons.get("fi-rr-apps-add")))
        self.add_btn.setStateColor(SiGlobal.siui.colors["TOGGLE_BUTTON_OFF_BG"], SiGlobal.siui.colors["TOGGLE_BUTTON_ON_BG"])
        self.today_badge.setStyleSheet(
            f"background-color: {SiGlobal.siui.colors['PANEL_THEME']}; "
            f"color: #ffffff; font-size: 11px; font-weight: bold; "
            f"border-radius: 11px;")
        self._refresh_bg()


class CalendarPanel(ThemedOptionCardPlane):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setTitle("日历")
        self.setUseSignals(True)
        
        today = date.today()
        self.view_year = today.year
        self.view_month = today.month

        # 控制栏
        self.controls_container = SiDenseHContainer(self.body())
        self.controls_container.setFixedHeight(32)
        self.controls_container.setSpacing(8)
        
        self.month_label = SiLabel(self.controls_container)
        f = QFont(SiGlobal.siui.fonts["M_BOLD"])
        f.setPixelSize(20)
        self.month_label.setFont(f)
        self.month_label.setAutoAdjustSize(True)
        self.month_label.setCursor(Qt.PointingHandCursor)
        self.month_label.installEventFilter(self)
        
        self.prev_btn = QPushButton("＜", self.controls_container)
        self.prev_btn.setFixedSize(32, 32)
        self.prev_btn.setCursor(Qt.PointingHandCursor)
        self.prev_btn.setToolTip("上个月")
        self.prev_btn.clicked.connect(self._prev_month)

        self.next_btn = QPushButton("＞", self.controls_container)
        self.next_btn.setFixedSize(32, 32)
        self.next_btn.setCursor(Qt.PointingHandCursor)
        self.next_btn.setToolTip("下个月")
        self.next_btn.clicked.connect(self._next_month)
        
        self.controls_container.addWidget(self.month_label)
        self.controls_container.addWidget(self.next_btn, "right")
        self.controls_container.addWidget(self.prev_btn, "right")
        
        self.body().addWidget(self.controls_container)
        self.body().addPlaceholder(8)
        
        # 星期标题
        self.weekdays_container = SiDenseHContainer(self.body())
        self.weekdays_container.setFixedHeight(24)
        self.weekdays_container.setSpacing(0)
        weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        self.weekday_labels = []
        for wd in weekdays:
            lbl = SiLabel(self.weekdays_container)
            lbl.setText(wd)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setFont(SiGlobal.siui.fonts["S_NORMAL"])
            self.weekday_labels.append(lbl)
            self.weekdays_container.addWidget(lbl)
            
        self.body().addWidget(self.weekdays_container)
        self.body().addPlaceholder(8)
        
        # 日期网格
        self.grid_widget = QWidget(self.body())
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(4)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.body().addWidget(self.grid_widget)
        self.body().addPlaceholder(8)
        
        self.day_widgets = []
        for row in range(6):
            for col in range(7):
                day_w = CalendarDayWidget(self.grid_widget)
                day_w.set_calendar_panel(self)
                self.grid_layout.addWidget(day_w, row, col)
                self.day_widgets.append(day_w)
                
        self.update_calendar()

    def eventFilter(self, obj, event):
        if obj == self.month_label and event.type() == QEvent.MouseButtonRelease:
            self._show_year_month_picker()
            return True
        return super().eventFilter(obj, event)

    def _show_year_month_picker(self):
        dlg = YearMonthPickerDialog(self.window(), self.view_year, self.view_month)
        if dlg.exec_() == QDialog.Accepted:
            y, m = dlg.get_year_month()
            self.view_year = y
            self.view_month = m
            self.update_calendar()

    def _prev_month(self):
        if self.view_month == 1:
            self.view_month = 12
            self.view_year -= 1
        else:
            self.view_month -= 1
        self.update_calendar()

    def _next_month(self):
        if self.view_month == 12:
            self.view_month = 1
            self.view_year += 1
        else:
            self.view_month += 1
        self.update_calendar()

    def _collect_reminder_todos(self):
        result = {}
        parser = SiGlobal.todo_list.todos_parser
        for list_name, todos in parser.lists.items():
            for i, todo in enumerate(todos):
                if not isinstance(todo, dict):
                    continue
                reminder = todo.get("reminder")
                if reminder and "timestamp" in reminder:
                    ts = reminder["timestamp"]
                    try:
                        d = date.fromtimestamp(ts)
                    except (OSError, ValueError):
                        continue
                    if d not in result:
                        result[d] = []
                    result[d].append({
                        "text": todo.get("text", ""),
                        "done": todo.get("done", False),
                        "reminder": reminder,
                        "list_name": list_name,
                        "index": i,
                    })
        return result

    def update_calendar(self):
        self.month_label.setText(f"{self.view_year}年{self.view_month}月  ▼")
        self.controls_container.adjustSize()

        reminder_todos = self._collect_reminder_todos()

        cal = calendar.Calendar(firstweekday=0)
        month_days = list(cal.itermonthdates(self.view_year, self.view_month))
        for i, d in enumerate(month_days):
            if i < len(self.day_widgets):
                self.day_widgets[i].set_date(d, d.month == self.view_month)
                todos_for_day = reminder_todos.get(d, [])
                self.day_widgets[i].set_todos(todos_for_day)
                self.day_widgets[i].show()

        for i in range(len(month_days), len(self.day_widgets)):
            self.day_widgets[i].hide()
            
    def _show_calendar_todo_context_menu(self, todo_data, global_pos):
        menu = QMenu(self)
        apply_popup_menu_appearance(menu)

        act_edit = QAction(themed_icon_from_svg_key("fi-rr-edit", menu_left_pad=8), "编辑内容", self)
        act_edit.triggered.connect(lambda: self._edit_calendar_todo(todo_data))
        menu.addAction(act_edit)

        act_reminder = QAction(themed_icon_from_svg_key("fi-rr-bell", menu_left_pad=8), "编辑提醒", self)
        act_reminder.triggered.connect(lambda: self._edit_calendar_todo_reminder(todo_data))
        menu.addAction(act_reminder)

        menu.addSeparator()

        done_text = "取消完成" if todo_data.get("done", False) else "完成"
        done_icon = "fi-rr-cross" if todo_data.get("done", False) else "fi-rr-check"
        act_done = QAction(themed_icon_from_svg_key(done_icon, menu_left_pad=8), done_text, self)
        act_done.triggered.connect(lambda: self._toggle_calendar_todo_done(todo_data))
        menu.addAction(act_done)

        act_delete = QAction(themed_icon_from_svg_key("fi-rr-trash", menu_left_pad=8), "删除", self)
        act_delete.triggered.connect(lambda: self._delete_calendar_todo(todo_data))
        menu.addAction(act_delete)

        menu.exec_(global_pos)

    def _edit_calendar_todo(self, todo_data):
        list_name = todo_data["list_name"]
        index = todo_data["index"]
        parser = SiGlobal.todo_list.todos_parser
        if list_name not in parser.lists or index >= len(parser.lists[list_name]):
            return
        current_text = parser.lists[list_name][index].get("text", "")
        new_text, ok = show_theme_text_input(self.window(), "编辑待办", "内容：", current_text)
        if not ok:
            return
        new_text = new_text.strip()
        if new_text == "":
            return
        parser.lists[list_name][index]["text"] = new_text
        parser.write()
        self.update_calendar()
        self._refresh_main_panel()

    def _edit_calendar_todo_reminder(self, todo_data):
        list_name = todo_data["list_name"]
        index = todo_data["index"]
        parser = SiGlobal.todo_list.todos_parser
        if list_name not in parser.lists or index >= len(parser.lists[list_name]):
            return
        current_reminder = parser.lists[list_name][index].get("reminder")
        dlg = ReminderDialog(self.window(), current_reminder)
        if dlg.exec_() == QDialog.Accepted:
            reminder_data = dlg.get_reminder_data()
            parser.lists[list_name][index]["reminder"] = reminder_data
            parser.write()
            self.update_calendar()
            self._refresh_main_panel()

    def _toggle_calendar_todo_done(self, todo_data):
        list_name = todo_data["list_name"]
        index = todo_data["index"]
        parser = SiGlobal.todo_list.todos_parser
        if list_name not in parser.lists or index >= len(parser.lists[list_name]):
            return
        current_done = parser.lists[list_name][index].get("done", False)
        parser.lists[list_name][index]["done"] = not current_done
        parser.write()
        self.update_calendar()
        self._refresh_main_panel()

    def _delete_calendar_todo(self, todo_data):
        list_name = todo_data["list_name"]
        index = todo_data["index"]
        parser = SiGlobal.todo_list.todos_parser
        if list_name not in parser.lists or index >= len(parser.lists[list_name]):
            return
        reply = show_theme_question(
            self.window(), "删除待办",
            f"确定删除「{todo_data.get('text', '')}」吗？", default_no=True)
        if reply != QMessageBox.Yes:
            return
        parser.lists[list_name].pop(index)
        parser.write()
        self.update_calendar()
        self._refresh_main_panel()

    def _refresh_main_panel(self):
        main_window = SiGlobal.siui.windows.get("MAIN_WINDOW")
        if main_window and hasattr(main_window, "todo_list_panel"):
            panel = main_window.todo_list_panel
            saved_list = panel.current_list_name
            panel.loadLists(SiGlobal.todo_list.todos_parser.lists)
            if saved_list in panel.todo_lists:
                panel._setCurrentList(saved_list, sync_before_switch=False, save_to_disk=False)

    def reloadStyleSheet(self):
        self.setThemeColor(SiGlobal.siui.colors["PANEL_THEME"])
        super().reloadStyleSheet()
        
        self.month_label.setStyleSheet(f"color: {SiGlobal.siui.colors['TEXT_A']};")
        nav_btn_ss = """
            QPushButton {{
                border: 1px solid {border};
                border-radius: 6px;
                background-color: transparent;
                color: {text};
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {hover};
            }}
            QPushButton:pressed {{
                background-color: {pressed};
            }}
        """.format(
            border=SiGlobal.siui.colors["BORDER_COLOR"],
            text=SiGlobal.siui.colors["TEXT_B"],
            hover=SiGlobal.siui.colors["BUTTON_HOVER"],
            pressed=SiGlobal.siui.colors["BUTTON_FLASH"],
        )
        self.prev_btn.setStyleSheet(nav_btn_ss)
        self.next_btn.setStyleSheet(nav_btn_ss)
        
        for lbl in self.weekday_labels:
            lbl.setStyleSheet(f"color: {SiGlobal.siui.colors['TEXT_C']};")
            
        for dw in self.day_widgets:
            dw.reloadStyleSheet()
            
    def resizeEvent(self, e):
        super().resizeEvent(e)
        w = self.width() - 64
        if w < 10: return
        
        self.controls_container.setFixedWidth(w)
        self.controls_container.adjustWidgetsGeometry()
        
        self.weekdays_container.setFixedWidth(w)
        col_w = w // 7
        for lbl in self.weekday_labels:
            lbl.setFixedWidth(col_w)
        self.weekdays_container.adjustWidgetsGeometry()
        
        top_h = self.header().height() + 32 + 8 + 24 + 8
        available_h = self.height() - top_h - 32
        
        available_h = max(available_h, 6 * 64 + 5 * 4)
        row_h = (available_h - 5 * 4) // 6
        
        self.grid_widget.setFixedSize(w, 6 * row_h + 5 * 4)
        for dw in self.day_widgets:
            dw.setFixedSize(col_w - 4, row_h)
            
        self.body().adjustSize()

class SettingsPanel(ThemedOptionCardPlane):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTitle("设置")
        self.setUseSignals(True)

        # 启用深色模式
        self.use_dark_mode = SingleSettingOption(self)
        self.use_dark_mode.setTitle("深色模式", "在深色主题的计算机上提供更佳的视觉效果")

        self.button_use_dark_mode = SiSwitch(self)
        self.button_use_dark_mode.setFixedHeight(32)
        self.button_use_dark_mode.toggled.connect(load_colors)
        self.button_use_dark_mode.toggled.connect(
            lambda b: SiGlobal.todo_list.settings_parser.modify("USE_DARK_MODE", b))
        self.button_use_dark_mode.setChecked(SiGlobal.todo_list.settings_parser.options["USE_DARK_MODE"])

        self.use_dark_mode.addWidget(self.button_use_dark_mode)
        self.use_dark_mode.addPlaceholder(16)

        # 锁定位置
        self.fix_position = SingleSettingOption(self)
        self.fix_position.setTitle("锁定位置", "阻止拖动窗口以保持位置不变")

        self.button_fix_position = SiSwitch(self)
        self.button_fix_position.setFixedHeight(32)
        self.button_fix_position.toggled.connect(lock_position)
        self.button_fix_position.toggled.connect(
            lambda b: SiGlobal.todo_list.settings_parser.modify("FIXED_POSITION", b))
        self.button_fix_position.setChecked(SiGlobal.todo_list.settings_parser.options["FIXED_POSITION"])

        self.fix_position.addWidget(self.button_fix_position)
        self.fix_position.addPlaceholder(16)

        # 开机自启动（仅 Windows，写入注册表「运行」项）
        self.button_startup = None
        if startup_supported():
            self.startup_option = SingleSettingOption(self)
            self.startup_option.setTitle("开机自启动", "登录 Windows 时自动运行本程序")
            self.button_startup = SiSwitch(self)
            self.button_startup.setFixedHeight(32)
            self.button_startup.setChecked(is_startup_enabled())
            self.startup_option.addWidget(self.button_startup)
            self.startup_option.addPlaceholder(16)

        # 半透明模式
        self.use_translucent_mode = SingleSettingOption(self)
        self.use_translucent_mode.setTitle("半透明模式", "降低窗口不透明度，显示更轻盈")

        self.button_use_translucent_mode = SiSwitch(self)
        self.button_use_translucent_mode.setFixedHeight(32)
        self.button_use_translucent_mode.toggled.connect(set_translucent_mode)
        self.button_use_translucent_mode.setChecked(
            bool(SiGlobal.todo_list.settings_parser.options.get("TRANSLUCENT_MODE", False)))

        self.use_translucent_mode.addWidget(self.button_use_translucent_mode)
        self.use_translucent_mode.addPlaceholder(16)

        # 半透明强度
        self.translucent_opacity = SingleSettingOption(self)
        self.translucent_opacity.setTitle("透明度", "值越小越透明，仅在半透明模式打开时生效")

        self.translucent_opacity_slider = QSlider(Qt.Horizontal, self)
        self.translucent_opacity_slider.setRange(10, 95)
        saved_opacity = int(SiGlobal.todo_list.settings_parser.options.get("TRANSLUCENT_OPACITY", 70))
        saved_opacity = max(10, min(95, saved_opacity))
        self.translucent_opacity_slider.setValue(saved_opacity)
        self.translucent_opacity_slider.setFixedWidth(150)
        self.translucent_opacity_slider.valueChanged.connect(self._onTranslucentOpacityChanged)
        self.translucent_opacity_slider.setEnabled(self.button_use_translucent_mode.isChecked())
        self.button_use_translucent_mode.toggled.connect(self.translucent_opacity_slider.setEnabled)

        self.translucent_opacity_value = SiLabel(self)
        self.translucent_opacity_value.setFont(SiGlobal.siui.fonts["S_NORMAL"])
        self.translucent_opacity_value.setAutoAdjustSize(True)
        self.translucent_opacity_value.setText(f"{saved_opacity}%")

        self.translucent_opacity.addWidget(self.translucent_opacity_slider)
        self.translucent_opacity.addWidget(self.translucent_opacity_value)
        self.translucent_opacity.addPlaceholder(16)

        # 字号（清单正文与勾选框指示器同一数值）
        self.todo_font_option = SingleSettingOption(self)
        self.todo_font_option.setTitle("字号", "像素值（8–24）")

        self.todo_font_px_input = QLineEdit(self)
        self.todo_font_px_input.setFixedWidth(56)
        self.todo_font_px_input.setText(str(todo_item_font_px()))
        self.todo_font_px_input.editingFinished.connect(self._onTodoFontPxEditingFinished)

        self.todo_font_option.addWidget(self.todo_font_px_input)
        self.todo_font_option.addPlaceholder(16)

        self.settings_footer_credits = SiLabel(self)
        self.settings_footer_credits.setTextFormat(Qt.RichText)
        self.settings_footer_credits.setOpenExternalLinks(True)
        self.settings_footer_credits.setAlignment(Qt.AlignCenter)
        self.settings_footer_credits.setAutoAdjustSize(True)
        self.settings_footer_credits.setHint("")

        # 添加到body
        self.body().setAdjustWidgetsSize(True)
        self.body().addWidget(self.use_dark_mode)
        self.body().addWidget(self.fix_position)
        if self.button_startup is not None:
            self.body().addWidget(self.startup_option)
        self.body().addWidget(self.use_translucent_mode)
        self.body().addWidget(self.translucent_opacity)
        self.body().addWidget(self.todo_font_option)
        self.body().addWidget(self.settings_footer_credits)
        self.body().addPlaceholder(16)

    def reloadStyleSheet(self):
        self.setThemeColor(SiGlobal.siui.colors["PANEL_THEME"])
        super().reloadStyleSheet()
        text_d = SiGlobal.siui.colors["TEXT_D"]
        # self.settings_footer_credits.setText(
        #     '<a href="https://github.com/InfiniteLoop888/TodoList" '
        #     'style="color:{}; font-size:11px; text-decoration:none;">InfiniteLoop888</a>'.format(text_d)
        # )
        self.settings_footer_credits.setText(
            '<a href="https://github.com/InfiniteLoop888/TodoList" '
            'style="color:{}; font-size:11px; text-decoration:none;">InfiniteLoop888</a>'.format(text_d)
        )
        self.translucent_opacity_value.setStyleSheet("color: {}".format(SiGlobal.siui.colors["TEXT_C"]))
        self.todo_font_px_input.setStyleSheet(
            """
            QLineEdit {{
                border: 1px solid {border};
                border-radius: 6px;
                padding: 4px 8px;
                background-color: {bg};
                color: {text};
            }}
            """.format(
                border=SiGlobal.siui.colors["BORDER_COLOR"],
                bg=SiGlobal.siui.colors["BACKGROUND_DARK_COLOR"],
                text=SiGlobal.siui.colors["TEXT_B"],
            )
        )
        self.translucent_opacity_slider.setStyleSheet(
            """
            QSlider::groove:horizontal {{
                border: 1px solid {border};
                height: 5px;
                border-radius: 2px;
                background: {bg};
            }}
            QSlider::sub-page:horizontal {{
                border-radius: 2px;
                background: {theme};
            }}
            QSlider::handle:horizontal {{
                width: 12px;
                margin: -4px 0;
                border-radius: 6px;
                border: 1px solid {border};
                background: {text};
            }}
            """.format(
                border=SiGlobal.siui.colors["BORDER_COLOR"],
                bg=SiGlobal.siui.colors["BACKGROUND_DARK_COLOR"],
                theme=SiGlobal.siui.colors["THEME"],
                text=SiGlobal.siui.colors["TEXT_B"],
            )
        )

    def _onTranslucentOpacityChanged(self, value):
        self.translucent_opacity_value.setText(f"{value}%")
        set_translucent_opacity(value)

    def _onTodoFontPxEditingFinished(self):
        text = self.todo_font_px_input.text().strip()
        try:
            px = int(text)
        except ValueError:
            self.todo_font_px_input.setText(str(todo_item_font_px()))
            return
        px = max(8, min(24, px))
        self.todo_font_px_input.setText(str(px))
        SiGlobal.todo_list.settings_parser.modify("TODO_ITEM_FONT_PX", px)
        SiGlobal.todo_list.settings_parser.write()
        apply_todo_item_font_setting()

    def showEvent(self, a0):
        super().showEvent(a0)
        self.setForceUseAnimations(True)
        if self.button_startup is not None:
            self.button_startup.blockSignals(True)
            self.button_startup.setChecked(is_startup_enabled())
            self.button_startup.blockSignals(False)


class CalendarWindow(QMainWindow):
    """
    独立的日历窗口
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowSystemMenuHint | Qt.WindowMinimizeButtonHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)
        
        self.setWindowIcon(self._createCalendarIcon())

        # 窗口周围留白，供阴影使用
        self.padding = 32
        
        self.container = QWidget(self)
        self.container.setMouseTracking(True)

        self.calendar_panel = CalendarPanel(self.container)
        self.calendar_panel.setForceUseAnimations(False)
        self.calendar_panel.setMouseTracking(True)
        self.calendar_panel.setCursor(Qt.ArrowCursor)
        
        # 覆写 panel 的 setTitle，添加关闭按钮
        header = self.calendar_panel.header()
        
        # 隐藏原来的折叠按钮（如果有的话）
        if hasattr(header, "button_unfold"):
            header.button_unfold.hide()
            
        self.maximize_btn = SiSimpleButton(self.calendar_panel)
        self.maximize_btn.resize(32, 32)
        self.maximize_btn.setHint("全屏")
        self.maximize_btn.clicked.connect(self._toggle_maximize)
        
        self.minimize_btn = SiSimpleButton(self.calendar_panel)
        self.minimize_btn.resize(32, 32)
        self.minimize_btn.setHint("最小化")
        self.minimize_btn.clicked.connect(self.showMinimized)
        
        self.close_btn = SiSimpleButton(self.calendar_panel)
        self.close_btn.resize(32, 32)
        self.close_btn.setHint("关闭")
        self.close_btn.clicked.connect(self.hide)
        
        header.addWidget(self.close_btn, "right")
        header.addWidget(self.maximize_btn, "right")
        header.addWidget(self.minimize_btn, "right")

        shadow = QGraphicsDropShadowEffect()
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 0)
        shadow.setBlurRadius(32)
        self.calendar_panel.setGraphicsEffect(shadow)

        # 拖拽与缩放变量
        self._dragging = False
        self._resizing = False
        self._resize_dir = ""
        self.anchor = QPoint()
        
        SiGlobal.siui.windows["CALENDAR_WINDOW"] = self

        # 默认大小
        panel_w = 560
        panel_h = 64 + 32 + 8 + 24 + 8 + (6 * 64 + 5 * 4) + 32
        self.resize(panel_w + 2 * self.padding, panel_h + 2 * self.padding)
        self._apply_saved_calendar_geometry()
        self.applyWindowOpacity()
        SiGlobal.siui.reloadAllWindowsStyleSheet()

        app = QApplication.instance()
        if app is not None:
            app.aboutToQuit.connect(self._persist_calendar_geometry)

    def _calendar_rect_on_any_screen(self, rect):
        app = QApplication.instance()
        if app is None:
            return False
        for screen in app.screens():
            if screen.availableGeometry().intersects(rect):
                return True
        return False

    def _apply_saved_calendar_geometry(self):
        opts = SiGlobal.todo_list.settings_parser.options
        x = opts.get("CALENDAR_X")
        y = opts.get("CALENDAR_Y")
        w = opts.get("CALENDAR_WIDTH")
        h = opts.get("CALENDAR_HEIGHT")
        maxed = bool(opts.get("CALENDAR_MAXIMIZED", False))

        min_w = 400 + 2 * 32
        min_h = 400 + 2 * 32

        if (
            isinstance(x, int)
            and isinstance(y, int)
            and isinstance(w, int)
            and isinstance(h, int)
            and w >= min_w
            and h >= min_h
        ):
            rect = QRect(x, y, w, h)
            if self._calendar_rect_on_any_screen(rect):
                self.setGeometry(rect)

        if maxed:
            self._is_maximized = True
            self.padding = 0
            self.calendar_panel.setGraphicsEffect(None)
            self.maximize_btn.setHint("恢复")
            self.maximize_btn.attachment().load(
                SiGlobal.siui.icons.get("fi-rr-compress", SiGlobal.siui.icons.get("fi-rr-picture"))
            )
            self.showMaximized()

    def _persist_calendar_geometry(self):
        parser = SiGlobal.todo_list.settings_parser
        if getattr(self, "_is_maximized", False):
            g = self.normalGeometry()
            parser.modify("CALENDAR_MAXIMIZED", True)
        else:
            g = self.geometry()
            parser.modify("CALENDAR_MAXIMIZED", False)
        parser.modify("CALENDAR_X", g.x())
        parser.modify("CALENDAR_Y", g.y())
        parser.modify("CALENDAR_WIDTH", g.width())
        parser.modify("CALENDAR_HEIGHT", g.height())
        parser.write()

    def hideEvent(self, event):
        self._persist_calendar_geometry()
        super().hideEvent(event)

    def closeEvent(self, event):
        self._persist_calendar_geometry()
        super().closeEvent(event)

    def _createCalendarIcon(self):
        try:
            svg_data = SiGlobal.siui.icons.get("fi-rr-calendar")
            if svg_data is None:
                svg_data = SiGlobal.siui.icons.get("fi-rr-menu-burger")

            renderer = QSvgRenderer(QByteArray(svg_data))
            if not renderer.isValid():
                return QIcon()

            size = QSize(64, 64)
            pixmap = QPixmap(size)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            renderer.render(painter)
            painter.end()
            return QIcon(pixmap)
        except Exception:
            return QIcon()
        
    def _toggle_maximize(self):
        if getattr(self, '_is_maximized', False):
            self._is_maximized = False
            self.padding = 32
            
            shadow = QGraphicsDropShadowEffect()
            shadow.setColor(QColor(0, 0, 0, 80))
            shadow.setOffset(0, 0)
            shadow.setBlurRadius(32)
            self.calendar_panel.setGraphicsEffect(shadow)
            
            self.showNormal()
            self.maximize_btn.setHint("全屏")
            self.maximize_btn.attachment().load(SiGlobal.siui.icons.get("fi-rr-expand", SiGlobal.siui.icons.get("fi-rr-picture")))
        else:
            self._is_maximized = True
            self.padding = 0
            
            self.calendar_panel.setGraphicsEffect(None)
            
            self.showMaximized()
            self.maximize_btn.setHint("恢复")
            self.maximize_btn.attachment().load(SiGlobal.siui.icons.get("fi-rr-compress", SiGlobal.siui.icons.get("fi-rr-picture")))
            
    def resizeEvent(self, event):
        super().resizeEvent(event)
        w, h = event.size().width(), event.size().height()
        self.container.resize(w, h)
        self.calendar_panel.resize(w - 2 * self.padding, h - 2 * self.padding)
        self.calendar_panel.move(self.padding, self.padding)
        
    def reloadStyleSheet(self):
        self.close_btn.attachment().load(SiGlobal.siui.icons["fi-rr-cross"])
        self.minimize_btn.attachment().load(SiGlobal.siui.icons.get("fi-rr-minus", SiGlobal.siui.icons.get("fi-rr-cross-small", SiGlobal.siui.icons["fi-rr-cross"])))
        if getattr(self, '_is_maximized', False):
            self.maximize_btn.attachment().load(SiGlobal.siui.icons.get("fi-rr-compress", SiGlobal.siui.icons.get("fi-rr-picture")))
        else:
            self.maximize_btn.attachment().load(SiGlobal.siui.icons.get("fi-rr-expand", SiGlobal.siui.icons.get("fi-rr-picture")))
        
    def applyWindowOpacity(self, enabled=None):
        options = SiGlobal.todo_list.settings_parser.options
        is_translucent = bool(options.get("TRANSLUCENT_MODE", False)) if enabled is None else bool(enabled)
        opacity_percent = int(options.get("TRANSLUCENT_OPACITY", 70))
        opacity_percent = max(10, min(95, opacity_percent))
        translucent_opacity = opacity_percent / 100.0
        self.setWindowOpacity(translucent_opacity if is_translucent else 1.0)
        
    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if event.button() == Qt.LeftButton:
            pos = event.pos()
            rect = self.rect()
            
            if getattr(self, '_is_maximized', False):
                return

            panel_x = self.padding
            panel_y = self.padding
            panel_r = self.width() - self.padding
            panel_b = self.height() - self.padding
            
            edge = 6
            self._resize_dir = ""
            
            if panel_x - edge <= pos.x() <= panel_r + edge and panel_y - edge <= pos.y() <= panel_b + edge:
                if abs(pos.x() - panel_x) <= edge: self._resize_dir += "L"
                elif abs(pos.x() - panel_r) <= edge: self._resize_dir += "R"
                
                if abs(pos.y() - panel_y) <= edge: self._resize_dir += "T"
                elif abs(pos.y() - panel_b) <= edge: self._resize_dir += "B"
            
            if self._resize_dir != "":
                self._resizing = True
                self._drag_start_pos = event.globalPos()
                self._drag_start_geometry = self.geometry()
                event.accept()
            elif panel_x <= pos.x() <= panel_r and panel_y <= pos.y() <= panel_y + self.calendar_panel.header().height():
                self._dragging = True
                self.anchor = event.pos()
                event.accept()

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        
        if not hasattr(self, '_resizing'): self._resizing = False
        if not hasattr(self, '_dragging'): self._dragging = False
        
        if not (event.buttons() & Qt.LeftButton):
            pos = event.pos()
            
            if getattr(self, '_is_maximized', False):
                self.setCursor(Qt.ArrowCursor)
                return
                
            panel_x = self.padding
            panel_y = self.padding
            panel_r = self.width() - self.padding
            panel_b = self.height() - self.padding
            
            edge = 6
            dir = ""
            
            if panel_x - edge <= pos.x() <= panel_r + edge and panel_y - edge <= pos.y() <= panel_b + edge:
                if abs(pos.x() - panel_x) <= edge: dir += "L"
                elif abs(pos.x() - panel_r) <= edge: dir += "R"
                
                if abs(pos.y() - panel_y) <= edge: dir += "T"
                elif abs(pos.y() - panel_b) <= edge: dir += "B"
            
            if dir in ("LT", "RB"): self.setCursor(Qt.SizeFDiagCursor)
            elif dir in ("RT", "LB"): self.setCursor(Qt.SizeBDiagCursor)
            elif dir in ("L", "R"): self.setCursor(Qt.SizeHorCursor)
            elif dir in ("T", "B"): self.setCursor(Qt.SizeVerCursor)
            else: self.setCursor(Qt.ArrowCursor)
            return

        if getattr(self, '_resizing', False):
            delta = event.globalPos() - self._drag_start_pos
            geom = self._drag_start_geometry
            x, y, w, h = geom.x(), geom.y(), geom.width(), geom.height()
            
            if "L" in self._resize_dir:
                w -= delta.x()
                x += delta.x()
            elif "R" in self._resize_dir:
                w += delta.x()
                
            if "T" in self._resize_dir:
                h -= delta.y()
                y += delta.y()
            elif "B" in self._resize_dir:
                h += delta.y()
                
            min_w = 400 + 2 * self.padding
            min_h = 400 + 2 * self.padding
            
            if w < min_w:
                if "L" in self._resize_dir: x -= (min_w - w)
                w = min_w
            if h < min_h:
                if "T" in self._resize_dir: y -= (min_h - h)
                h = min_h
                
            self.setGeometry(x, y, w, h)
            
        elif getattr(self, '_dragging', False):
            new_pos = event.pos() - self.anchor + self.frameGeometry().topLeft()
            self.move(new_pos)

    def mouseReleaseEvent(self, event):
        self._dragging = False
        self._resizing = False
        super().mouseReleaseEvent(event)

class ReminderNotificationWindow(QMainWindow):
    def __init__(self, todo_widget, todo_text, time_str):
        super().__init__()
        self.todo_widget = todo_widget
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(300, 110)

        bg = SiLabel(self)
        bg.resize(self.size())
        bg_color = SiGlobal.siui.colors["BACKGROUND_DARK_COLOR"]
        border_color = SiGlobal.siui.colors["BORDER_COLOR"]
        bg.setFixedStyleSheet(f"background-color: {bg_color}; border: 1px solid {border_color}; border-radius: 8px;")

        layout = QVBoxLayout(bg)
        layout.setContentsMargins(16, 12, 16, 12)

        top_layout = QHBoxLayout()
        dot = QLabel("●")
        dot.setStyleSheet("color: #ff4d4f; font-size: 16px;")
        
        # Ellide long text
        f = QFont(SiGlobal.siui.fonts["S_NORMAL"])
        f.setPointSize(10)
        f.setWeight(QFont.Bold)
        fm = QFontMetrics(f)
        elided_text = fm.elidedText(f"【待办】{todo_text}", Qt.ElideRight, 220)
        
        title = QLabel(elided_text)
        title.setStyleSheet(f"color: {SiGlobal.siui.colors['TEXT_B']}; font-size: 14px; font-weight: bold;")
        top_layout.addWidget(dot)
        top_layout.addWidget(title)
        top_layout.addStretch()
        layout.addLayout(top_layout)

        time_lbl = QLabel(f"🕒 {time_str}")
        time_lbl.setStyleSheet(f"color: {SiGlobal.siui.colors['TEXT_D']}; font-size: 12px; margin-left: 20px;")
        layout.addWidget(time_lbl)

        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(16, 0, 16, 0)
        btn_close = QPushButton("关闭", self)
        btn_delay = QPushButton("延时", self)
        
        btn_close.setStyleSheet(f"color: {SiGlobal.siui.colors['TEXT_C']}; border: none; background: transparent; font-size: 14px;")
        btn_delay.setStyleSheet(f"color: {SiGlobal.siui.colors['PANEL_THEME']}; border: none; background: transparent; font-size: 14px;")
        
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_delay.setCursor(Qt.PointingHandCursor)

        btn_close.clicked.connect(self._on_close)
        btn_delay.clicked.connect(self._on_delay)
        btn_layout.addWidget(btn_close)
        btn_layout.addWidget(btn_delay)
        layout.addLayout(btn_layout)

        self._move_to_bottom_right()
        
    def _move_to_bottom_right(self):
        screen = QApplication.primaryScreen()
        if screen:
            geom = screen.availableGeometry()
            self.move(geom.width() - self.width() - 24, geom.height() - self.height() - 24)

    def _on_close(self):
        if self.todo_widget:
            self.todo_widget.setReminder(None)
            if hasattr(self.todo_widget, "todo_panel"):
                self.todo_widget.todo_panel._syncCurrentListFromUI(save_to_disk=True)
        self.close()
        self.deleteLater()

    def _on_delay(self):
        if self.todo_widget:
            rem = getattr(self.todo_widget, "reminder_data", {})
            if rem:
                rem["timestamp"] += 1800 # Delay by 30 minutes
                self.todo_widget.setReminder(rem)
                if hasattr(self.todo_widget, "todo_panel"):
                    self.todo_widget.todo_panel._syncCurrentListFromUI(save_to_disk=True)
        self.close()
        self.deleteLater()

class TODOApplication(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 窗口周围留白，供阴影使用
        self.padding = 48
        self.extra_left_space = 112
        self.min_container_width = 420
        self.anchor = QPoint(self.x(), self.y())
        self.fixed_position = QPoint(0, 0)

        # 使用 Tool 窗口类型，仅在系统托盘展示，不在任务栏显示普通进程按钮
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)  # 设置窗口背景透明
        self._quitting = False
        self.opacity_normal = 1.0
        self._dragging_by_header = False

        # 初始化全局变量
        SiGlobal.todo_list.todo_list_unfold_state = True

        # 初始化工具提示窗口
        SiGlobal.siui.windows["TOOL_TIP"] = ToolTipWindow()
        SiGlobal.siui.windows["TOOL_TIP"].show()
        SiGlobal.siui.windows["TOOL_TIP"].hide_()
        SiGlobal.siui.windows["MAIN_WINDOW"] = self

        # 创建移动动画
        self.move_animation = SiExpAnimation(self)
        self.move_animation.setFactor(1 / 4)
        self.move_animation.setBias(1)
        self.move_animation.setCurrent([self.x(), self.y()])
        self.move_animation.ticked.connect(self._onMoveAnimationTicked)

        # 创建垂直容器
        self.container_v = SiDenseVContainer(self)
        self.container_v.setFixedWidth(500)
        self.container_v.move(self.extra_left_space, self.padding)
        self.container_v.setSpacing(0)
        self.container_v.setShrinking(True)
        self.container_v.setAlignCenter(True)

        # 构建界面
        # 头
        self.header_panel = AppHeaderPanel(self)
        self.header_panel.setFixedWidth(self.container_v.width() - 2 * self.padding)
        self.header_panel.setFixedHeight(48 + 12)

        # 设置面板
        self.settings_panel = SettingsPanel(self)
        self.settings_panel.setFixedWidth(self.container_v.width() - 2 * self.padding)
        self.settings_panel.adjustSize()

        self.settings_panel_placeholder = SiLabel(self)
        self.settings_panel_placeholder.setFixedHeight(12)
        self._onSettingsButtonToggled(False)

        # 待办列表面板（标题为当前清单名）
        self.todo_list_panel = TODOListPanel(self)
        self.todo_list_panel.setFixedWidth(self.container_v.width() - 2 * self.padding)
        self.todo_list_panel.attachSidebarHost(self)

        self.todo_list_panel_placeholder = SiLabel(self)
        self.todo_list_panel_placeholder.setFixedHeight(12)
        self._onShowTODOButtonToggled(True)

        # <- 添加到垂直容器
        self.container_v.addWidget(self.header_panel)
        self.container_v.addWidget(self.settings_panel)
        self.container_v.addWidget(self.settings_panel_placeholder)
        self.container_v.addWidget(self.todo_list_panel)
        self.container_v.addWidget(self.todo_list_panel_placeholder)

        # 绑定界面信号
        self.header_panel.unfold_button.toggled.connect(self._onShowTODOButtonToggled)
        self.header_panel.settings_button.toggled.connect(self._onSettingsButtonToggled)
        self.header_panel.calendar_button.clicked.connect(self._onCalendarButtonClicked)

        self.settings_panel.resized.connect(self._onTODOWindowResized)
        self.todo_list_panel.resized.connect(self._onTODOWindowResized)
        self.settings_panel.button_use_dark_mode.toggled.connect(lambda _: self._applyTrayMenuStyle())
        if self.settings_panel.button_startup is not None:
            self.settings_panel.button_startup.toggled.connect(self._onStartupToggledFromSettings)

        self._initTrayIcon()

        self.todo_list_panel.todoAmountChanged.connect(self._onTODOAmountChanged)

        shadow = QGraphicsDropShadowEffect()
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 0)
        shadow.setBlurRadius(48)
        # 在 Win 分层窗口上给顶层窗口直接加阴影会触发 UpdateLayeredWindowIndirect 报错，
        # 改为给内容容器加阴影，视觉保持一致且更稳定。
        self.container_v.setGraphicsEffect(shadow)

        self.resize(500 + self.extra_left_space, 800)
        SiGlobal.siui.reloadAllWindowsStyleSheet()

        # 读取 todos.ini 清单数据
        self.todo_list_panel.loadLists(SiGlobal.todo_list.todos_parser.lists)
        self._moveToStartupPosition()
        self.applyWindowOpacity()

        # Reminder Timer
        self.reminder_timer = QTimer(self)
        self.reminder_timer.timeout.connect(self._check_reminders)
        self.reminder_timer.start(10000) # Check every 10 seconds
        self.active_reminders = []

    def _check_reminders(self):
        # 过滤掉已经被删除的C++对象
        valid_reminders = []
        for p in self.active_reminders:
            try:
                if p.isVisible():
                    valid_reminders.append(p)
            except RuntimeError:
                pass
        self.active_reminders = valid_reminders

        now = int(datetime.now().timestamp())
        for widget in self.todo_list_panel._todoWidgets():
            rem = getattr(widget, "reminder_data", None)
            if rem and not widget.check_box.isChecked():
                ts = rem.get("timestamp", 0)
                if 0 < ts <= now:
                    # Clear it so it doesn't trigger again, or wait for user to close/delay
                    # We'll just show the popup and the popup will handle clearing or delaying
                    if not getattr(widget, "_popup_shown", False):
                        widget._popup_shown = True
                        t_str = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
                        popup = ReminderNotificationWindow(widget, widget.text_label.text(), t_str)
                        popup.show()
                        self.active_reminders.append(popup)

    def _createAppIcon(self):
        try:
            svg_data = SiGlobal.siui.icons.get("fi-rr-list-check")
            if svg_data is None:
                raise KeyError("missing fi-rr-list-check icon")

            renderer = QSvgRenderer(QByteArray(svg_data))
            if not renderer.isValid():
                raise ValueError("invalid svg icon data")

            size = QSize(64, 64)
            pixmap = QPixmap(size)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            renderer.render(painter)
            painter.end()
            return QIcon(pixmap)
        except Exception:
            # 回退到系统默认图标，避免图标资源异常影响启动
            return self.style().standardIcon(QStyle.SP_FileDialogDetailedView)

    def _initTrayIcon(self):
        app_icon = self._createAppIcon()
        self.setWindowIcon(app_icon)
        QApplication.instance().setWindowIcon(app_icon)

        if not QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = None
            return

        self.tray_icon = QSystemTrayIcon(app_icon, self)
        self.tray_icon.setToolTip("My TODOs")
        self.tray_menu = QMenu(self)

        self.action_show = QAction(themed_icon_from_svg_key("fi-rr-list-check", menu_left_pad=8), "显示窗口", self)
        self.action_show.triggered.connect(self._showFromTray)
        self.tray_menu.addAction(self.action_show)

        self.action_minimize = QAction("最小化", self)
        self.action_minimize.triggered.connect(self.showMinimized)
        self.tray_menu.addAction(self.action_minimize)

        self.action_startup = None
        if startup_supported():
            self.action_startup = QAction("开机自启动", self)
            self.action_startup.setCheckable(True)
            self.action_startup.blockSignals(True)
            self.action_startup.setChecked(is_startup_enabled())
            self.action_startup.blockSignals(False)
            self.action_startup.toggled.connect(self._onStartupToggledFromTray)
            self.tray_menu.addAction(self.action_startup)
            self.tray_menu.aboutToShow.connect(self._refreshTrayStartupAction)

        self.tray_menu.addSeparator()

        self.action_quit = QAction(themed_icon_from_svg_key("fi-rr-cross", menu_left_pad=8), "退出", self)
        self.action_quit.triggered.connect(self._quitFromTray)
        self.tray_menu.addAction(self.action_quit)

        self._applyTrayMenuStyle()
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.activated.connect(self._onTrayActivated)
        self.tray_icon.show()

    def _applyTrayMenuStyle(self):
        if getattr(self, "tray_menu", None) is None:
            return
        apply_popup_menu_appearance(self.tray_menu)

    def _refreshTrayStartupAction(self):
        if getattr(self, "action_startup", None) is None:
            return
        self.action_startup.blockSignals(True)
        self.action_startup.setChecked(is_startup_enabled())
        self.action_startup.blockSignals(False)

    def _onStartupToggledFromTray(self, checked):
        set_startup_enabled(bool(checked))
        sp = getattr(self.settings_panel, "button_startup", None)
        if sp is not None:
            sp.blockSignals(True)
            sp.setChecked(bool(checked))
            sp.blockSignals(False)

    def _onStartupToggledFromSettings(self, enabled):
        set_startup_enabled(bool(enabled))
        if getattr(self, "action_startup", None) is not None:
            self.action_startup.blockSignals(True)
            self.action_startup.setChecked(bool(enabled))
            self.action_startup.blockSignals(False)

    def _showFromTray(self):
        self.showNormal()
        self.activateWindow()
        self.raise_()

    def applyWindowOpacity(self, enabled=None):
        options = SiGlobal.todo_list.settings_parser.options
        is_translucent = bool(options.get("TRANSLUCENT_MODE", False)) if enabled is None else bool(enabled)
        opacity_percent = int(options.get("TRANSLUCENT_OPACITY", 70))
        opacity_percent = max(10, min(95, opacity_percent))
        translucent_opacity = opacity_percent / 100.0
        self.setWindowOpacity(translucent_opacity if is_translucent else self.opacity_normal)

    def _moveToTopRight(self):
        screen = QApplication.primaryScreen()
        if screen is None:
            return

        geometry = screen.availableGeometry()
        margin = 16
        x = geometry.x() + geometry.width() - self.width() - margin
        y = geometry.y() + margin
        self.move(x, y)
        self.fixed_position = QPoint(x, y)

    def _moveToStartupPosition(self):
        options = SiGlobal.todo_list.settings_parser.options
        has_custom_position = bool(options.get("HAS_CUSTOM_POSITION", False))
        saved_x = options.get("FIXED_POSITION_X")
        saved_y = options.get("FIXED_POSITION_Y")

        if has_custom_position and isinstance(saved_x, int) and isinstance(saved_y, int):
            screen = QApplication.primaryScreen()
            if screen is not None:
                geometry = screen.availableGeometry()
                if geometry.contains(saved_x, saved_y):
                    self.move(saved_x, saved_y)
                    self.fixed_position = QPoint(saved_x, saved_y)
                    return

        self._moveToTopRight()

    def _quitFromTray(self):
        self._quitting = True
        self.close()

    def _onTrayActivated(self, reason):
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self._showFromTray()


    def adjustSize(self):
        h = (self.header_panel.height() + 12 +
             self.settings_panel.height() + 12 +
             self.todo_list_panel.height() +
             2 * self.padding)
        self.resize(self.width(), h)
        self.container_v.adjustSize()

    def _apply_container_width(self, container_width):
        container_width = max(self.min_container_width, int(container_width))
        panel_width = max(200, container_width - 2 * self.padding)

        self.container_v.setFixedWidth(container_width)
        self.header_panel.setFixedWidth(panel_width)
        self.settings_panel.setFixedWidth(panel_width)
        self.todo_list_panel.setFixedWidth(panel_width)

        if self.header_panel.settings_button.isChecked():
            self.settings_panel.adjustSize()
        else:
            self.settings_panel.resize(panel_width, 0)

        if self.header_panel.unfold_button.isChecked():
            self.todo_list_panel.adjustSize()
        else:
            self.todo_list_panel.resize(panel_width, 0)

        self.container_v.adjustSize()
        self.resize(container_width + self.extra_left_space, self.height())
        self._update_resize_handles()

    def _update_resize_handles(self):
        return

    def resizeEvent(self, a0):
        super().resizeEvent(a0)
        extra_left = getattr(self, "extra_left_space", 0)
        self.container_v.move(extra_left, self.padding)

    def showEvent(self, a0):
        super().showEvent(a0)

    def _onTODOWindowResized(self, size):
        w, h = size
        self.adjustSize()

    def _onShowTODOButtonToggled(self, state):
        if state is True:
            self.todo_list_panel_placeholder.setFixedHeight(12)
            self.todo_list_panel.adjustSize()
            self.todo_list_panel.setSidebarVisible(True)
        else:
            self.todo_list_panel_placeholder.setFixedHeight(0)
            self.todo_list_panel.resize(self.todo_list_panel.width(), 0)
            self.todo_list_panel.setSidebarVisible(False)

    def _onSettingsButtonToggled(self, state):
        if state is True:
            self.settings_panel_placeholder.setFixedHeight(12)
            self.settings_panel.adjustSize()
        else:
            self.settings_panel_placeholder.setFixedHeight(0)
            self.settings_panel.resize(self.settings_panel.width(), 0)

    def _onCalendarButtonClicked(self):
        # 确保不会重复创建
        if "CALENDAR_WINDOW" not in SiGlobal.siui.windows:
            CalendarWindow().show()
        elif not SiGlobal.siui.windows["CALENDAR_WINDOW"].isVisible():
            SiGlobal.siui.windows["CALENDAR_WINDOW"].show()
        else:
            SiGlobal.siui.windows["CALENDAR_WINDOW"].hide()

    def _onTODOAmountChanged(self, amount):
        if amount == 0:
            self.header_panel.unfold_button.attachment().setText("没有待办")
        else:
            self.header_panel.unfold_button.attachment().setText(f"{amount}个待办事项")
        self.header_panel.unfold_button.adjustSize()

    def moveTo(self, x, y):
        self.move_animation.setTarget([x, y])
        self.move_animation.try_to_start()

    def moveEvent(self, a0):
        super().moveEvent(a0)
        x, y = a0.pos().x(), a0.pos().y()
        self.move_animation.setCurrent([x, y])

    def _onMoveAnimationTicked(self, pos):
        self.move(int(pos[0]), int(pos[1]))
        if SiGlobal.todo_list.position_locked is False:
            self.fixed_position = self.pos()

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        top_drag_height = self.padding + self.header_panel.height()
        if event.button() == Qt.LeftButton and 0 <= event.pos().y() <= top_drag_height:
            self._dragging_by_header = True
            self.anchor = event.pos()
            event.accept()
        else:
            self._dragging_by_header = False

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        if self._dragging_by_header is False:
            return
        if not (event.buttons() & Qt.LeftButton):
            return

        new_pos = event.pos() - self.anchor + self.frameGeometry().topLeft()
        x, y = new_pos.x(), new_pos.y()

        self.moveTo(x, y)

    def mouseReleaseEvent(self, a0):
        self._dragging_by_header = False
        if SiGlobal.todo_list.position_locked is True:
            self.moveTo(self.fixed_position.x(), self.fixed_position.y())

    def eventFilter(self, obj, event):
        return super().eventFilter(obj, event)

    def closeEvent(self, a0):
        if getattr(self, "tray_icon", None) is not None:
            self.tray_icon.hide()

        super().closeEvent(a0)

        # 获取当前清单数据，并写入 todos.ini
        todo_lists = self.todo_list_panel.exportLists()
        SiGlobal.todo_list.todos_parser.lists = todo_lists
        SiGlobal.todo_list.todos_parser.todos = list(next(iter(todo_lists.values()))) if todo_lists else []
        SiGlobal.todo_list.todos_parser.write()

        # 写入设置到 options.ini
        SiGlobal.todo_list.settings_parser.modify("HAS_CUSTOM_POSITION", True)
        SiGlobal.todo_list.settings_parser.modify("FIXED_POSITION_X", self.fixed_position.x())
        SiGlobal.todo_list.settings_parser.modify("FIXED_POSITION_Y", self.fixed_position.y())
        SiGlobal.todo_list.settings_parser.write()

        SiGlobal.siui.windows["TOOL_TIP"].close()
        QCoreApplication.quit()
