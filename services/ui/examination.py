from datetime import datetime, timedelta
import json
import time

from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *  # type: ignore
import qtawesome as qta

from services.ui.shimbox import ShimBox
import sip  # type: ignore

import common.runtime as rt
import common.logger as logger
import common.task as task
from common.constants import *
from common.types import ScanQueueEntry, ScanTask
from common.ipc import Communicator
import common.ipc as ipc
import common.helper as helper

from common.types import ScanQueueEntry, ScanTask, ResultItem
import services.ui.ui_runtime as ui_runtime
import services.ui.about as about
import services.ui.logviewer as logviewer
import services.ui.configuration as configuration
import services.ui.systemstatus as systemstatus
import services.ui.taskviewer as taskviewer
import services.ui.studyviewer as studyviewer
import services.ui.protocolbrowser as protocolbrowser
import services.ui.flexviewer as flexviewer
from sequences import SequenceBase
from services.ui.viewerwidget import MplCanvas, ViewerWidget
from services.ui.custommessagebox import CustomMessageBox  # type: ignore
import services.ui.control as control

from services.ui.errors import SequenceUIFailed, UIException

import external.seq.adjustments_acq.config as cfg

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
    flexViewer = None

    scanner_status_message = ""
    updating_queue_widget = False

    shimSignal = pyqtSignal(object)

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
        self.actionProtocol_Browser.triggered.connect(
            protocolbrowser.show_protocol_browser
        )
        self.actionStudy_Viewer.triggered.connect(studyviewer.show_viewer)
        self.action_set3Viewers.triggered.connect(self.set3Viewers)
        self.action_set2Viewers.triggered.connect(self.set2Viewers)
        self.action_set1Viewer.triggered.connect(self.set1Viewer)

        self.menuDebug.menuAction().setVisible(rt.is_debugging_enabled())
        self.actionDebug_update_scan_list.triggered.connect(self.debug_update_scan_list)

        self.protocolBrowserButton.setText("")
        self.protocolBrowserButton.setToolTip("Open protocol browser")
        self.protocolBrowserButton.setIcon(qta.icon("fa5s.list"))
        self.protocolBrowserButton.setIconSize(QSize(32, 32))
        self.protocolBrowserButton.clicked.connect(
            protocolbrowser.show_protocol_browser
        )

        self.resultsViewerButton.setText("")
        self.resultsViewerButton.setToolTip("Open study viewer")
        self.resultsViewerButton.setIcon(qta.icon("fa5s.x-ray"))
        self.resultsViewerButton.setIconSize(QSize(32, 32))
        self.resultsViewerButton.clicked.connect(studyviewer.show_viewer)

        self.flexViewerButton.setText("")
        self.flexViewerButton.setToolTip("Open flex viewer")
        self.flexViewerButton.setIcon(qta.icon("fa5.window-maximize"))
        self.flexViewerButton.setIconSize(QSize(32, 32))
        self.flexViewerButton.clicked.connect(self.toggle_flexviewer)
        self.flexViewerButton.setProperty("type", "dimmedcheck")

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
        self.stopScanButton.setIcon(qta.icon("fa5s.stop", color_disabled="#515669"))
        self.stopScanButton.setIconSize(QSize(24, 24))
        self.stopScanButton.setProperty("type", "toolbar")
        self.stopScanButton.clicked.connect(self.stop_scan_clicked)

        self.editScanButton.setText("")
        self.editScanButton.setToolTip("Edit selected sequence")
        self.editScanButton.setIcon(qta.icon("fa5s.pen", color_disabled="#515669"))
        self.editScanButton.setIconSize(QSize(24, 24))
        self.editScanButton.setProperty("type", "toolbar")
        self.editScanButton.clicked.connect(self.edit_sequence_clicked)

        self.deleteScanButton.setText("")
        self.deleteScanButton.setToolTip("Delete selected sequence")
        self.deleteScanButton.setIcon(
            qta.icon("fa5s.trash-alt", color_disabled="#515669")
        )
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
        self.queueWidget.itemClicked.connect(self.edit_queue_clicked)
        self.queueWidget.currentItemChanged.connect(self.queue_selection_changed)
        self.queueWidget.installEventFilter(self)

        self.setStyleSheet(
            "QListView::item:selected, QListView::item:hover:selected  { background-color: #E0A526; } QListView::item:hover { background-color: none; } "
        )
        self.scanParametersWidget.setStyleSheet(scanParameters_stylesheet)
        self.scanParametersWidget.insertTab(0, QWidget(), "SEQUENCE")
        self.scanParametersWidget.widget(0).setStyleSheet("background-color: #0C1123;")
        self.scanParametersWidget.setCurrentIndex(0)
        self.scanParametersWidget.setEnabled(False)
        self.scanParametersWidget.widget(1).setStyleSheet("background-color: #0C1123;")
        self.scanParametersWidget.widget(2).setStyleSheet("background-color: #0C1123;")
        self.scanParametersWidget.widget(3).setStyleSheet("background-color: #0C1123;")
        self.scanParametersWidget.widget(4).setStyleSheet("background-color: #0C1123;")
        self.scanParametersWidget.widget(5).setStyleSheet("background-color: #0C1123;")
        self.scanParametersWidget.tabBar().setTabIcon(
            5, qta.icon("fa5s.exclamation-circle", color="#E5554F")
        )
        self.scanParametersWidget.setTabVisible(5, False)
        self.scanParametersWidget.currentChanged.connect(
            self.scanParametersWidgetChanged
        )
        self.larmorUpdateButton.setProperty("type", "toolbar")
        self.larmorUpdateButton.clicked.connect(self.update_larmor_clicked)
        self.larmorUpdateButton.setStyleSheet(
            "QPushButton:hover { background-color: #E0A526; color: #FFF }"
        )
        self.larmorUpdateButton.setIcon(qta.icon("fa5s.check"))
        self.larmorUpdateButton.setText(" Update")
        self.larmorUpdateButton.setToolTip("Update the Larmor frequency")
        # self.larmorUpdateButton.setIconSize(QSize(24, 24))

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

        viewer_styles = "QFrame:hover#viewer1Frame, QFrame:hover#viewer2Frame, QFrame:hover#viewer3Frame { border: 1px solid #E0A526; }"
        self.viewer1Frame.setStyleSheet(viewer_styles)
        self.viewer2Frame.setStyleSheet(viewer_styles)
        self.viewer3Frame.setStyleSheet(viewer_styles)

        viewer1Layout = QHBoxLayout(self.viewer1Frame)
        viewer1Layout.setContentsMargins(0, 0, 0, 0)
        self.viewer1 = ViewerWidget()
        self.viewer1.setProperty("id", "1")
        viewer1Layout.addWidget(self.viewer1)
        self.viewer1Frame.setLayout(viewer1Layout)

        viewer2Layout = QHBoxLayout(self.viewer2Frame)
        viewer2Layout.setContentsMargins(0, 0, 0, 0)
        self.viewer2 = ViewerWidget()
        self.viewer2.setProperty("id", "2")
        viewer2Layout.addWidget(self.viewer2)
        self.viewer2Frame.setLayout(viewer2Layout)

        viewer3Layout = QHBoxLayout(self.viewer3Frame)
        viewer3Layout.setContentsMargins(0, 0, 0, 0)
        self.viewer3 = ViewerWidget()
        self.viewer3.setProperty("id", "3")
        viewer3Layout.addWidget(self.viewer3)
        self.viewer3Frame.setLayout(viewer3Layout)

        self.sequenceResolutionLabel.setStyleSheet(
            "color: #515669; font-size: 18px; font-weight: normal;"
        )
        self.sequenceResolutionLabel.setText(
            "TA: 4.5 min   Voxel Size: 1.0 x 1.0 x 1.0 mm"
        )
        self.sequenceResolutionLabel.setVisible(False)

        self.statusLabel = QLabel()
        self.statusbar.addPermanentWidget(self.statusLabel, 0)
        self.statusLabel.setStyleSheet(
            "QLabel:hover { background-color: none; } QLabel { margin-left: 12px; margin-right: 4px; }"
        )
        self.statusProgress = QProgressBar()
        self.statusProgress.setMinimum(0)
        self.statusProgress.setMaximum(100)
        self.statusbar.addPermanentWidget(self.statusProgress, 0)
        self.statusProgress.setStyleSheet(
            "QProgressBar:hover { background-color: #040919; } QProgressBar::chunk { background-color: #262C44 }"
        )
        dummy_label = QLabel()
        dummy_label.setStyleSheet("QLabel:hover { background-color: none; }")
        self.statusbar.addPermanentWidget(dummy_label, 100)

        self.update_size()

        self.recon_pipe = Communicator(Communicator.UI_RECON)
        self.recon_pipe.received.connect(self.received_recon)
        self.recon_pipe.listen()

        self.acq_pipe = Communicator(Communicator.UI_ACQ)
        self.acq_pipe.received.connect(self.received_acq)
        self.acq_pipe.listen()

        self.monitorTimer = QTimer(self)
        self.monitorTimer.timeout.connect(self.update_monitor_status)
        self.monitorTimer.start(1000)

        self.queue_selection_changed()
        self.init_seqparam_ui()

        self.flexViewerWindow = flexviewer.FlexViewer()
        self.flexViewer = self.flexViewerWindow.viewer

    def received_recon(self, o):
        self.received_message(o, self.recon_pipe)

    def received_acq(self, o):
        self.received_message(o, self.acq_pipe)

    def received_message(self, o, pipe):
        msg_value = o.value
        if isinstance(msg_value, ipc.messages.UserQueryMessage):
            try:
                ok = False
                value = None
                dlg = None
                while value is None:
                    dlg = QInputDialog(self)
                    dlg.setInputMode(
                        dict(
                            text=QInputDialog.TextInput,
                            int=QInputDialog.IntInput,
                            float=QInputDialog.DoubleInput,
                        )[msg_value.input_type]
                    )

                    if msg_value.input_type == "int":
                        dlg.setIntMinimum(int(msg_value.in_min))
                        dlg.setIntMaximum(int(msg_value.in_max))
                    if msg_value.input_type == "float":
                        dlg.setDoubleMinimum(msg_value.in_min)
                        dlg.setDoubleMaximum(msg_value.in_max)

                    dlg.setLabelText(f"Enter {msg_value.request}")
                    dlg.setWindowTitle(msg_value.request.capitalize())
                    dlg.resize(500, 100)
                    ok = dlg.exec_()
                    get_value = dict(
                        text=dlg.textValue, int=dlg.intValue, float=dlg.doubleValue
                    )[msg_value.input_type]
                    value = get_value()
                pipe.send_user_response(response=value, error=False)

            except Exception as e:
                log.exception("Error")
                pipe.send_user_response(error=True)
        elif isinstance(msg_value, ipc.messages.UserAlertMessage):
            try:
                msg = QMessageBox()
                msg.setIcon(
                    dict(
                        information=QMessageBox.Information,
                        warning=QMessageBox.Warning,
                        critical=QMessageBox.Critical,
                    )[msg_value.alert_type]
                )
                msg.setWindowTitle(msg_value.alert_type.capitalize())
                msg.setText(msg_value.message)
                msg.exec_()
            except:
                pipe.send_user_response(error=True)
            else:
                pipe.send_user_response(error=False)
        elif isinstance(msg_value, ipc.messages.SetStatusMessage):
            self.set_status_message(msg_value.message)
        elif isinstance(msg_value, ipc.messages.ShowPlotMessage):
            try:
                sc = MplCanvas(width=7, height=4)
                dlg = CustomMessageBox(self, sc)
                msg_value.plot.show(sc.axes)
                result = dlg.exec_()
                pipe.send_user_response(response=result)
            except:
                pipe.send_user_response(error=True)
                raise
        elif isinstance(msg_value, ipc.messages.ShowDicomMessage):
            try:
                w = ViewerWidget()
                dlg = CustomMessageBox(self, w)
                w.load_dicoms(msg_value.dicom_files)
                result = dlg.exec_()
                pipe.send_user_response(response=result)
            except:
                pipe.send_user_response(error=True)
                raise
        elif isinstance(msg_value, ipc.messages.DoShimMessage):
            if msg_value.message == "start":
                self.shim_dlg = ShimBox(self)
                self.shimSignal.connect(self.shim_dlg.new_data)
                self.shim_dlg.show()
                pipe.send_user_response()
            elif msg_value.message == "get":
                pipe.send_user_response(
                    {
                        "values": self.shim_dlg.current_values.model_dump(),
                        "complete": self.shim_dlg.user_clicked != None,
                    }
                )
            elif msg_value.message == "put":
                # self.shim_dlg.canvas.axes.clear()
                log.info("received put")
                self.shimSignal.emit(msg_value.data)
                # self.shim_dlg.canvas.axes.plot([1, 2, 3, 4, 5, 6])  # [msg_value.data])
                # self.shim_dlg.canvas.axes.up
        elif isinstance(msg_value, ipc.messages.AcqDataMessage):
            try:
                ui_runtime.status_start_time = datetime.fromisoformat(
                    msg_value.start_time
                )
                ui_runtime.status_expected_duration_sec = (
                    msg_value.expected_duration_sec
                )
                ui_runtime.status_disable_statustimer = msg_value.disable_statustimer
                ui_runtime.status_received_acqdata = True
            except Exception as e:
                ui_runtime.status_received_acqdata = False
                log.warning("Received invalid acqdata message")
                log.exception(e)

    def update_monitor_status(self):
        self.monitorTimer.stop()
        self.sync_queue_widget(False)

        new_status_message = ""

        if ui_runtime.status_acq_active:
            if ui_runtime.status_received_acqdata:
                current_duration = int(
                    (datetime.now() - ui_runtime.status_start_time).total_seconds()
                )
                if ui_runtime.status_expected_duration_sec <= 0:
                    if not ui_runtime.status_disable_statustimer:
                        new_status_message = f"Running scan...  ({str(timedelta(seconds=current_duration))})"
                    self.statusProgress.setVisible(False)
                else:
                    current_percent = int(
                        100 * current_duration / ui_runtime.status_expected_duration_sec
                    )
                    if current_percent > 100:
                        current_percent = 100
                    if not ui_runtime.status_disable_statustimer:
                        new_status_message = f"Running scan...  ({str(timedelta(seconds=current_duration))})"
                    self.statusProgress.setValue(current_percent)
                    self.statusProgress.setVisible(True)
            else:
                new_status_message = "Running scan..."
        elif ui_runtime.status_recon_active:
            new_status_message = "Reconstruction data..."
            ui_runtime.status_received_acqdata = False
            self.statusProgress.setValue(0)
            self.statusProgress.setVisible(False)
        else:
            new_status_message = "Scanner ready"
            ui_runtime.status_received_acqdata = False
            self.statusProgress.setValue(0)
            self.statusProgress.setVisible(False)

        # Update the status widget, but only if the scanner status has changed
        if new_status_message != self.scanner_status_message:
            self.scanner_status_message = new_status_message
            self.set_status_message(self.scanner_status_message)

        if (
            ui_runtime.status_last_completed_scan
            != ui_runtime.status_viewer_last_autoload_scan
        ):
            # Trigger autoload of the last case
            ui_runtime.status_viewer_last_autoload_scan = (
                ui_runtime.status_last_completed_scan
            )

            if ui_runtime.status_last_completed_scan:
                # Autoload the results into the viewers
                self.autoload_results_in_viewer(ui_runtime.status_last_completed_scan)
        self.monitorTimer.start(100)

    def eventFilter(self, source, event):
        if event.type() == QEvent.ContextMenu and source is self.queueWidget:
            if self.queueWidget.currentRow() >= 0:
                if ui_runtime.editor_active == False:
                    menu = QMenu()
                    menu.addAction("Duplicate", self.duplicate_scan_clicked)
                    menu.addAction("Rename...", self.rename_scan_clicked)
                    menu.addAction("Delete", self.delete_sequence_clicked)
                    menu.addSeparator()
                    menu.addAction("Save to browser...")
                    menu.addSeparator()
                    menu.addAction("Show definition...", self.show_definition_clicked)
                    menu.exec_(event.globalPos())
                else:
                    menu = QMenu()
                    menu.addAction("Rename...", self.rename_scan_clicked)
                    menu.exec_(event.globalPos())

        return super(QMainWindow, self).eventFilter(source, event)

    def update_size(self):
        """
        Scales certain UI elements to fit the current screen size.
        """
        screen_width, screen_height = ui_runtime.get_screen_size()

        self.inlineViewerFrame.setMaximumHeight(int(screen_height * 0.475))
        self.inlineViewerFrame.setMinimumHeight(int(screen_height * 0.475))

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
        self.clear_viewers()
        patient_text = f'<span style="color: #FFF; font-size: 20px; font-weight: bold; ">{ui_runtime.patient_information.get_full_name()}</span><span style="color: #515669; font-size: 20px;">'
        patient_text += chr(0xA0) + chr(0xA0)
        patient_text += f"MRN: {ui_runtime.patient_information.mrn.upper()}</span>"
        self.patientLabel.setText(patient_text)
        self.set_status_message("Scanner ready")
        self.sync_queue_widget(True)

    def clear_examination_ui(self):
        if ui_runtime.editor_active:
            self.stop_scan_edit(False)

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
            SequenceBase.installed_sequences(),
            key=lambda d: SequenceBase.get_sequence(d).get_readable_name(),
        )
        for seq in sequence_list:
            # Adjustment sequences should not be shown here
            if (
                not seq.startswith("adj_") or not seq.startswith("prescan_")
            ) or rt.is_debugging_enabled():
                add_sequence_action = QAction(self)
                seq_name = SequenceBase.get_sequence(seq).get_readable_name()
                add_sequence_action.setText(seq_name)
                add_sequence_action.setProperty("sequence_class", seq)
                add_sequence_action.triggered.connect(self.add_sequence)
                self.add_sequence_menu.addAction(add_sequence_action)

    def add_sequence(self):
        # Delegate creation of ScanQueueEntry to UI runtime
        sequence_class = self.sender().property("sequence_class")
        if not ui_runtime.create_new_scan(sequence_class):
            log.error("Failed to create new scan")
            self.set_status_message("Failed to insert new scan. Check log file.")

        self.sync_queue_widget(False)
        self.scroll_queue_end()

    def scroll_queue_end(self):
        self.queueWidget.scrollToItem(
            self.queueWidget.item(self.queueWidget.count() - 1)
        )

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
        if entry.state == "scheduled_recon":
            widget_icon = "hourglass-half"
        if entry.state == "recon":
            widget_icon = "cog"
        if entry.state == "scheduled_acq":
            widget_icon = ""
        if entry.state == "created":
            widget_icon = "wrench"

        item = QListWidgetItem()
        tool_tip = f"Class = {entry.sequence}"
        if entry.description:
            tool_tip = f"{entry.description}\n" + tool_tip
        item.setToolTip(tool_tip)
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
        widgetButton.setProperty("state", str(entry.state))
        if widget_icon:
            if (entry.state != "acq") and (entry.state != "recon"):
                widgetButton.setIcon(
                    qta.icon(f"fa5s.{widget_icon}", color=widget_font_color)
                )
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

        imageWidgetButton = QPushButton("")
        imageWidgetButton.setContentsMargins(0, 0, 0, 0)
        imageWidgetButton.setMaximumWidth(32)
        imageWidgetButton.setFlat(True)
        imageWidgetButton.setIcon(qta.icon(f"fa5s.image", color=widget_font_color))
        imageWidgetButton.setIconSize(QSize(24, 24))
        imageWidgetButton.setStyleSheet("background-color: transparent;")
        image_button_menu = QMenu(self)
        view_action = image_button_menu.addAction(
            "Show in Viewer 1", self.load_result_in_viewer
        )
        view_action.setProperty("source", str(entry.folder_name))
        view_action.setProperty("target", "viewer1")
        view_action = image_button_menu.addAction(
            "Show in Viewer 2", self.load_result_in_viewer
        )
        view_action.setProperty("source", str(entry.folder_name))
        view_action.setProperty("target", "viewer2")
        view_action = image_button_menu.addAction(
            "Show in Viewer 3", self.load_result_in_viewer
        )
        view_action.setProperty("source", str(entry.folder_name))
        view_action.setProperty("target", "viewer3")
        view_action = image_button_menu.addAction(
            "Show in Flex Viewer", self.load_result_in_viewer
        )
        view_action.setProperty("source", str(entry.folder_name))
        view_action.setProperty("target", "flex")
        imageWidgetButton.setMenu(image_button_menu)
        imageWidgetButton.setStyleSheet(
            """QPushButton::menu-indicator {
                                                image: none;
                                                subcontrol-position: right top;
                                                subcontrol-origin: padding;
                                            }
                QPushButton::hover {
                    background-color: #FFF;
                }     
            """
        )
        widgetLayout = QHBoxLayout()
        widgetLayout.addWidget(widgetText)
        widgetLayout.addWidget(imageWidgetButton)
        widgetLayout.addWidget(widgetButton)

        if entry.has_results:
            imageWidgetButton.setVisible(True)
        else:
            imageWidgetButton.setVisible(False)

        widgetLayout.setContentsMargins(0, 0, 0, 0)
        widgetLayout.setSpacing(0)
        widget.setLayout(widgetLayout)
        item.setSizeHint(widget.sizeHint())
        self.queueWidget.addItem(item)  # type: ignore
        self.queueWidget.setItemWidget(item, widget)  # type: ignore

    def update_entry_in_queue_widget(self, index: int, entry: ScanQueueEntry):
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
        if entry.state == "scheduled_recon":
            widget_icon = "hourglass-half"
        if entry.state == "recon":
            widget_icon = "cog"
        if entry.state == "scheduled_acq":
            widget_icon = ""
        if entry.state == "created":
            widget_icon = "wrench"

        selected_stylesheet = ""
        if index == ui_runtime.editor_queue_index:
            selected_stylesheet = "font-weight: bold; border-left: 16px solid #E0A526;"
        else:
            selected_stylesheet = "font-weight: normal; border-left: 0px solid #000;"

        widget_stylesheet = (
            "QWidget { background-color: transparent; color: "
            + widget_font_color
            + "; padding-top: 12px; padding-bottom: 12px; "
            + selected_stylesheet
            + " } QLabel { padding-left: 7px; color: "
            + widget_font_color
            + "; } "
        )

        self.queueWidget.item(index).setBackground(QColor(widget_background_color))
        selected_widget = self.queueWidget.itemWidget(self.queueWidget.item(index))
        selected_widget.layout().itemAt(0).widget().setText(
            f"{entry.scan_counter}. {entry.protocol_name}"
        )
        selected_widget.layout().itemAt(0).widget().setStyleSheet(widget_stylesheet)

        selected_widget.layout().itemAt(1).widget().setIcon(
            qta.icon(f"fa5s.image", color=widget_font_color)
        )
        if entry.has_results:
            selected_widget.layout().itemAt(1).widget().setVisible(True)
        else:
            selected_widget.layout().itemAt(1).widget().setVisible(False)

        if widget_icon:
            # Only update the icon if the change has state. Otherwise, the animation gets reset during every update
            if str(entry.state) != selected_widget.layout().itemAt(2).widget().property(
                "state"
            ):
                if (entry.state != "acq") and (entry.state != "recon"):
                    selected_widget.layout().itemAt(2).widget().setIcon(
                        qta.icon(f"fa5s.{widget_icon}", color=widget_font_color)
                    )
                else:
                    selected_widget.layout().itemAt(2).widget().setIcon(
                        qta.icon(
                            f"fa5s.{widget_icon}",
                            color=widget_font_color,
                            animation=qta.Spin(
                                selected_widget.layout().itemAt(2).widget()
                            ),
                        )
                    )
        else:
            selected_widget.layout().itemAt(2).widget().setIcon(QIcon())
        selected_widget.layout().itemAt(2).widget().setProperty("state", entry.state)

    last_item_clicked = -1

    def edit_queue_clicked(self):
        pass
        # TODO: Find better way to highlight selected state
        # if (self.queueWidget.currentRow() > -1) and (
        #     self.last_item_clicked == self.queueWidget.currentRow()
        # ):
        #     self.queueWidget.clearSelection()
        #     self.last_item_clicked = -1
        # else:
        #     self.last_item_clicked = self.queueWidget.currentRow()

    def edit_sequence_clicked(self):
        # Prevent switching to another scan while editing
        if ui_runtime.editor_active:
            self.queueWidget.setCurrentRow(ui_runtime.editor_queue_index)
            return

        self.last_item_clicked = -1
        index = self.queueWidget.currentRow()

        if index < 0:
            return
        if index >= len(ui_runtime.scan_queue_list):
            log.error("Invalid scan queue index selected")
            return

        # Update the scan queue list to ensure that the job can still be deleted at this time
        ui_runtime.update_scan_queue_list()
        scan_entry = ui_runtime.get_scan_queue_entry(index)
        if not scan_entry:
            log.error("Invalid scan queue index selected")
            return

        # Protocols can only be edited if they have not been scanned yet
        read_only = True
        if (
            scan_entry.state == mri4all_states.CREATED
            or scan_entry.state == mri4all_states.SCHEDULED_ACQ
        ):
            read_only = False

        # Make the selected item bold
        selected_widget = self.queueWidget.itemWidget(self.queueWidget.currentItem())
        selected_widget.layout().itemAt(0).widget().setStyleSheet(
            "QWidget {font-weight: bold; border-left: 16px solid #E0A526; }"
        )
        self.queueWidget.currentItem().setSelected(False)

        self.start_scan_edit(index, read_only)
        self.scanParametersWidget.setEnabled(True)
        self.queueToolbarFrame.setCurrentIndex(1)
        self.sync_queue_widget(False)

    def start_scan_edit(self, index, read_only=False):
        """
        Edits the selected scan protocol. To that end, the sequence class is instantiated and
        asked to render the sequence parameter UI to the editor. Also, the buttons below the
        queue widget are switched to the editing state.
        """
        scan_entry = ui_runtime.get_scan_queue_entry(index)
        sequence_type = scan_entry.sequence

        log.info(f"Editing protocol {scan_entry.protocol_name} of type {sequence_type}")

        if not sequence_type in SequenceBase.installed_sequences():
            log.error(
                f"Invalid sequence type selected for edit. Sequence {sequence_type} not installed"
            )
            return

        try:
            # Create an instance of the sequence class and buffer it
            ui_runtime.editor_sequence_instance = SequenceBase.get_sequence(
                sequence_type
            )()
        except:
            log.error(f"Failed to create instance of sequence {sequence_type}")
            return

        # Ask the sequence to insert its UI into the first tab of the parameter widget
        self.sequenceResolutionLabel.setText("")
        sequence_ui_container = self.clear_seq_tab_and_return_empty()
        ui_runtime.editor_sequence_instance.init_ui(
            sequence_ui_container, self.sequenceResolutionLabel
        )
        scan_path = ui_runtime.get_scan_location(index)
        if not scan_path:
            log.error("Case has invalid state. Cannot read scan parameters")
            # Needs handling
            pass

        if not read_only:
            task.set_task_state(scan_path, mri4all_files.EDITING, True)
            task.set_task_state(scan_path, mri4all_files.PREPARED, False)

        scan_task = task.read_task(scan_path)
        ui_runtime.editor_protocol_name = scan_task.protocol_name

        if not ui_runtime.editor_sequence_instance.set_parameters(
            scan_task.parameters, scan_task
        ):
            # TODO: Parameters from task file are invalid. Needs error handling.
            pass

        self.otherParametersTextEdit.setPlainText(json.dumps(scan_task.other, indent=4))
        self.load_seqparam_to_ui(scan_task)

        ui_runtime.editor_scantask = scan_task
        ui_runtime.editor_sequence_instance.write_parameters_to_ui(
            sequence_ui_container
        )

        # Configure UI for editing
        for i in range(self.scanParametersWidget.count()):
            self.scanParametersWidget.widget(i).setEnabled(read_only == False)

        self.scanParametersWidget.setCurrentIndex(0)
        self.scanParametersWidget.setEnabled(True)
        self.sequenceResolutionLabel.setVisible(True)
        ui_runtime.editor_active = True
        ui_runtime.editor_readonly = read_only
        ui_runtime.editor_queue_index = index

    def stop_scan_edit(self, update_job: bool):
        """
        Ends the protocol editing mode and switches the buttons below the queue widget back
        to their default state.
        """
        if update_job:
            # Update the scan job with the new settings
            scan_path = ui_runtime.get_scan_location(ui_runtime.editor_queue_index)
            ui_runtime.editor_scantask.parameters = (
                ui_runtime.editor_sequence_instance.get_parameters()
            )
            ui_runtime.editor_scantask.other = json.loads(
                self.otherParametersTextEdit.toPlainText()
            )
            self.store_seqparam_from_ui(ui_runtime.editor_scantask)
            ui_runtime.editor_scantask.journal.prepared_at = helper.get_datetime()
            task.write_task(scan_path, ui_runtime.editor_scantask)
            task.set_task_state(scan_path, mri4all_files.EDITING, False)
            task.set_task_state(scan_path, mri4all_files.PREPARED, True)

        # Remove the bold font from the selected item
        for i in range(self.queueWidget.count()):
            selected_widget = self.queueWidget.itemWidget(self.queueWidget.item(i))
            selected_widget.layout().itemAt(0).widget().setStyleSheet(
                "font-weight: normal;"
            )

        self.clear_seq_tab_and_return_empty()
        self.scanParametersWidget.setCurrentIndex(0)
        self.scanParametersWidget.setEnabled(False)
        self.sequenceResolutionLabel.setVisible(False)

        # Delete the sequence instance created for the editor
        if ui_runtime.editor_sequence_instance is not None:
            del ui_runtime.editor_sequence_instance
            ui_runtime.editor_sequence_instance = SequenceBase()

        ui_runtime.editor_active = False
        ui_runtime.editor_readonly = False
        ui_runtime.editor_queue_index = -1
        ui_runtime.editor_scantask = ScanTask()
        self.sync_queue_widget(False)

    def clear_seq_tab_and_return_empty(self):
        old_widget_to_delete = self.scanParametersWidget.widget(0)
        sip.delete(old_widget_to_delete)
        new_container_widget = QWidget()
        self.scanParametersWidget.insertTab(0, new_container_widget, "SEQUENCE")
        self.scanParametersWidget.widget(0).setStyleSheet("background-color: #0C1123;")
        return new_container_widget

    def accept_scan_edit_clicked(self):
        problems_list = []

        ui_widget = self.scanParametersWidget.widget(0)
        # TODO: Pass the full scan task object
        parameters_valid = ui_runtime.editor_sequence_instance.read_parameters_from_ui(
            ui_widget, ui_runtime.editor_scantask
        )
        try:
            json.loads(self.otherParametersTextEdit.toPlainText())
        except:
            parameters_valid = False
            problems_list.append(
                "Other additional parameters have invalid format. Please validate JSON syntax."
            )

        if not parameters_valid:
            self.scanParametersWidget.setTabVisible(5, True)
            self.scanParametersWidget.setStyleSheet(scanParameters_stylesheet_error)
            self.scanParametersWidget.setCurrentIndex(5)
            problems_list = (
                ui_runtime.editor_sequence_instance.get_problems() + problems_list
            )
            self.problemsWidget.clear()
            for problem in problems_list:
                self.problemsWidget.addItem(str(problem))
        else:
            self.scanParametersWidget.setTabVisible(5, False)
            self.scanParametersWidget.setStyleSheet(scanParameters_stylesheet)
            self.scanParametersWidget.setEnabled(False)
            self.queueToolbarFrame.setCurrentIndex(0)
            # Update the task file, but only if the case has not been opened in read-only mode
            self.stop_scan_edit(ui_runtime.editor_readonly == False)

    def discard_scan_edit_clicked(self):
        self.scanParametersWidget.setTabVisible(5, False)
        self.scanParametersWidget.setStyleSheet(scanParameters_stylesheet)
        self.scanParametersWidget.setEnabled(False)
        self.queueToolbarFrame.setCurrentIndex(0)
        self.stop_scan_edit(False)

    def stop_scan_clicked(self):
        index = self.queueWidget.currentRow()

        if index < 0:
            return
        if index >= len(ui_runtime.scan_queue_list):
            log.error("Invalid scan queue index selected")
            return

        # Update the scan queue list to ensure that the job can still be stopped at this time
        ui_runtime.update_scan_queue_list()
        scan_entry = ui_runtime.get_scan_queue_entry(index)
        if not scan_entry:
            log.error("Invalid scan queue index selected")
            return

        scan_path = ui_runtime.get_scan_location(index)

        if scan_entry.state == "scheduled_acq":
            # Revert the case to the "created" state
            task.set_task_state(scan_path, mri4all_files.PREPARED, False)
        if scan_entry.state == "acq":
            if task.has_task_state(scan_path, mri4all_files.STOP):
                control.restart_device()
            else:
                task.set_task_state(scan_path, mri4all_files.STOP, True)
        self.sync_queue_widget(False)

    def sync_queue_widget(self, reset: bool):
        """
        Update/sync the displayed scan queue list according to the list kept by the runtime
        environment (which is synced with the folders and contains information about the
        sequence types and state)
        """
        # Avoid running updates in parallel
        if self.updating_queue_widget:
            return
        self.updating_queue_widget = True

        reset_list = reset
        ui_runtime.update_scan_queue_list()
        if len(ui_runtime.scan_queue_list) != self.queueWidget.count():
            reset_list = True

        if reset_list:
            self.queueWidget.clear()
            for entry in ui_runtime.scan_queue_list:
                self.insert_entry_to_queue_widget(entry)
        else:
            for i in range(len(ui_runtime.scan_queue_list)):
                entry = ui_runtime.get_scan_queue_entry(i)
                if not entry:
                    log.error("Invalid scan queue index while updating widget")
                    continue
                self.update_entry_in_queue_widget(i, entry)

        self.updating_queue_widget = False

    def delete_sequence_clicked(self):
        index = self.queueWidget.currentRow()

        if index < 0:
            return
        if index >= len(ui_runtime.scan_queue_list):
            log.error("Invalid scan queue index selected")
            return

        # Update the scan queue list to ensure that the job can still be deleted at this time
        ui_runtime.update_scan_queue_list()
        scan_entry = ui_runtime.get_scan_queue_entry(index)
        if not scan_entry:
            log.error("Invalid scan queue index selected")
            return

        if not (scan_entry.state == "created" or scan_entry.state == "scheduled_acq"):
            # Jobs can only be deleted if they have not been scanned yet
            return

        scan_path = ui_runtime.get_scan_location(index)

        # Delete case the corresponding task folder
        if not task.delete_task(scan_path):
            # TODO: Show error message
            pass
        # Update the scan queue list
        self.sync_queue_widget(True)

    def debug_update_scan_list(self):
        self.sync_queue_widget(False)

    def set1Viewer(self):
        self.viewer1Frame.setVisible(True)
        self.viewer2Frame.setVisible(False)
        self.viewer3Frame.setVisible(False)
        QTimer.singleShot(1, self.triggerViewerLayoutUpdate)

    def set2Viewers(self):
        self.viewer1Frame.setVisible(True)
        self.viewer2Frame.setVisible(True)
        self.viewer3Frame.setVisible(False)
        QTimer.singleShot(1, self.triggerViewerLayoutUpdate)

    def set3Viewers(self):
        self.viewer1Frame.setVisible(True)
        self.viewer2Frame.setVisible(True)
        self.viewer3Frame.setVisible(True)
        QTimer.singleShot(1, self.triggerViewerLayoutUpdate)

    def triggerViewerLayoutUpdate(self):
        self.viewer1.layoutUpdate()
        self.viewer2.layoutUpdate()
        self.viewer3.layoutUpdate()

    def show_definition_clicked(self):
        index = self.queueWidget.currentRow()
        if index < 0:
            return
        if index >= len(ui_runtime.scan_queue_list):
            log.error("Invalid scan queue index selected")
            return

        # Update the scan queue list to ensure that the job can still be deleted at this time
        ui_runtime.update_scan_queue_list()
        scan_entry = ui_runtime.get_scan_queue_entry(index)
        if not scan_entry:
            log.warning("Invalid scan queue index selected")
            return

        taskviewer.show_taskviewer(ui_runtime.get_scan_location(index))

    def rename_scan_clicked(self):
        index = self.queueWidget.currentRow()

        if index < 0:
            return
        if index >= len(ui_runtime.scan_queue_list):
            log.error("Invalid scan queue index selected")
            return

        # Update the scan queue list to ensure that the job can still be renamed at this time
        ui_runtime.update_scan_queue_list()
        scan_entry = ui_runtime.get_scan_queue_entry(index)
        if not scan_entry:
            log.warning("Invalid scan queue index selected for renaming")
            return
        if not (
            scan_entry.state == mri4all_states.CREATED
            or scan_entry.state == mri4all_states.SCHEDULED_ACQ
        ):
            # Jobs can only be renamed if they have not been scanned yet
            return

        current_name = ""
        if not ui_runtime.editor_active:
            current_name = scan_entry.protocol_name
        else:
            current_name = ui_runtime.editor_scantask.protocol_name

        dlg = QInputDialog(self)
        dlg.setInputMode(QInputDialog.TextInput)
        dlg.setLabelText("Enter protocol name")
        dlg.setWindowTitle("Protocol Name")
        dlg.resize(500, 100)
        dlg.setTextValue(current_name)
        ok = dlg.exec_()
        new_name = dlg.textValue()

        if ok:
            if ui_runtime.editor_active == False:
                ui_runtime.update_scan_queue_list()
                scan_entry = ui_runtime.get_scan_queue_entry(index)

                if (
                    scan_entry.state != mri4all_states.CREATED
                    and scan_entry.state != mri4all_states.SCHEDULED_ACQ
                ):
                    log.warning("Cannot rename scan. Scan has already been started.")
                    # TODO: Post message to UI
                    return

                scan_path = ui_runtime.get_scan_location(index)
                if not scan_path:
                    log.error("Case has invalid state. Cannot read scan parameters")
                    # Needs handling
                    pass
                scan_task = task.read_task(scan_path)
                if scan_task == None:
                    log.error("Failed to read task file")
                    # Needs handling
                    pass
                scan_task.protocol_name = new_name
                ui_runtime.get_scan_queue_entry(index).protocol_name = new_name
                if not task.write_task(scan_path, scan_task):
                    log.error("Failed to write updated task file")
                    # Needs handling
                    pass
            else:
                ui_runtime.editor_scantask.protocol_name = new_name
                ui_runtime.get_scan_queue_entry(index).protocol_name = new_name
                # self.update_entry_in_queue_widget(index, ui_runtime.get_scan_queue_entry(index))

            self.sync_queue_widget(False)

    def duplicate_scan_clicked(self):
        index = self.queueWidget.currentRow()

        if index < 0:
            return
        if index >= len(ui_runtime.scan_queue_list):
            log.error("Invalid scan queue index selected")
            return

        ui_runtime.update_scan_queue_list()
        scan_entry = ui_runtime.get_scan_queue_entry(index)
        if not scan_entry:
            log.warning("Invalid scan queue index selected")
            return

        if not ui_runtime.duplicate_sequence(index):
            log.error("Failed to duplicate scan")
            # TODO: Show error message
            return

        ui_runtime.get_scan_queue_entry(
            len(ui_runtime.scan_queue_list) - 1
        ).protocol_name = scan_entry.protocol_name

        self.sync_queue_widget(True)
        self.scroll_queue_end()

    def clear_viewers(self):
        self.viewer1.view_data("", "empty", {})
        self.viewer2.view_data("", "empty", {})
        self.viewer3.view_data("", "empty", {})
        self.flexViewer.view_data("", "empty", {})

    def load_result_in_viewer(self):
        scan_folder = self.sender().property("source")
        if not scan_folder:
            log.warning("Unable to identify scan for viewers.")
            return
        scan_path = mri4all_paths.DATA_COMPLETE + "/" + scan_folder
        scan_task = task.read_task(scan_path)
        if not scan_task:
            log.warning("Unable load scan task for viewers.")
            return

        result_item = None
        for result in scan_task.results:
            if result.primary:
                result_item = result
                break

        if not result_item:
            log.warning("Unable load scan task for viewers.")
            return
        result_path = scan_path + "/" + result_item.file_path

        target_viewer = self.sender().property("target")
        if target_viewer == "viewer1":
            self.viewer1.view_data(result_path, result_item.type, scan_task)
        elif target_viewer == "viewer2":
            self.viewer2.view_data(result_path, result_item.type, scan_task)
        elif target_viewer == "viewer3":
            self.viewer3.view_data(result_path, result_item.type, scan_task)
        elif target_viewer == "flex":
            self.flexViewer.view_data(result_path, result_item.type, scan_task)
        else:
            log.error("Invalid target viewer selected")

    def autoload_results_in_viewer(self, scan_folder):
        if not scan_folder:
            return

        log.info(f"Autoloading results for scan {scan_folder}")

        # Read scan_task for given queue item
        scan_path = mri4all_paths.DATA_COMPLETE + "/" + scan_folder
        scan_task = task.read_task(scan_path)
        if not scan_task:
            log.warning("Unable load scan task for viewers.")
            return

        # Loop over all results of the scan task
        for result_item in scan_task.results:
            result_path = scan_path + "/" + result_item.file_path
            if result_item.autoload_viewer == 1:
                self.viewer1.view_data(result_path, result_item.type, scan_task)
            elif result_item.autoload_viewer == 2:
                self.viewer2.view_data(result_path, result_item.type, scan_task)
            elif result_item.autoload_viewer == 3:
                self.viewer3.view_data(result_path, result_item.type, scan_task)
            elif result_item.autoload_viewer == 4:
                self.flexViewer.view_data(result_path, result_item.type, scan_task)
            elif result_item.autoload_viewer == 0:
                continue
            else:
                log.warning("Invalid target viewer provided")

    def queue_selection_changed(self):
        index = self.queueWidget.currentRow()

        if index < 0:
            self.deleteScanButton.setEnabled(False)
            self.stopScanButton.setEnabled(False)
            self.editScanButton.setEnabled(False)
            return
        if index >= len(ui_runtime.scan_queue_list):
            log.warning("Invalid scan queue index selected")
            return

        ui_runtime.update_scan_queue_list()
        scan_entry = ui_runtime.get_scan_queue_entry(index)

        if (
            scan_entry.state == mri4all_states.CREATED
            or scan_entry.state == mri4all_states.SCHEDULED_ACQ
        ):
            self.deleteScanButton.setEnabled(True)
        else:
            self.deleteScanButton.setEnabled(False)

        if (
            scan_entry.state == mri4all_states.CREATED
            or scan_entry.state == mri4all_states.SCHEDULED_ACQ
        ):
            self.deleteScanButton.setEnabled(True)
        else:
            self.deleteScanButton.setEnabled(False)

        if scan_entry.state in [
            mri4all_states.FAILURE,
            mri4all_states.COMPLETE,
            mri4all_states.SCHEDULED_RECON,
        ]:
            self.stopScanButton.setEnabled(False)
        else:
            self.stopScanButton.setEnabled(True)

        self.editScanButton.setEnabled(True)

    def ui_denoising_strength(self):
        value = self.denoisingSlider.value()
        description = "OFF"
        if value > 0:
            description = "LOW"
        if value > 3:
            description = "MEDIUM"
        if value > 6:
            description = "HIGH"
        self.denoisingValueLabel.setText(description + " (" + str(value) + ")")

    def init_seqparam_ui(self):
        self.denoisingSlider.valueChanged.connect(self.ui_denoising_strength)

    def load_seqparam_to_ui(self, scan_task):
        denoising_strength = scan_task.processing.denoising_strength
        if denoising_strength > 9:
            denoising_strength = 9
        if denoising_strength < 0:
            denoising_strength = 0
        self.denoisingSlider.setValue(denoising_strength)

    def store_seqparam_from_ui(self, scan_task):
        scan_task.processing.denoising_strength = self.denoisingSlider.value()

    def toggle_flexviewer(self):
        if self.flexViewerWindow.isVisible():
            self.flexViewerWindow.setVisible(False)
        else:
            self.flexViewerWindow.setVisible(True)

    def scanParametersWidgetChanged(self, index):
        # TODO: This is just a hack to make the Larmor frequency editable from the UI. Needs to be replaced with a cleaner solution.
        if index == 2:
            cfg.update()
            self.larmorSpinBox.setValue(cfg.LARMOR_FREQ)

    def update_larmor_clicked(self):
        # TODO: This is just a hack to make the Larmor frequency editable from the UI. Needs to be replaced with a cleaner solution.
        from sequences.common.util import reading_json_parameter, writing_json_parameter

        configuration_data = reading_json_parameter()
        configuration_data.rf_parameters.larmor_frequency_MHz = (
            self.larmorSpinBox.value()
        )
        writing_json_parameter(config_data=configuration_data)
        cfg.update()
        pass
