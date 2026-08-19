import sys
import os
import json
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
                               QLineEdit, QLabel, QFileDialog, QStatusBar, QCheckBox, QMessageBox,
                               QComboBox, QGraphicsDropShadowEffect, QFrame)
from PySide6.QtCore import Qt, QSize, QTimer, QRectF
from PySide6.QtGui import QColor, QFont, QFontMetrics, QIcon, QPixmap, QPainter, QPen, QMouseEvent

import LCRename

THEMES = {
    "Light": {
        "bg_base": "#D8DCE3",      # Silver metallic chassis
        "bg_surface": "#E5E8ED",   # Lighter silver for buttons and table
        "border": "#A5B0BC",       # Darker metallic grooves
        "text_main": "#111827",
        "text_muted": "#4B5563",
        "accent": "#3B82F6",       # Blue Power LED
        "accent_hover": "#2563EB",
        "success": "#22C55E",      # Green Signal LED
        "danger": "#EF4444",       # Red +48V LED
        "lcd_text": "#1A2B4C",
        "lcd_bg": "#A3B8E1"
    },
    "Dark": {
        "bg_base": "#1F2937",
        "bg_surface": "#111827",
        "border": "#374151",
        "text_main": "#F9FAFB",
        "text_muted": "#9CA3AF",
        "accent": "#3B82F6",       # Blue Power LED
        "accent_hover": "#60A5FA",
        "success": "#22C55E",      # Green Signal LED
        "danger": "#EF4444",       # Red +48V LED
        "lcd_text": "#A3B8E1",
        "lcd_bg": "#1A2B4C"
    }
}

def apply_drop_shadow(widget):
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(15)
    shadow.setOffset(0, 4)
    shadow.setColor(QColor(0, 0, 0, 80))
    widget.setGraphicsEffect(shadow)

class IdeaButton(QPushButton):
    def __init__(self, color_hex, parent=None):
        super().__init__(parent)
        self.color_hex = color_hex
        self.setFixedSize(32, 32)
        self.setCursor(Qt.PointingHandCursor)

    def set_icon_color(self, color_hex):
        self.color_hex = color_hex
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        center_x = self.width() / 2.0
        center_y = self.height() / 2.0
        
        # Draw Light Rays (Glowing Yellow)
        ray_color = QColor("#FBBF24")
        ray_pen = QPen(ray_color)
        ray_pen.setWidth(2)
        ray_pen.setCapStyle(Qt.RoundCap)
        painter.setPen(ray_pen)
        
        # Rays
        painter.drawLine(center_x, center_y - 12, center_x, center_y - 9)
        painter.drawLine(center_x - 8, center_y - 10, center_x - 6, center_y - 8)
        painter.drawLine(center_x + 8, center_y - 10, center_x + 6, center_y - 8)
        painter.drawLine(center_x - 11, center_y - 4, center_x - 8, center_y - 4)
        painter.drawLine(center_x + 11, center_y - 4, center_x + 8, center_y - 4)
        
        # Bulb glass (Glowing Yellow)
        painter.setBrush(ray_color)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(center_x - 6, center_y - 7, 12, 12)
        
        # Bulb base (Theme text color for contrast)
        base_color = QColor(self.color_hex)
        painter.setBrush(base_color)
        painter.drawRect(center_x - 4, center_y + 3, 8, 6)
        
        # Draw lines inside the base to make it look like a screw thread
        painter.setPen(QPen(QColor(self.palette().window().color()), 1))
        painter.drawLine(center_x - 4, center_y + 5, center_x + 4, center_y + 5)
        painter.drawLine(center_x - 4, center_y + 7, center_x + 4, center_y + 7)
        
        # Draw the little bottom contact point
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(center_x - 2, center_y + 8, 4, 3)
        
        painter.end()

