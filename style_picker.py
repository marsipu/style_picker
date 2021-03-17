import re
from functools import partial
from os.path import join

import qdarkstyle
from PyQt5.QtGui import QColor, QPixmap
from PyQt5.QtWidgets import (QApplication, QColorDialog, QDialog, QFileDialog,
                             QGridLayout, QHBoxLayout, QLabel, QMainWindow,
                             QPushButton, QSizePolicy, QTextEdit, QVBoxLayout, QWidget)
from mne import read_source_estimate
from mne.datasets.sample import sample

from base_widgets import EditList

stylable_widgets = ['QAbstractScrollArea', 'QCheckBox', 'QColumnView', 'QComboBox',
                    'QDateEdit', 'QDateTimeEdit', 'QDialog', 'QDialogButtonBox', 'QDockWidget',
                    'QDoubleSpinBox', 'QFrame', 'QGroupBox', 'QHeaderView', 'QLabel', 'QLineEdit',
                    'QListView', 'QListWidget', 'QMainWindow', 'QMenu', 'QMenuBar', 'QMessageBox',
                    'QProgressBar', 'QPushButton', 'QRadioButton', 'QScrollBar', 'QSizeGrip',
                    'QSlider', 'QSpinBox', 'QSplitter', 'QStatusBar', 'QTabBar', 'QTabWidget',
                    'QTableView', 'QTableWidget', 'QTextEdit', 'QTimeEdit', 'QToolBar', 'QToolButton',
                    'QToolBox', 'QToolTip', 'QTreeView', 'QTreeWidget', 'QWidget']

class QSSViewer(QDialog):
    def __init__(self, main_win):
        super().__init__(main_win)
        self.mw = main_win

        self.init_ui()
        self.open()

    def init_ui(self):
        layout = QVBoxLayout()

        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setText(self.mw.stylesheet)
        layout.addWidget(text_edit)

        close_bt = QPushButton('Close')
        close_bt.clicked.connect(self.close)
        layout.addWidget(close_bt)

        self.setLayout(layout)


