from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *  # type: ignore
import qtawesome as qta  # type: ignore
import sip  # type: ignore

import common.runtime as rt
import common.logger as logger
import services.ui.ui_runtime as ui_runtime
import services.ui.about as about
import services.ui.logviewer as logviewer
import services.ui.configuration as configuration
import services.ui.systemstatus as systemstatus
from sequences import SequenceBase
from services.ui.viewerwidget import ViewerWidget

log = logger.get_logger()


class ExaminationWindow(QMainWindow):
    viewer1 = None
    viewer2 = None
    viewer3 = None

    def __init__(self):
        super(ExaminationWindow, self).__init__()
        uic.loadUi(f"{rt.get_console_path()}/services/ui/forms/examination.ui", self)
        self.actionClose_Examination.triggered.connect(self.close_examination_clicked)
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

        self.acceptScanEditButton.setText("")
        self.acceptScanEditButton.setIcon(qta.icon("fa5s.check"))
        self.acceptScanEditButton.setIconSize(QSize(24, 24))
        self.acceptScanEditButton.setProperty("type", "toolbar")
        self.acceptScanEditButton.clicked.connect(self.accept_scan_edit_clicked)

        self.discardScanEditButton.setText("")
        self.discardScanEditButton.setIcon(qta.icon("fa5s.times"))
        self.discardScanEditButton.setIconSize(QSize(24, 24))
        self.discardScanEditButton.setProperty("type", "toolbar")
        self.discardScanEditButton.clicked.connect(self.discard_scan_edit_clicked)

        self.stopScanButton.setText("")
        self.stopScanButton.setIcon(qta.icon("fa5s.stop"))
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
        self.queueWidget.itemSelectionChanged.connect(self.queue_item_clicked)

        self.setStyleSheet(
            "QListView::item:selected, QListView::item:hover:selected  { background-color: #E0A526; } QListView::item:hover { background-color: none; } "
        )
        self.scanParametersWidget.setStyleSheet(
            """ QTabBar { 
                    font-size: 16px;
                    font-weight: bold;
                }  
                QTabBar::tab {
                    margin-left:0px;
                    margin-right:16px;          
                    border-bottom: 3px solid transparent;
                }
               QTabBar::tab:selected {
                    border-bottom: 3px solid #E0A526;
                }                
                QTabBar::tab:selected:disabled {
                    border-bottom: 3px solid transparent;
                }                
               QTabBar::tab:disabled {
                    color: #515669;
                    border-bottom: 3px solid transparent;
                }                    
            """
        )
        self.scanParametersWidget.insertTab(0, QWidget(), "SEQUENCE")
        self.scanParametersWidget.setCurrentIndex(0)
        self.scanParametersWidget.setEnabled(False)
        self.scanParametersWidget.widget(1).setStyleSheet("background-color: #0C1123;")
        self.scanParametersWidget.widget(2).setStyleSheet("background-color: #0C1123;")
        self.scanParametersWidget.widget(3).setStyleSheet("background-color: #0C1123;")

        self.viewer1Frame.setStyleSheet("QFrame:hover { border: 1px solid #E0A526; }")
        self.viewer2Frame.setStyleSheet("QFrame:hover { border: 1px solid #E0A526; }")
        self.viewer3Frame.setStyleSheet("QFrame:hover { border: 1px solid #E0A526; }")

        viewer1Layout = QHBoxLayout(self.viewer1Frame)
        viewer1Layout.setContentsMargins(0, 0, 0, 0)
        viewer1 = ViewerWidget()
        viewer1.setProperty("id", "1")
        viewer1Layout.addWidget(viewer1)
        self.viewer1Frame.setLayout(viewer1Layout)
        viewer1.configure()

        viewer2Layout = QHBoxLayout(self.viewer2Frame)
        viewer2Layout.setContentsMargins(0, 0, 0, 0)
        viewer2 = ViewerWidget()
        viewer2.setProperty("id", "2")
        viewer2Layout.addWidget(viewer2)
        self.viewer2Frame.setLayout(viewer2Layout)
        viewer2.configure()

        viewer3Layout = QHBoxLayout(self.viewer3Frame)
        viewer3Layout.setContentsMargins(0, 0, 0, 0)
        viewer3 = ViewerWidget()
        viewer3.setProperty("id", "3")
        viewer3Layout.addWidget(viewer3)
        self.viewer3Frame.setLayout(viewer3Layout)
        viewer3.configure()

        self.update_size()
        self.update_scanlist()

    def prepare_examination_ui(self):
        patient_text = f'<span style="color: #FFF; font-size: 20px; font-weight: bold; ">{ui_runtime.patient_information.get_full_name()}</span><span style="color: #515669; font-size: 20px;">'
        patient_text += chr(0xA0) + chr(0xA0)
        patient_text += f"MRN: {ui_runtime.patient_information.mrn.upper()}</span>"
        self.patientLabel.setText(patient_text)

        self.statusBar().showMessage("Scanner ready", 0)

    def clear_examination_ui(self):
        if ui_runtime.editor_active:
            self.stop_scan_edit()

    def close_examination_clicked(self):
        ui_runtime.close_patient()

    def shutdown_clicked(self):
        ui_runtime.shutdown()

    def update_size(self):
        screen_width, screen_height = ui_runtime.get_screen_size()

        self.inlineViewerFrame.setMaximumHeight(int(screen_height * 0.45))
        self.inlineViewerFrame.setMinimumHeight(int(screen_height * 0.45))

        self.seqQueueFrame.setMaximumWidth(int(screen_width * 0.25))
        self.seqQueueFrame.setMinimumWidth(int(screen_width * 0.25))
        self.timerFrame.setMaximumWidth(int(screen_width * 0.25))
        self.timerFrame.setMinimumWidth(int(screen_width * 0.25))

    def update_sequence_list(self):
        # Dummy implementation for demo
        # TODO: Should be filled with protocol manager in the future
        self.add_sequence_menu.clear()

        sequence_list = SequenceBase.installed_sequences()
        for seq in sequence_list:
            my_action = QAction(self)
            my_action.setText(SequenceBase.get_sequence(seq).get_readable_name())
            my_action.triggered.connect(self.insert_sequence)
            my_action.setProperty("sequence_class", seq)
            self.add_sequence_menu.addAction(my_action)

    def insert_sequence(self):
        # Dummy implementation for demo
        sequence_class = self.sender().property("sequence_class")

        # Create an instance of the sequence class
        sequence_instance = SequenceBase.get_sequence(sequence_class)()
        # Ask the sequence to insert its UI into the first tab
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
        widget.setStyleSheet("QWidget { background-color: transparent; color: #444;} QLabel { padding-left: 6px; }")
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
        widget.setStyleSheet("QWidget { background-color: transparent; color: #444; } QLabel { padding-left: 6px; }")
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
        widget.setStyleSheet("QWidget { background-color: transparent; color: #000;} QLabel { padding-left: 6px; } ")
        widgetText = QLabel("3. Radial 2D TSE - AX")
        widgetText.setStyleSheet("background-color: transparent;")
        widgetButton = QPushButton("")
        widgetButton.setContentsMargins(0, 0, 0, 0)
        widgetButton.setMaximumWidth(48)
        widgetButton.setFlat(True)
        widgetButton.setIcon(qta.icon("fa5s.circle-notch", color="#000", animation=qta.Spin(widgetButton)))
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
        item2.setBackground(QColor(58, 66, 102))
        widget = QWidget()
        widget.setStyleSheet("QWidget { background-color: transparent; color: #fff;} QLabel { padding-left: 6px; }")
        widgetText = QLabel("4. Radial 2D TSE - AX")
        widgetText.setStyleSheet("background-color: transparent;")
        widgetButton = QPushButton("")
        widgetButton.setContentsMargins(0, 0, 0, 0)
        widgetButton.setMaximumWidth(48)
        widgetButton.setFlat(True)
        # widgetButton.setIcon(qta.icon("fa5s.wrench", color="#fff"))
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
        item2.setBackground(QColor(58, 66, 102))
        widget = QWidget()
        widget.setStyleSheet("QWidget { background-color: transparent; color: #fff;} QLabel { padding-left: 6px; }")
        widgetText = QLabel("5. Radial 2D TSE - COR")
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
        index = self.queueWidget.currentRow()
        read_only = True

        # Dummy code
        if index > 2:
            read_only = False

        # Make the selected item bold
        selected_widget = self.queueWidget.itemWidget(self.queueWidget.currentItem())
        selected_widget.layout().itemAt(0).widget().setStyleSheet("font-weight: bold; border-left: 16px solid #000;")
        self.queueWidget.currentItem().setSelected(False)

        self.start_scan_edit("flash_demo", read_only)
        self.scanParametersWidget.setEnabled(True)
        self.queueToolbarFrame.setCurrentIndex(1)

    def accept_scan_edit_clicked(self):
        self.scanParametersWidget.setEnabled(False)
        self.queueToolbarFrame.setCurrentIndex(0)
        self.stop_scan_edit()

    def discard_scan_edit_clicked(self):
        self.scanParametersWidget.setEnabled(False)
        self.queueToolbarFrame.setCurrentIndex(0)
        self.stop_scan_edit()

    def start_scan_edit(self, id, read_only=False):
        sequence_id = "flash_demo"

        index = self.queueWidget.currentRow()
        if index % 2:
            sequence_id = "tse3d_demo"

        if not sequence_id in SequenceBase.installed_sequences():
            log.error(f"Invalid sequence type selected for edit. Sequence {sequence_id} not installed")
            return

        # Create an instance of the sequence class and buffer it
        ui_runtime.editor_sequence_instance = SequenceBase.get_sequence(sequence_id)()

        # Ask the sequence to insert its UI into the first tab of the parameter widget
        sequence_ui_container = self.clear_seq_tab_and_return_empty()
        ui_runtime.editor_sequence_instance.setup_ui(sequence_ui_container)

        for i in range(self.scanParametersWidget.count()):
            self.scanParametersWidget.widget(i).setEnabled(read_only == False)

        self.scanParametersWidget.setCurrentIndex(0)
        self.scanParametersWidget.setEnabled(True)
        ui_runtime.editor_active = True

    def stop_scan_edit(self):
        # Remove the bold font from the selected item
        for i in range(self.queueWidget.count()):
            selected_widget = self.queueWidget.itemWidget(self.queueWidget.item(i))
            selected_widget.layout().itemAt(0).widget().setStyleSheet("font-weight: normal;")

        self.clear_seq_tab_and_return_empty()
        self.scanParametersWidget.setCurrentIndex(0)
        self.scanParametersWidget.setEnabled(False)

        if ui_runtime.editor_sequence_instance is not None:
            del ui_runtime.editor_sequence_instance
            ui_runtime.editor_sequence_instance = None

        ui_runtime.editor_active = False

    def clear_seq_tab_and_return_empty(self):
        old_widget_to_delete = self.scanParametersWidget.widget(0)
        sip.delete(old_widget_to_delete)
        new_container_widget = QWidget()
        self.scanParametersWidget.insertTab(0, new_container_widget, "SEQUENCE")
        self.scanParametersWidget.widget(0).setStyleSheet("background-color: #0C1123;")
        return new_container_widget

    def queue_item_clicked(self):
        pass
        # index = self.queueWidget.currentRow()
        # if index > 2:

        # else:
