from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *  # type: ignore
import qtawesome as qta  # type: ignore
import sip  # type: ignore

import common.runtime as rt
import services.ui.runtime as ui_runtime
import services.ui.about as about
import services.ui.logviewer as logviewer
import services.ui.configuration as configuration
import services.ui.systemstatus as systemstatus
from sequences import SequenceBase


class ExaminationWindow(QMainWindow):
    def __init__(self):
        super(ExaminationWindow, self).__init__()
        uic.loadUi(f"{rt.get_console_path()}/services/ui/forms/examination.ui", self)
        self.actionClose_Examination.triggered.connect(self.close_examination_clicked)
        self.viewer1Frame.setStyleSheet("background-color: #000000;")
        self.viewer2Frame.setStyleSheet("background-color: #000000;")
        self.viewer3Frame.setStyleSheet("background-color: #000000;")
        self.actionShutdown.triggered.connect(self.shutdown_clicked)
        self.actionAbout.triggered.connect(about.show_about)
        self.actionLog_Viewer.triggered.connect(logviewer.show_logviewer)
        self.actionConfiguration.triggered.connect(configuration.show_configuration)
        self.actionSystem_Status.triggered.connect(systemstatus.show_systemstatus)

        self.protocolBrowserButton.setText("")
        self.protocolBrowserButton.setIcon(qta.icon("fa5s.list"))
        self.protocolBrowserButton.setIconSize(QSize(32, 32))
        self.settingsButton.setText("")
        self.settingsButton.setIcon(qta.icon("fa5s.images"))
        self.settingsButton.setIconSize(QSize(32, 32))
        self.closePatientButton.setText("")
        self.closePatientButton.setIcon(qta.icon("fa5s.sign-out-alt"))
        self.closePatientButton.setIconSize(QSize(32, 32))
        self.closePatientButton.clicked.connect(self.close_examination_clicked)

        self.startScanButton.setText("")
        self.startScanButton.setIcon(qta.icon("fa5s.play", color="#40C1AC"))
        self.startScanButton.setIconSize(QSize(24, 24))
        self.startScanButton.setProperty("type", "toolbar")

        self.stopScanButton.setText("")
        self.stopScanButton.setIcon(qta.icon("fa5s.stop", color="#E5554F"))
        self.stopScanButton.setIconSize(QSize(24, 24))
        self.stopScanButton.setProperty("type", "toolbar")

        self.editScanButton.setText("")
        self.editScanButton.setIcon(qta.icon("fa5s.pen"))
        self.editScanButton.setIconSize(QSize(24, 24))
        self.editScanButton.setProperty("type", "toolbar")
        self.editScanButton.clicked.connect(self.edit_sequence_clicked)

        self.deleteScanButton.setText("")
        self.deleteScanButton.setIcon(qta.icon("fa5s.trash-alt"))
        self.deleteScanButton.setIconSize(QSize(24, 24))
        self.deleteScanButton.setProperty("type", "toolbar")

        self.addScanButton.setText("")
        self.addScanButton.setIcon(qta.icon("fa5s.plus-square"))
        self.addScanButton.setIconSize(QSize(24, 24))
        self.addScanButton.setProperty("type", "toolbar")
        self.addScanButton.setStyleSheet(
            """QPushButton::menu-indicator {
                                                image: none;
                                                subcontrol-position: right top;
                                                subcontrol-origin: padding;
                                            }
            QMenu::item:selected {
                background: #0ff;
                color: red;
            }                                            
            """
        )
        self.add_sequence_menu = QMenu(self)
        self.add_sequence_menu.setStyleSheet(
            """
            QMenu::item:selected {
                background: #E0A526; 
                color: #FFF;
            }                                            
            """
        )
        self.addScanButton.setMenu(self.add_sequence_menu)
        self.update_sequence_list()

        self.queueWidget.setStyleSheet("background-color: rgba(38, 44, 68, 60);")

        self.setStyleSheet(
            "QListView::item:selected, QListView::item:hover:selected  { background-color: #E0A526; } QListView::item:hover { background-color: none; } "
        )
        self.scanParametersWidget.setStyleSheet(
            """ QTabBar { 
                    font-size: 16px;
                    font-weight: bold;
                }  
                QTabBar::tab {
                }"""
        )
        self.scanParametersWidget.insertTab(0, QWidget(), "Sequence")
        self.scanParametersWidget.setCurrentIndex(0)
        self.scanParametersWidget.setEnabled(False)

        self.update_size()
        self.update_scanlist()

    def prepare_examination_ui(self):
        patient_text = f'<span style="color: #FFF; font-size: 20px; font-weight: bold; ">{ui_runtime.patient_information.get_full_name()}</span><span style="color: #515669; font-size: 20px;">'
        patient_text += chr(0xA0) + chr(0xA0)
        patient_text += f"MRN: {ui_runtime.patient_information.mrn.upper()}</span>"
        self.patientLabel.setText(patient_text)

        self.statusBar().showMessage("Scanner ready", 0)

    def clear_examination_ui(self):
        pass

    def close_examination_clicked(self):
        ui_runtime.close_patient()

    def shutdown_clicked(self):
        ui_runtime.shutdown()

    def update_size(self):
        screen_width, screen_height = ui_runtime.get_screen_size()

        self.inlineViewerFrame.setMaximumHeight(int(screen_height * 0.5))
        self.inlineViewerFrame.setMinimumHeight(int(screen_height * 0.5))

        self.seqQueueFrame.setMaximumWidth(int(screen_width * 0.25))
        self.seqQueueFrame.setMinimumWidth(int(screen_width * 0.25))
        self.timerFrame.setMaximumWidth(int(screen_width * 0.25))
        self.timerFrame.setMinimumWidth(int(screen_width * 0.25))

    def update_sequence_list(self):
        # Dummy implementation for demo
        # TODO: Should be filled with protocol manager in the future
        self.add_sequence_menu.clear()

        sequence_list = SequenceBase.registered_sequences()
        for seq in sequence_list:
            my_action = QAction(self)
            my_action.setText(SequenceBase.registered_sequence(seq).get_readable_name())
            my_action.triggered.connect(self.insert_sequence)
            my_action.setProperty("sequence_class", seq)
            self.add_sequence_menu.addAction(my_action)

    def insert_sequence(self):
        # Dummy implementation for demo
        sequence_class = self.sender().property("sequence_class")
        sequence_instance = SequenceBase.registered_sequence(sequence_class)()
        widget_to_delete = self.scanParametersWidget.widget(0)
        sip.delete(widget_to_delete)
        new_widget = QWidget()
        self.scanParametersWidget.insertTab(0, new_widget, "Sequence")
        sequence_instance.setup_ui(new_widget)
        self.scanParametersWidget.setCurrentIndex(0)
        self.scanParametersWidget.setEnabled(True)

    def update_scanlist(self):
        # Dummy implementation for demo
        itemN = QListWidgetItem()
        itemN.setBackground(QColor("#777"))
        widget = QWidget()
        widget.setStyleSheet("QWidget { background-color: transparent; color: #444;} ")
        widgetText = QLabel("1. 3D TSE - COR")
        widgetText.setStyleSheet("background-color: transparent;")
        widgetButton = QPushButton("")
        widgetButton.setContentsMargins(0, 0, 0, 0)
        widgetButton.setMaximumWidth(48)
        widgetButton.setFlat(True)
        widgetButton.setIcon(qta.icon("fa5s.bolt", color="#444"))
        widgetButton.setIconSize(QSize(24, 24))
        widgetButton.setStyleSheet("background-color: transparent;")
        widgetLayout = QHBoxLayout()
        widgetLayout.addWidget(widgetText)
        widgetLayout.addWidget(widgetButton)
        widgetLayout.setContentsMargins(0, 0, 0, 0)
        widget.setLayout(widgetLayout)
        itemN.setSizeHint(widget.sizeHint())
        self.queueWidget.addItem(itemN)
        self.queueWidget.setItemWidget(itemN, widget)

        itemN = QListWidgetItem()
        itemN.setBackground(QColor("#777"))
        widget = QWidget()
        widget.setStyleSheet("QWidget { background-color: transparent; color: #444;} ")
        widgetText = QLabel("2. 3D TSE - COR")
        widgetText.setStyleSheet("background-color: transparent;")
        widgetButton = QPushButton("")
        widgetButton.setContentsMargins(0, 0, 0, 0)
        widgetButton.setMaximumWidth(48)
        widgetButton.setFlat(True)
        widgetButton.setIcon(qta.icon("fa5s.check", color="#444"))
        widgetButton.setIconSize(QSize(24, 24))
        widgetButton.setStyleSheet("background-color: transparent;")
        widgetLayout = QHBoxLayout()
        widgetLayout.addWidget(widgetText)
        widgetLayout.addWidget(widgetButton)
        widgetLayout.setContentsMargins(0, 0, 0, 0)
        widget.setLayout(widgetLayout)
        itemN.setSizeHint(widget.sizeHint())
        self.queueWidget.addItem(itemN)
        self.queueWidget.setItemWidget(itemN, widget)

        item2 = QListWidgetItem()
        item2.setBackground(QColor("#FFF"))
        widget = QWidget()
        widget.setStyleSheet("QWidget { background-color: transparent; color: #000;}  ")
        widgetText = QLabel("3. Radial 2D TSE - AX")
        widgetText.setStyleSheet("background-color: transparent;")
        widgetButton = QPushButton("")
        widgetButton.setContentsMargins(0, 0, 0, 0)
        widgetButton.setMaximumWidth(48)
        widgetButton.setFlat(True)
        widgetButton.setIcon(qta.icon("fa5s.pen", color="#000"))
        widgetButton.setIconSize(QSize(24, 24))
        widgetButton.setStyleSheet("background-color: transparent;")
        widgetLayout = QHBoxLayout()
        widgetLayout.addWidget(widgetText)
        widgetLayout.addWidget(widgetButton)
        widgetLayout.setContentsMargins(0, 0, 0, 0)
        widget.setLayout(widgetLayout)
        item2.setSizeHint(widget.sizeHint())
        self.queueWidget.addItem(item2)
        self.queueWidget.setItemWidget(item2, widget)

        item2 = QListWidgetItem()
        item2.setBackground(QColor(38, 44, 68))
        widget = QWidget()
        widget.setStyleSheet("QWidget { background-color: transparent; color: #fff;}  ")
        widgetText = QLabel("4. Radial 2D TSE - AX")
        widgetText.setStyleSheet("background-color: transparent;")
        widgetButton = QPushButton("")
        widgetButton.setContentsMargins(0, 0, 0, 0)
        widgetButton.setMaximumWidth(48)
        widgetButton.setFlat(True)
        widgetButton.setIcon(qta.icon("fa5s.wrench", color="#fff"))
        widgetButton.setIconSize(QSize(24, 24))
        widgetButton.setStyleSheet("background-color: transparent;")
        widgetLayout = QHBoxLayout()
        widgetLayout.addWidget(widgetText)
        widgetLayout.addWidget(widgetButton)
        widgetLayout.setContentsMargins(0, 0, 0, 0)
        widget.setLayout(widgetLayout)
        item2.setSizeHint(widget.sizeHint())
        self.queueWidget.addItem(item2)
        self.queueWidget.setItemWidget(item2, widget)

    def edit_sequence_clicked(self):
        self.scanParametersWidget.setEnabled(False)