class DarkSheetPicker(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('MNE Color Picker')
        self.setCentralWidget(QWidget())

        self.stylesheet = ''
        self.stylesheet_dict = dict()
        self.color_labels = dict()

        self.init_ui()
        self.init_menu()

    def init_ui(self):
        layout = QVBoxLayout()
        self.list_layout = QHBoxLayout()

        self.item_list = EditList(ui_button_pos='bottom', title='Select Item')
        self.item_list.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        self.item_list.currentChanged.connect(self.item_selected)
        self.list_layout.addWidget(self.item_list)

        self.color_widget = QWidget()
        self.list_layout.addWidget(self.color_widget)

        layout.addLayout(self.list_layout)

        # Example Widgets
        bt_layout = QHBoxLayout()
        
        show_bt = QPushButton('Show Stylesheet')
        show_bt.clicked.connect(partial(QSSViewer, self))
        bt_layout.addWidget(show_bt)

        test_pyvista_bt = QPushButton('Test PyVista')
        test_pyvista_bt.clicked.connect(self.test_pyvista)
        bt_layout.addWidget(test_pyvista_bt)

        close_bt = QPushButton('Close')
        close_bt.clicked.connect(self.close)
        bt_layout.addWidget(close_bt)

        layout.addLayout(bt_layout)

        self.centralWidget().setLayout(layout)

    def init_menu(self):
        load_menu = self.menuBar().addMenu('&Load')
        load_menu.addAction('Load File', self.load_from_file)
        load_menu.addAction('Load QDarkStyle', self.load_qdarkstyle)

        save_menu = self.menuBar().addMenu('&Save')
        save_menu.addAction('Save File', self.save_stylesheet)

    def _change_color(self, item_name, key, value):
        old_color = QColor(value)
        new_color = QColorDialog.getColor(initial=old_color, parent=self)
        if new_color.isValid():
            new_color = new_color.name()
            self.stylesheet_dict[item_name][key] = new_color

            # Update Label
            name_label = self.color_labels[key]['name']
            name_label.setText(f'{key}: {new_color}')
            show_label = self.color_labels[key]['show']
            show_label.pixmap().fill(QColor(new_color))
        self.set_stylesheet()

    def item_selected(self, item_name):
        # Remove old Color-Widget
        self.list_layout.removeWidget(self.color_widget)
        self.color_widget.deleteLater()
        del self.color_widget

        if item_name in self.stylesheet_dict:
            # Create new Color-Widget
            self.color_widget = QWidget()
            color_layout = QGridLayout()
            for row, (key, value) in enumerate(self.stylesheet_dict[item_name].items()):
                self.color_labels[key] = dict()

                # Add Color-Label
                show_label = QLabel()
                color_pixmap = QPixmap(50, 50)
                color_pixmap.fill(QColor(value))
                show_label.setPixmap(color_pixmap)
                self.color_labels[key]['show'] = show_label
                color_layout.addWidget(show_label, row, 0)

                name_label = QLabel(f'{key}: {value}')
                self.color_labels[key]['name'] = name_label
                color_layout.addWidget(name_label, row, 1)

                # Add Change-Button
                change_bt = QPushButton('Change')
                change_bt.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
                change_bt.clicked.connect(partial(self._change_color, item_name, key, value))
                color_layout.addWidget(change_bt, row, 2)

            self.color_widget.setLayout(color_layout)
            self.list_layout.addWidget(self.color_widget)
            self.item_list.adjustSize()

    def _css_to_dict(self, stylesheet_string):
        """
        Parsing css-string for items from stylable_widgets with some
        constraints (just color).
        """
        self.stylesheet_dict.clear()
        for qitem in stylable_widgets:
            pattern = rf'{qitem}([ :\w]*)\{{([^\{{\}}]+)\}}'
            all_matches = re.findall(pattern, stylesheet_string)
            for suffix, attributes in all_matches:
                attribute_pattern = r'([\-\w]*): (#[\d\w]+);'
                attribute_dict = dict()
                attr_matches = re.findall(attribute_pattern, attributes)
                for attribute, value in attr_matches:
                    attribute_dict[attribute] = value

                if len(attribute_dict) != 0:
                    self.stylesheet_dict[qitem + suffix] = attribute_dict

        self.item_list.replace_data(list(self.stylesheet_dict.keys()))
        self.item_list.adjustSize()

    def _dict_to_css(self):
        self.stylesheet = ''
        # Only include items, which are present (not removed) in list-widget
        for item in [i for i in self.stylesheet_dict if i in self.item_list.model._data]:
            self.stylesheet += item + '{\n'

            for key, value in self.stylesheet_dict[item].items():
                self.stylesheet += f'   {key}: {value};\n'

            self.stylesheet += '}\n\n'

    def set_stylesheet(self):
        self._dict_to_css()
        app = QApplication.instance()
        app.setStyleSheet(self.stylesheet)

    def load_from_file(self):
        file_path = QFileDialog.getOpenFileName(self, 'Load Stylesheet')[0]
        if file_path:
            with open(file_path, 'r') as file:
                stylesheet_string = file.read()
            self._css_to_dict(stylesheet_string)
            self.set_stylesheet()

    def load_qdarkstyle(self):
        stylesheet_string = qdarkstyle.load_stylesheet().replace('\n', '')
        self._css_to_dict(stylesheet_string)
        self.set_stylesheet()

    def save_stylesheet(self):
        save_path = QFileDialog.getSaveFileName(self)[0]
        if save_path:
            with open(save_path, 'w') as file:
                file.write(self.stylesheet)

    def test_pyvista(self):
        sample_dir_raw = sample.data_path()
        sample_dir = join(sample_dir_raw, 'MEG', 'sample')
        subjects_dir = join(sample_dir_raw, 'subjects')

        fname_stc = join(sample_dir, 'sample_audvis-meg')
        stc = read_source_estimate(fname_stc, subject='sample')

        surfer_kwargs = dict(
                hemi='lh', subjects_dir=subjects_dir,
                clim=dict(kind='value', lims=[8, 12, 15]), views='lateral',
                initial_time=0.09, time_unit='s', size=(800, 800),
                smoothing_steps=5)

        # Plot surface
        brain = stc.plot(**surfer_kwargs)

        # Add title
        brain.add_text(0.1, 0.9, 'SourceEstimate', 'title', font_size=16)
