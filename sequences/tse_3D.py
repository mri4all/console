import os
from pathlib import Path
import datetime

from PyQt5 import uic

import pypulseq as pp  # type: ignore
import external.seq.adjustments_acq.config as cfg
from external.seq.adjustments_acq.scripts import run_pulseq
from sequences.common.get_trajectory import choose_pe_order
from sequences import PulseqSequence
from sequences.common import make_tse_3D
import common.logger as logger
from common.types import ResultItem

log = logger.get_logger()


class SequenceTSE_2D(PulseqSequence, registry_key=Path(__file__).stem):
    # Sequence parameters
    param_TE: int = 50
    param_TR: int = 250
    param_ETL: int = 2
    param_NSA: int = 1
    param_Orientation: str = "Axial"
    param_FOV: int = 200
    param_Base_Resolution: int = 64
    param_Slices: int = 8
    param_BW: int = 32000
    param_Trajectory: str = "Cartesian"
    param_PE_Ordering: str = "Center_out"
    param_Slice_Ordering: str = "Center_out"
    param_view_traj: bool = True

    @classmethod
    def get_readable_name(self) -> str:
        return "3D Turbo Spin-Echo"

    def setup_ui(self, widget) -> bool:
        seq_path = os.path.dirname(os.path.abspath(__file__))
        uic.loadUi(f"{seq_path}/{self.get_name()}/interface.ui", widget)

        widget.TRSpinBox.valueChanged.connect(self.update_info)
        widget.Base_Resolution_SpinBox.valueChanged.connect(self.update_info)
        widget.Slices_SpinBox.valueChanged.connect(self.update_info)
        widget.ETL_SpinBox.valueChanged.connect(self.update_info)
        return True

    def update_info(self):
        duration_sec = int(
            self.main_widget.TRSpinBox.value()
            * self.main_widget.Base_Resolution_SpinBox.value()
            * self.main_widget.Slices_SpinBox.value()
            / self.main_widget.ETL_SpinBox.value()
            / 1000
        )
        duration = str(datetime.timedelta(seconds=duration_sec))

        res_slice = (
            self.main_widget.FOV_SpinBox.value()
            / self.main_widget.Slices_SpinBox.value()
            * 10
        )
        res_inplane = (
            self.main_widget.FOV_SpinBox.value()
            / self.main_widget.Base_Resolution_SpinBox.value()
            * 10
        )

        self.show_ui_info_text(
            f"TA: {duration} sec       Voxel Size: {res_inplane:.2f} x {res_inplane:.2f} x {res_slice:.2f} mm"
        )

    def get_parameters(self) -> dict:
        return {
            "TE": self.param_TE,
            "TR": self.param_TR,
            "ETL": self.param_ETL,
            "NSA": self.param_NSA,
            "Orientation": self.param_Orientation,
            "FOV": self.param_FOV,
            "Base_Resolution": self.param_Base_Resolution,
            "Slices": self.param_Slices,
            "BW": self.param_BW,
            "Trajectory": self.param_Trajectory,
            "PE_Ordering": self.param_PE_Ordering,
            "Slice_Ordering": self.param_Slice_Ordering,
            "view_traj": self.param_view_traj,
        }

    @classmethod
    def get_default_parameters(
        self,
    ) -> dict:
        return {
            "TE": 20,
            "TR": 250,
            "ETL": 1,
            "NSA": 1,
            "Orientation": "Axial",
            "FOV": 20,
            "Base_Resolution": 32,
            "Slices": 8,
            "BW": 32000,
            "Trajectory": "Cartesian",
            "PE_Ordering": "Linear_up",
            "Slice_Ordering": "Linear_up",
            "view_traj": False,
        }

    def set_parameters(self, parameters, scan_task) -> bool:
        self.problem_list = []
        try:
            self.param_TE = parameters["TE"]
            self.param_TR = parameters["TR"]
            self.param_ETL = parameters["ETL"]
            self.param_NSA = parameters["NSA"]
            self.param_Orientation = parameters["Orientation"]
            self.param_FOV = parameters["FOV"]
            self.param_Base_Resolution = parameters["Base_Resolution"]
            self.param_Slices = parameters["Slices"]
            self.param_BW = parameters["BW"]
            self.param_Trajectory = parameters["Trajectory"]
            self.param_PE_Ordering = parameters["PE_Ordering"]
            self.param_Slice_Ordering = parameters["Slice_Ordering"]
            self.param_view_traj = parameters["view_traj"]
        except:
            self.problem_list.append("Invalid parameters provided")
            return False
        return self.validate_parameters(scan_task)

    def write_parameters_to_ui(self, widget) -> bool:
        widget.TESpinBox.setValue(self.param_TE)
        widget.TRSpinBox.setValue(self.param_TR)
        widget.ETL_SpinBox.setValue(self.param_ETL)
        widget.NSA_SpinBox.setValue(self.param_NSA)
        widget.Orientation_ComboBox.setCurrentText(self.param_Orientation)
        widget.FOV_SpinBox.setValue(self.param_FOV)
        widget.Base_Resolution_SpinBox.setValue(self.param_Base_Resolution)
        widget.Slices_SpinBox.setValue(self.param_Slices)
        widget.BW_SpinBox.setValue(self.param_BW)
        widget.Trajectory_ComboBox.setCurrentText(self.param_Trajectory)
        widget.PE_Ordering_ComboBox.setCurrentText(self.param_PE_Ordering)
        widget.Slice_Ordering_ComboBox.setCurrentText(self.param_Slice_Ordering)
        widget.visualize_traj_CheckBox.setCheckState(self.param_view_traj)
        return True

    def read_parameters_from_ui(self, widget, scan_task) -> bool:
        self.problem_list = []
        self.param_TE = widget.TESpinBox.value()
        self.param_TR = widget.TRSpinBox.value()
        self.param_ETL = widget.ETL_SpinBox.value()
        self.param_NSA = widget.NSA_SpinBox.value()
        self.param_Orientation = widget.Orientation_ComboBox.currentText()
        self.param_FOV = widget.FOV_SpinBox.value()
        self.param_Base_Resolution = widget.Base_Resolution_SpinBox.value()
        self.param_Slices = widget.Slices_SpinBox.value()
        self.param_BW = widget.BW_SpinBox.value()
        self.param_Trajectory = widget.Trajectory_ComboBox.currentText()
        self.param_PE_Ordering = widget.PE_Ordering_ComboBox.currentText()
        self.param_Slice_Ordering = widget.Slice_Ordering_ComboBox.currentText()
        self.param_view_traj = widget.visualize_traj_CheckBox.isChecked()
        self.validate_parameters(scan_task)
        return self.is_valid()

    def validate_parameters(self, scan_task) -> bool:
        if self.param_TE > self.param_TR:
            self.problem_list.append("TE cannot be longer than TR")
        return self.is_valid()

    def calculate_sequence(self, scan_task) -> bool:
        log.info("Calculating sequence " + self.get_name())

        scan_task.processing.recon_mode = "basic3d"
        scan_task.processing.dim = 3
        scan_task.processing.dim_size = f"{self.param_Slices},{self.param_Base_Resolution},{self.param_Base_Resolution}"
        self.seq_file_path = self.get_working_folder() + "/seq/acq0.seq"

        # ToDo: if self.trajectory == "Cartesian": # (default)
        make_tse_3D.pypulseq_tse3D(
            inputs={
                "TE": self.param_TE,
                "TR": self.param_TR,
                "NSA": self.param_NSA,
                "ETL": self.param_ETL,
                "FOV": self.param_FOV,
                "Orientation": self.param_Orientation,
                "Base_Resolution": self.param_Base_Resolution,
                "Slices": self.param_Slices,
                "BW": self.param_BW,
                "Trajectory": self.param_Trajectory,
                "PE_Ordering": self.param_PE_Ordering,
                "Slice_Ordering": self.param_Slice_Ordering,
                "view_traj": self.param_view_traj,
            },
            check_timing=True,
            output_file=self.seq_file_path,
            pe_order_file=self.get_working_folder() + "/rawdata/pe_order.npy",
            output_folder=self.get_working_folder(),
        )
        # elif self.trajectory == "Radial":
        # pypulseq_tse2D_radial(
        #    inputs={"TE": self.param_TE, "TR": self.param_TR}, check_timing=True, output_file=self.seq_file_path
        # )

        log.info("Done calculating sequence " + self.get_name())
        self.calculated = True
        if self.param_view_traj is True:
            log.info("Displaying trajectory... " + self.get_name())
            result = ResultItem()
            result.name = "traj plot"
            result.description = "Plot of trajectory in k space of current sequence."
            result.type = "plot"
            result.primary = True
            result.autoload_viewer = 1
            result.file_path = "other/traj.plot"
            scan_task.results.append(result)

        return True

    def run_sequence(self, scan_task) -> bool:
        log.info("Running sequence " + self.get_name())

        rxd, rx_t = run_pulseq(
            seq_file=self.seq_file_path,
            rf_center=cfg.LARMOR_FREQ,
            tx_t=1,
            grad_t=10,
            tx_warmup=100,
            shim_x=0,
            shim_y=0,
            shim_z=0,
            grad_cal=False,
            save_np=True,
            save_mat=False,
            save_msgs=False,
            gui_test=False,
            case_path=self.get_working_folder(),
            raw_filename="raw",
        )

        log.info("Done running sequence " + self.get_name())
        return True