class CustomTitleBar(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(15, 8, 15, 8)
        
        self.title = QLabel("LCRename - Liquid Channel Replica Modifier")
        self.title.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        self.btn_min = QPushButton("—")
        self.btn_min.setFixedSize(30, 30)
        self.btn_min.clicked.connect(self.parent.showMinimized)
        self.btn_min.setProperty("cssClass", "titlebtn")
        
        self.btn_close = QPushButton("✕")
        self.btn_close.setFixedSize(30, 30)
        self.btn_close.clicked.connect(self.parent.close)
        self.btn_close.setProperty("cssClass", "titlebtn closebtn")
        
        self.layout.addWidget(self.title)
        self.layout.addStretch()
        self.layout.addWidget(self.btn_min)
        self.layout.addWidget(self.btn_close)
        
        self.start_pos = None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.start_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.start_pos:
            delta = event.globalPosition().toPoint() - self.start_pos
            self.parent.move(self.parent.pos() + delta)
            self.start_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self.start_pos = None

class ReplicaEditorGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.resize(1350, 750)
        
        self.export_folder = ""
        self.mappings = {}
        self.all_selected = True
        
        self.load_mappings()
        self.setup_ui()
        self.apply_theme("Light")

    def load_mappings(self):
        mapping_file = "hardware_mapping.json"
        if os.path.exists(mapping_file):
            try:
                with open(mapping_file, 'r', encoding='utf-8') as f:
                    self.mappings = json.load(f)
            except Exception as e:
                pass

    def setup_ui(self):
        # Set a consistent global font
        global_font = QFont("Consolas", 11)
        QApplication.setFont(global_font)

        main_widget = QWidget()
        main_widget.setObjectName("main_widget")
        self.setCentralWidget(main_widget)
        
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.title_bar = CustomTitleBar(self)
        layout.addWidget(self.title_bar)
        
        inner_widget = QWidget()
        inner_widget.setObjectName("inner_widget")
        inner_layout = QVBoxLayout(inner_widget)
        inner_layout.setContentsMargins(15, 10, 15, 15)
        layout.addWidget(inner_widget)

        toolbar = QHBoxLayout()
        
        self.btn_add_files = QPushButton("Add Files")
        self.btn_add_files.clicked.connect(self.add_files)
        apply_drop_shadow(self.btn_add_files)

        self.btn_select_all = QPushButton("Select All")
        self.btn_select_all.clicked.connect(self.toggle_select_all)
        apply_drop_shadow(self.btn_select_all)

        self.btn_set_export = QPushButton("Set Export Folder...")
        self.btn_set_export.clicked.connect(self.set_export_folder)
        apply_drop_shadow(self.btn_set_export)

        self.lbl_export_folder = QLabel("Export Folder: Not set")
        self.lbl_export_folder.setStyleSheet("font-weight: bold;")

        self.theme_selector = QComboBox()
        self.theme_selector.addItems(list(THEMES.keys()))
        self.theme_selector.currentTextChanged.connect(self.apply_theme)
        apply_drop_shadow(self.theme_selector)

        self.btn_apply = QPushButton("Apply Changes")
        self.btn_apply.setProperty("cssClass", "primary")
        self.btn_apply.clicked.connect(self.apply_changes)
        apply_drop_shadow(self.btn_apply)

        toolbar.addWidget(self.btn_add_files)
        toolbar.addWidget(self.btn_select_all)
        toolbar.addWidget(self.btn_set_export)
        toolbar.addWidget(self.lbl_export_folder)
        toolbar.addStretch()
        toolbar.addWidget(QLabel("Theme:"))
        toolbar.addWidget(self.theme_selector)
        toolbar.addWidget(self.btn_apply)
        inner_layout.addLayout(toolbar)

        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels([
            "Select", "Source File", "Old Name", "New Name (12)", 
            "Old Description", "New Description (32)", "Suggest", "Status"
        ])
        
        header = self.table.horizontalHeader()
        for i in range(self.table.columnCount()):
            header.setSectionResizeMode(i, QHeaderView.Interactive)
            
        v_header = self.table.verticalHeader()
        v_header.setDefaultSectionSize(42)
        v_header.setSectionResizeMode(QHeaderView.Fixed)
        
        fm = QFontMetrics(global_font)
        char_width = fm.horizontalAdvance("X")
        width_12 = (char_width * 12) + 32
        width_32 = (char_width * 32) + 32
        
        self.table.setColumnWidth(0, 65)
        self.table.setColumnWidth(1, 200)
        self.table.setColumnWidth(2, width_12)
        self.table.setColumnWidth(3, width_12)
        self.table.setColumnWidth(4, width_32)
        self.table.setColumnWidth(5, width_32)
        self.table.setColumnWidth(6, 85)
        self.table.setColumnWidth(7, 100)
        
        apply_drop_shadow(self.table)
        inner_layout.addWidget(self.table)

        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("Ready. Hardware database loaded.")

    def apply_theme(self, theme_name):
        self.current_theme = theme_name
        theme = THEMES.get(theme_name, THEMES["Light"])
        font_family = "Consolas, Courier New, monospace"
        
        self.setStyleSheet(f"""
            * {{
                font-family: {font_family};
            }}
            QWidget#main_widget, QWidget#inner_widget {{
                background-color: {theme['bg_base']};
            }}
            QLabel {{
                color: {theme['text_main']};
            }}
            QPushButton {{
                background-color: {theme['bg_surface']};
                border: 1px solid {theme['border']};
                padding: 6px 14px;
                border-radius: 4px;
                color: {theme['text_main']};
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {theme['accent']};
                color: {theme['bg_base']};
                border: 1px solid {theme['accent']};
            }}
            QPushButton[cssClass="primary"] {{
                background-color: {theme['success']};
                color: #FFFFFF;
                font-weight: bold;
                border: none;
            }}
            QPushButton[cssClass="primary"]:hover {{
                background-color: {theme['success']};
                border: 2px solid {theme['bg_base']};
            }}
            QPushButton[cssClass~="titlebtn"] {{
                background-color: transparent;
                border: none;
                border-radius: 4px;
                padding: 0;
            }}
            QPushButton[cssClass~="titlebtn"]:hover {{
                background-color: {theme['border']};
                color: {theme['text_main']};
            }}
            QPushButton[cssClass~="closebtn"]:hover {{
                background-color: {theme['danger']};
                color: white;
            }}
            
            QComboBox {{
                background-color: {theme['bg_surface']};
                border: 1px solid {theme['border']};
                padding: 6px 12px;
                border-radius: 4px;
                color: {theme['text_main']};
                min-width: 150px;
            }}
            QComboBox::drop-down {{
                border-left: 1px solid {theme['border']};
                width: 24px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {theme['bg_surface']};
                border: 1px solid {theme['border']};
                color: {theme['text_main']};
                selection-background-color: {theme['accent']};
                selection-color: {theme['bg_base']};
            }}
            
            QTableWidget {{
                background-color: {theme['bg_surface']};
                gridline-color: {theme['border']};
                border: 1px solid {theme['border']};
                color: {theme['text_main']};
                border-radius: 4px;
            }}
            QTableWidget::item:hover {{
                background-color: {theme['border']};
            }}
            QTableWidget::item:selected {{
                background-color: {theme['accent']};
                color: {theme['bg_base']};
            }}
            QHeaderView {{
                background-color: {theme['bg_surface']};
            }}
            QTableCornerButton::section {{
                background-color: {theme['bg_surface']};
                border: none;
            }}
            QHeaderView::section {{
                background-color: {theme['bg_surface']};
                color: {theme['text_muted']};
                padding: 8px;
                border: none;
                border-bottom: 2px solid {theme['border']};
                border-right: 1px solid {theme['border']};
                font-weight: bold;
            }}
            QLineEdit {{
                background-color: {theme['lcd_bg']};
                border: 1px solid {theme['border']};
                color: {theme['lcd_text']};
                padding: 4px 8px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
                letter-spacing: 1px;
            }}
            QLineEdit:focus {{
                border: 2px solid {theme['accent']};
            }}
            QStatusBar {{
                color: {theme['text_muted']};
                background: {theme['bg_base']};
                padding-left: 10px;
                border-top: 1px solid {theme['border']};
            }}
            
            QScrollBar:vertical {{
                border: none;
                background: {theme['bg_surface']};
                width: 12px;
                border-radius: 6px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {theme['border']};
                min-height: 20px;
                border-radius: 6px;
                margin: 2px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {theme['accent']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
            
            QScrollBar:horizontal {{
                border: none;
                background: {theme['bg_surface']};
                height: 12px;
                border-radius: 6px;
                margin: 0px;
            }}
            QScrollBar::handle:horizontal {{
                background: {theme['border']};
                min-width: 20px;
                border-radius: 6px;
                margin: 2px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background: {theme['accent']};
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0px; }}
        """)
        self.lbl_export_folder.setStyleSheet(f"color: {theme['text_muted']}; font-weight: bold;")
        self.title_bar.setStyleSheet(f"QWidget {{ background-color: {theme['bg_surface']}; }}")
        self.title_bar.title.setStyleSheet(f"color: {theme['text_main']}; font-weight: bold; font-size: 14px; background-color: transparent;")
        
        for row in range(self.table.rowCount()):
            sugg_container = self.table.cellWidget(row, 6)
            if sugg_container:
                btn_suggest = sugg_container.findChild(IdeaButton)
                if btn_suggest:
                    btn_suggest.setStyleSheet(f"""
                        QPushButton {{
                            background-color: {theme['bg_base']}; 
                            border: 1px solid {theme['border']}; 
                            border-radius: 4px;
                        }}
                        QPushButton:hover {{
                            background-color: {theme['accent']};
                        }}
                    """)
                    btn_suggest.set_icon_color(theme['text_main'])
            
            item_oname = self.table.item(row, 2)
            item_odesc = self.table.item(row, 4)
            if item_oname:
                item_oname.setForeground(QColor(theme['lcd_text']))
            if item_odesc:
                item_odesc.setForeground(QColor(theme['lcd_text']))

    def toggle_select_all(self):
        self.all_selected = not self.all_selected
        for row in range(self.table.rowCount()):
            chk_widget = self.table.cellWidget(row, 0)
            if chk_widget:
                chk = chk_widget.findChild(QCheckBox)
                if chk:
                    chk.setChecked(self.all_selected)
        self.btn_select_all.setText("Deselect All" if self.all_selected else "Select All")

    def get_suggestion(self, old_name):
        clean_name = old_name.strip()
        match = self.mappings.get(clean_name)
        if not match:
            for k, v in self.mappings.items():
                if k.lower() == clean_name.lower():
                    match = v
                    break

        if match:
            hardware = match.get("hardware", "")
            base_model = hardware.split('*')[0].split('(')[0].strip()
            suggested_name = base_model[:12]
            
            desc_part = hardware.replace(base_model, "").replace('*', '').strip()
            if not desc_part:
                desc_part = "Factory Emulation"
                
            suggested_desc = desc_part[:32].strip()
            return suggested_name, suggested_desc
            
        return None, None

    def apply_suggestion(self, row, suggested_name, suggested_desc, btn_suggest):
        name_edit = self.table.cellWidget(row, 3)
        desc_edit = self.table.cellWidget(row, 5)
        
        if name_edit and suggested_name:
            name_edit.setText(suggested_name)
        if desc_edit and suggested_desc:
            desc_edit.setText(suggested_desc)

    def extract_metadata(self, filepath):
        try:
            with open(filepath, 'rb') as f:
                data = bytearray(f.read())
            LCRename.unobfuscate(data)
            old_name = data[0x0208:0x0218].split(b'\x00')[0].decode('utf-8', errors='ignore').strip()
            old_desc = data[0x03DC:0x03FC].split(b'\x00')[0].decode('utf-8', errors='ignore').strip()
            return old_name, old_desc
        except Exception as e:
            return "Error", str(e)

    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Replica Files", "", "Replica Files (*.lqm *.lqc);;All Files (*)")
        if not files: return
        
        theme = THEMES.get(self.current_theme, THEMES["Light"])

        for fpath in files:
            row = self.table.rowCount()
            self.table.insertRow(row)

            chk = QCheckBox()
            chk.setChecked(True)
            chk_widget = QWidget()
            l = QHBoxLayout(chk_widget)
            l.addWidget(chk)
            l.setAlignment(Qt.AlignCenter)
            l.setContentsMargins(0,0,0,0)
            self.table.setCellWidget(row, 0, chk_widget)

            fname = os.path.basename(fpath)
            item_file = QTableWidgetItem(fname)
            item_file.setData(Qt.UserRole, fpath)
            item_file.setFlags(item_file.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 1, item_file)

            old_name, old_desc = self.extract_metadata(fpath)

            item_oname = QTableWidgetItem(old_name)
            item_oname.setFlags(item_oname.flags() & ~Qt.ItemIsEditable)
            item_oname.setForeground(QColor(theme['lcd_text']))
            self.table.setItem(row, 2, item_oname)

            edit_name = QLineEdit(old_name)
            edit_name.setMaxLength(12)
            self.table.setCellWidget(row, 3, edit_name)

            item_odesc = QTableWidgetItem(old_desc)
            item_odesc.setFlags(item_odesc.flags() & ~Qt.ItemIsEditable)
            item_odesc.setForeground(QColor(theme['lcd_text']))
            self.table.setItem(row, 4, item_odesc)

            edit_desc = QLineEdit(old_desc)
            edit_desc.setMaxLength(32)
            self.table.setCellWidget(row, 5, edit_desc)

            suggested_name, suggested_desc = self.get_suggestion(old_name)
            if suggested_name:
                btn_suggest = IdeaButton(theme['text_main'])
                btn_suggest.setToolTip(f"Hardware Match Found!\nName: {suggested_name}\nDesc: {suggested_desc}")
                btn_suggest.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {theme['bg_base']}; 
                        border: 1px solid {theme['border']}; 
                        border-radius: 4px;
                    }}
                    QPushButton:hover {{
                        background-color: {theme['accent']};
                    }}
                """)
                btn_suggest.clicked.connect(lambda checked=False, r=row, n=suggested_name, d=suggested_desc, b=btn_suggest: self.apply_suggestion(r, n, d, b))
                
                btn_container = QWidget()
                btn_layout = QHBoxLayout(btn_container)
                btn_layout.addWidget(btn_suggest)
                btn_layout.setAlignment(Qt.AlignCenter)
                btn_layout.setContentsMargins(0,0,0,0)
                self.table.setCellWidget(row, 6, btn_container)
            else:
                item_nosugg = QTableWidgetItem(" - ")
                item_nosugg.setTextAlignment(Qt.AlignCenter)
                item_nosugg.setFlags(item_nosugg.flags() & ~Qt.ItemIsEditable)
                item_nosugg.setForeground(QColor("#64748b"))
                self.table.setItem(row, 6, item_nosugg)

            item_status = QTableWidgetItem("Pending")
            item_status.setFlags(item_status.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 7, item_status)
            
        self.status.showMessage(f"Loaded {len(files)} files.")

    def set_export_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Export Folder")
        if folder:
            self.export_folder = folder
            self.lbl_export_folder.setText(f"Export Folder: {folder}")
            self.status.showMessage(f"Export folder set to: {folder}")

    def apply_changes(self):
        if not self.export_folder:
            QMessageBox.warning(self, "No Export Folder", "Please select an export folder first!\n\nThis ensures your original files remain untouched.")
            return

        success_count = 0
        error_count = 0
        theme = THEMES.get(self.current_theme, THEMES["Light"])
        
        for row in range(self.table.rowCount()):
            chk_widget = self.table.cellWidget(row, 0)
            if not chk_widget: continue
            chk = chk_widget.findChild(QCheckBox)
            if not chk.isChecked(): continue

            in_file = self.table.item(row, 1).data(Qt.UserRole)
            filename = self.table.item(row, 1).text()
            out_file = os.path.join(self.export_folder, filename)
            
            new_name = self.table.cellWidget(row, 3).text()
            new_desc = self.table.cellWidget(row, 5).text()

            try:
                LCRename.rename_replica(in_file, out_file, new_name, new_desc)
                item_status = self.table.item(row, 7)
                item_status.setText("Success ✓")
                item_status.setForeground(QColor(theme['success']))
                success_count += 1
            except Exception as e:
                item_status = self.table.item(row, 7)
                item_status.setText("Error")
                item_status.setForeground(QColor(theme['danger']))
                item_status.setToolTip(str(e))
                error_count += 1

        msg = f"Processing Complete!\n\nSuccessfully exported: {success_count} files"
        if error_count > 0:
            msg += f"\nErrors encountered: {error_count} files"
            
        self.status.showMessage(f"Processed {success_count} files successfully.")
        QMessageBox.information(self, "Done", msg)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ReplicaEditorGUI()
    window.show()
    sys.exit(app.exec())
