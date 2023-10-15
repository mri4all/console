from datetime import datetime
import time

from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *  # type: ignore
import qtawesome as qta  # type: ignore
import sip  # type: ignore

import common.runtime as rt
import common.logger as logger
from common.types import ScanQueueEntry
import services.ui.ui_runtime as ui_runtime
import services.ui.about as about
import services.ui.logviewer as logviewer
import services.ui.configuration as configuration
import services.ui.systemstatus as systemstatus
from sequences import SequenceBase
from services.ui.viewerwidget import ViewerWidget

log = logger.get_logger()

scanParameters_stylesheet = """ 
                QTabBar { 
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

scanParameters_stylesheet_error = (
    scanParameters_stylesheet
    + """ QTabBar::tab:last { color: #E5554F; } QTabBar::tab:selected:last { color: #E5554F; border-bottom: 3px solid #E5554F; } """
)


class ExaminationWindow(QMainWindow):
    viewer1 = None
    viewer2 = None
    viewer3 = None

    def __init__(self):
        """
        Loads the user interface, applies styling, and configures the event handling.
        """
        super(ExaminationWindow, self).__init__()
        uic.loadUi(f"{rt.get_console_path()}/services/ui/forms/examination.ui", self)
        self.actionClose_Examination.triggered.connect(self.close_examination_clicked)
        self.actionShutdown.triggered.connect(self.shutdown_clicked)
        self.actionAbout.triggered.connect(about.show_about)
        self.actionLog_Viewer.triggered.connect(logviewer.show_logviewer)
        self.actionConfiguration.triggered.connect(configuration.show_configuration)
        self.actionSystem_Status.triggered.connect(systemstatus.show_systemstatus)

        self.protocolBrowserButton.setText("")
        self.protocolBrowserButton.setToolTip("Open protocol browser")
        self.protocolBrowserButton.setIcon(qta.icon("fa5s.list"))
        self.protocolBrowserButton.setIconSize(QSize(32, 32))

        self.resultsViewerButton.setText("")
        self.resultsViewerButton.setToolTip("Open results viewer")
        self.resultsViewerButton.setIcon(qta.icon("fa5s.images"))
        self.resultsViewerButton.setIconSize(QSize(32, 32))

        self.closePatientButton.setText("")
        self.closePatientButton.setToolTip("End the exam")
        self.closePatientButton.setIcon(qta.icon("fa5s.sign-out-alt"))
        self.closePatientButton.setIconSize(QSize(32, 32))
        self.closePatientButton.clicked.connect(self.close_examination_clicked)

        self.acceptScanEditButton.setText("")
        self.acceptScanEditButton.setToolTip("Accept changes")
        self.acceptScanEditButton.setIcon(qta.icon("fa5s.check"))
        self.acceptScanEditButton.setIconSize(QSize(24, 24))
        self.acceptScanEditButton.setProperty("type", "toolbar")
        self.acceptScanEditButton.clicked.connect(self.accept_scan_edit_clicked)

        self.discardScanEditButton.setText("")
        self.discardScanEditButton.setToolTip("Discard changes")
        self.discardScanEditButton.setIcon(qta.icon("fa5s.times"))
        self.discardScanEditButton.setIconSize(QSize(24, 24))
        self.discardScanEditButton.setProperty("type", "toolbar")
        self.discardScanEditButton.clicked.connect(self.discard_scan_edit_clicked)

        self.stopScanButton.setText("")
        self.stopScanButton.setToolTip("Halt selected sequence")
        self.stopScanButton.setIcon(qta.icon("fa5s.stop"))
        self.stopScanButton.setIconSize(QSize(24, 24))
        self.stopScanButton.setProperty("type", "toolbar")
        self.stopScanButton.clicked.connect(self.stop_scan_clicked)

        self.editScanButton.setText("")
        self.editScanButton.setToolTip("Edit selected sequence")
        self.editScanButton.setIcon(qta.icon("fa5s.pen"))
        self.editScanButton.setIconSize(QSize(24, 24))
        self.editScanButton.setProperty("type", "toolbar")
        self.editScanButton.clicked.connect(self.edit_sequence_clicked)

        self.deleteScanButton.setText("")
        self.deleteScanButton.setToolTip("Delete selected sequence")
        self.deleteScanButton.setIcon(qta.icon("fa5s.trash-alt"))
        self.deleteScanButton.setIconSize(QSize(24, 24))
        self.deleteScanButton.setProperty("type", "toolbar")
        self.deleteScanButton.clicked.connect(self.delete_sequence_clicked)

        self.addScanButton.setText("")
        self.addScanButton.setToolTip("Insert new sequence")
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
        self.prepare_sequence_list()

        self.queueWidget.setStyleSheet("background-color: rgba(38, 44, 68, 60);")
        self.queueWidget.itemDoubleClicked.connect(self.edit_sequence_clicked)
        self.queueWidget.installEventFilter(self)

        self.setStyleSheet(
            "QListView::item:selected, QListView::item:hover:selected  { background-color: #E0A526; } QListView::item:hover { background-color: none; } "
        )
        self.scanParametersWidget.setStyleSheet(scanParameters_stylesheet)
        self.scanParametersWidget.insertTab(0, QWidget(), "SEQUENCE")
        self.scanParametersWidget.setCurrentIndex(0)
        self.scanParametersWidget.setEnabled(False)
        self.scanParametersWidget.widget(1).setStyleSheet("background-color: #0C1123;")
        self.scanParametersWidget.widget(2).setStyleSheet("background-color: #0C1123;")
        self.scanParametersWidget.widget(3).setStyleSheet("background-color: #0C1123;")
        self.scanParametersWidget.widget(4).setStyleSheet("background-color: #0C1123;")
        self.scanParametersWidget.widget(5).setStyleSheet("background-color: #0C1123;")
        self.scanParametersWidget.tabBar().setTabIcon(5, qta.icon("fa5s.exclamation-circle", color="#E5554F"))
        self.scanParametersWidget.setTabVisible(5, False)

        self.problemsWidget.setStyleSheet(
            """
            QListView::item
            {
                margin-bottom: 14px;
                padding-left: 8px;
                padding-top: 6px;
                padding-bottom: 6px;
                border-left: 5px solid #E5554F;
            }
            """
        )

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

        self.statusLabel = QLabel()
        self.statusbar.addPermanentWidget(self.statusLabel, 100)
        self.statusLabel.setStyleSheet("QLabel:hover { background-color: none; }")

        self.update_size()

        # self.monitorTimer = QTimer(self)
        # self.monitorTimer.timeout.connect(self.update_monitor_status)
        # self.monitorTimer.start(1000)

    # def update_monitor_status(self):
    #     now = datetime.now()
    #     current_time = now.strftime("%H:%M:%S")
    #     ui_runtime.examination_widget.statusBar().showMessage(f"Last update {current_time}", 0)

    def eventFilter(self, source, event):
        if event.type() == QEvent.ContextMenu and source is self.queueWidget:
            if self.queueWidget.currentRow() >= 0 and ui_runtime.editor_active == False:
                menu = QMenu()
                menu.addAction("Rename...")
                menu.addAction("Duplicate...")
                menu.addSeparator()
                menu.addAction("Save to browser...")
                menu.addSeparator()
                menu.addAction("Show definition...")
                menu.exec_(event.globalPos())

        return super(QMainWindow, self).eventFilter(source, event)

    def update_size(self):
        """
        Scales certain UI elements to fit the current screen size.
        """
        screen_width, screen_height = ui_runtime.get_screen_size()

        self.inlineViewerFrame.setMaximumHeight(int(screen_height * 0.45))
        self.inlineViewerFrame.setMinimumHeight(int(screen_height * 0.45))

        self.seqQueueFrame.setMaximumWidth(int(screen_width * 0.25))
        self.seqQueueFrame.setMinimumWidth(int(screen_width * 0.25))
        self.timerFrame.setMaximumWidth(int(screen_width * 0.25))
        self.timerFrame.setMinimumWidth(int(screen_width * 0.25))

    def set_status_message(self, message: str):
        self.statusLabel.setText(message)

    def prepare_examination_ui(self):
        """
        Prepare the exam UI screen for a new patient. Note that the UI is not destroyed when
        closing a patient (it is just moved to the background). Hence, all UI elements need to be
        reset to their initial state.
        """
        patient_text = f'<span style="color: #FFF; font-size: 20px; font-weight: bold; ">{ui_runtime.patient_information.get_full_name()}</span><span style="color: #515669; font-size: 20px;">'
        patient_text += chr(0xA0) + chr(0xA0)
        patient_text += f"MRN: {ui_runtime.patient_information.mrn.upper()}</span>"
        self.patientLabel.setText(patient_text)
        self.set_status_message("Scanner ready")
        self.sync_queue_widget()

    def clear_examination_ui(self):
        if ui_runtime.editor_active:
            self.stop_scan_edit()

    def close_examination_clicked(self):
        ui_runtime.close_patient()

    def shutdown_clicked(self):
        ui_runtime.shutdown()

    def prepare_sequence_list(self):
        """
        Insert entries for the installed sequences to the "Add sequence" menu.
        """
        # TODO: Should be replaced with protocol manager in the future
        self.add_sequence_menu.clear()

        sequence_list = sorted(
            SequenceBase.installed_sequences(), key=lambda d: SequenceBase.get_sequence(d).get_readable_name()
        )
        for seq in sequence_list:
            # Adjustment sequences should not be shown here
            if not seq.startswith("adj_"):
                add_sequence_action = QAction(self)
                add_sequence_action.setText(SequenceBase.get_sequence(seq).get_readable_name())
                add_sequence_action.setProperty("sequence_class", seq)
                add_sequence_action.triggered.connect(self.add_sequence)
                self.add_sequence_menu.addAction(add_sequence_action)

    def add_sequence(self):
        # Delegate creation of ScanQueueEntry to UI runtime
        sequence_class = self.sender().property("sequence_class")
        if not ui_runtime.create_new_scan(sequence_class):
            log.error("Failed to create new scan")
            self.set_status_message("Failed to insert new scan. Check log file.")

        self.sync_queue_widget()

    def insert_entry_to_queue_widget(self, entry: ScanQueueEntry):
        """
        Create a new UI entry to the queue widget and colors it according the the state of the
        scan task.
        """
        widget_font_color = "#F00"
        widget_background_color = "#F00"
        widget_icon = ""
        if entry.state in ["scheduled_recon", "recon", "complete", "failure"]:
            widget_font_color = "#444"
            widget_background_color = "#777"
        if entry.state in ["created", "scheduled_acq"]:
            widget_font_color = "#FFF"
            widget_background_color = "#3a4266"
        if entry.state == "acq":
            widget_font_color = "#000"
            widget_background_color = "#FFF"
            widget_icon = "circle-notch"
        if entry.state == "complete":
            widget_icon = "check"
        if entry.state == "failure":
            widget_icon = "bolt"
        if entry.state == "scheduled_recon" or entry.state == "recon":
            widget_icon = "hourglass-half"
        if entry.state == "scheduled_acq":
            widget_icon = ""
        if entry.state == "created":
            widget_icon = "wrench"

        item = QListWidgetItem()
        item.setToolTip(f"Sequence class = {entry.sequence}")
        item.setBackground(QColor(widget_background_color))
        widget = QWidget()
        widget.setStyleSheet(
            "QWidget { background-color: transparent; color: "
            + widget_font_color
            + "; padding-top: 12px; padding-bottom: 12px; } QLabel { padding-left: 6px; }"
        )
        widgetText = QLabel(f"{entry.scan_counter}. {entry.protocol_name}")
        widgetText.setStyleSheet("background-color: transparent;")
        widgetButton = QPushButton("")
        widgetButton.setContentsMargins(0, 0, 0, 0)
        widgetButton.setMaximumWidth(48)
        widgetButton.setFlat(True)
        if widget_icon:
            if entry.state != "acq":
                widgetButton.setIcon(qta.icon(f"fa5s.{widget_icon}", color=widget_font_color))
            else:
                widgetButton.setIcon(
                    qta.icon(
                        f"fa5s.{widget_icon}",
                        color=widget_font_color,
                        animation=qta.Spin(widgetButton),
                    )
                )
        widgetButton.setIconSize(QSize(24, 24))
        widgetButton.setStyleSheet("background-color: transparent;")
        widgetLayout = QHBoxLayout()
        widgetLayout.addWidget(widgetText)
        widgetLayout.addWidget(widgetButton)
        widgetLayout.setContentsMargins(0, 0, 0, 0)
        widget.setLayout(widgetLayout)
        item.setSizeHint(widget.sizeHint())
        self.queueWidget.addItem(item)  # type: ignore
        self.queueWidget.setItemWidget(item, widget)  # type: ignore

    def edit_sequence_clicked(self):
        index = self.queueWidget.currentRow()

        if index < 0:
            return

        if index >= len(ui_runtime.scan_queue_list):
            log.error("Invalid scan queue index selected")
            return

        # Protocols can only be edited if they have not been scanned yet
        read_only = True
        if (
            ui_runtime.scan_queue_list[index].state == "created"
            or ui_runtime.scan_queue_list[index].state == "scheduled_acq"
        ):
            read_only = False

        # Make the selected item bold
        selected_widget = self.queueWidget.itemWidget(self.queueWidget.currentItem())
        selected_widget.layout().itemAt(0).widget().setStyleSheet("font-weight: bold; border-left: 16px solid #000;")
        self.queueWidget.currentItem().setSelected(False)

        sequence_type = ui_runtime.scan_queue_list[index].sequence
        scan_id = ui_runtime.scan_queue_list[index].id
        self.start_scan_edit(scan_id, sequence_type, read_only)
        self.scanParametersWidget.setEnabled(True)
        self.queueToolbarFrame.setCurrentIndex(1)

    def start_scan_edit(self, id, sequence_type, read_only=False):
        """
        Edits the selected scan protocol. To that end, the sequence class is instantiated and
        asked to render the sequence parameter UI to the editor. Also, the buttons below the
        queue widget are switched to the editing state.
        """
        # TODO: Read the settings from the selected protocol

        log.info(f"Editing scan {id} of type {sequence_type}")

        if not sequence_type in SequenceBase.installed_sequences():
            log.error(f"Invalid sequence type selected for edit. Sequence {sequence_type} not installed")
            return

        # Create an instance of the sequence class and buffer it
        ui_runtime.editor_sequence_instance = SequenceBase.get_sequence(sequence_type)()

        # Ask the sequence to insert its UI into the first tab of the parameter widget
        sequence_ui_container = self.clear_seq_tab_and_return_empty()
        ui_runtime.editor_sequence_instance.setup_ui(sequence_ui_container)

        default_settings = ui_runtime.editor_sequence_instance.get_default_parameters()
        # TODO: Pass full scan task object
        ui_runtime.editor_sequence_instance.set_parameters(default_settings, {})
        ui_runtime.editor_sequence_instance.write_parameters_to_ui(sequence_ui_container)

        for i in range(self.scanParametersWidget.count()):
            self.scanParametersWidget.widget(i).setEnabled(read_only == False)

        self.scanParametersWidget.setCurrentIndex(0)
        self.scanParametersWidget.setEnabled(True)
        ui_runtime.editor_active = True

    def stop_scan_edit(self):
        """
        Ends the protocol editing mode and switches the buttons below the queue widget back
        to their default state.
        """
        # Remove the bold font from the selected item
        for i in range(self.queueWidget.count()):
            selected_widget = self.queueWidget.itemWidget(self.queueWidget.item(i))
            selected_widget.layout().itemAt(0).widget().setStyleSheet("font-weight: normal;")

        self.clear_seq_tab_and_return_empty()
        self.scanParametersWidget.setCurrentIndex(0)
        self.scanParametersWidget.setEnabled(False)

        # Delete the sequence instance created for the editor
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

    def accept_scan_edit_clicked(self):
        ui_widget = self.scanParametersWidget.widget(0)
        # TODO: Pass the full scan task object
        parameters_valid = ui_runtime.editor_sequence_instance.read_parameters_from_ui(ui_widget, {})

        if not parameters_valid:
            self.scanParametersWidget.setTabVisible(5, True)
            self.scanParametersWidget.setStyleSheet(scanParameters_stylesheet_error)
            self.scanParametersWidget.setCurrentIndex(5)
            problems_list = ui_runtime.editor_sequence_instance.get_problems()
            self.problemsWidget.clear()
            for problem in problems_list:
                self.problemsWidget.addItem(problem)
        else:
            self.scanParametersWidget.setTabVisible(5, False)
            self.scanParametersWidget.setStyleSheet(scanParameters_stylesheet)
            self.scanParametersWidget.setEnabled(False)
            self.queueToolbarFrame.setCurrentIndex(0)
            self.stop_scan_edit()

    def discard_scan_edit_clicked(self):
        self.scanParametersWidget.setTabVisible(5, False)
        self.scanParametersWidget.setStyleSheet(scanParameters_stylesheet)
        self.scanParametersWidget.setEnabled(False)
        self.queueToolbarFrame.setCurrentIndex(0)
        self.stop_scan_edit()

    def stop_scan_clicked(self):
        # TODO: Dummy content
        self.sync_queue_widget()

    def sync_queue_widget(self):
        """
        Update/sync the displayed scan queue list according to the list kept by the runtime
        environment (which is synced with the folders and contains information about the
        sequence types and state)
        """
        ui_runtime.update_scan_queue_list()
        # TODO: Instead of clearing the whole widget, only update the changed items
        self.queueWidget.clear()

        for entry in ui_runtime.scan_queue_list:
            self.insert_entry_to_queue_widget(entry)

    def delete_sequence_clicked(self):
        index = self.queueWidget.currentRow()

        if index < 0:
            return

        if index >= len(ui_runtime.scan_queue_list):
            log.error("Invalid scan queue index selected")
            return

        # TODO: Properly delete case
        ui_runtime.scan_queue_list.pop(index)
        self.sync_queue_widget()
