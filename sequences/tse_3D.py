import os
from pathlib import Path
import datetime

import matplotlib.pyplot as plt
from PyQt5 import uic
import pickle

import pypulseq as pp  # type: ignore
import external.seq.adjustments_acq.config as cfg
from external.seq.adjustments_acq.scripts import run_pulseq
from sequences.common.get_trajectory import choose_pe_order
from sequences import PulseqSequence
from sequences.common import make_tse_3D
import common.logger as logger
from common.types import ResultItem
import common.helper as helper
import common.config as config

log = logger.get_logger()


from common.ipc import Communicator

ipc_comm = Communicator(Communicator.ACQ)


class SequenceTSE_3D(PulseqSequence, registry_key=Path(__file__).stem):
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
    param_Ordering: str = "center_out"
    param_plot_timing: bool = False
    param_dummy_shots: int = 5

    @classmethod
    def get_readable_name(self) -> str:
        return "3D Turbo Spin-Echo"

    @classmethod
    def get_description(self) -> str:
        return "volumetric 3D TSE acquisition with Cartesian sampling"

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
            * (
                self.main_widget.Base_Resolution_SpinBox.value()
                * self.main_widget.Slices_SpinBox.value()
                / self.main_widget.ETL_SpinBox.value()
                + self.param_dummy_shots
            )
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
            "Ordering": self.param_Ordering,
            "Plot_Timing": self.param_plot_timing,
        }

    @classmethod
    def get_default_parameters(
        self,
    ) -> dict:
        return {
            "TE": 15,
            "TR": 1000,
            "ETL": 8,
            "NSA": 1,
            "Orientation": "Axial",
            "FOV": 15,
            "Base_Resolution": 32,
            "Slices": 8,
            "BW": 32000,
            "Trajectory": "Cartesian",
            "Ordering": "center_out",
            "Plot_Timing": False,
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
            self.param_Ordering = parameters["Ordering"]
            self.param_plot_timing = parameters["Plot_Timing"]
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
        widget.Ordering_ComboBox.setCurrentText(self.param_Ordering)
        widget.PlotTiming_CheckBox.setChecked(self.param_plot_timing)
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
        self.param_Ordering = widget.Ordering_ComboBox.currentText()
        self.param_plot_timing = widget.PlotTiming_CheckBox.isChecked()
        self.validate_parameters(scan_task)
        return self.is_valid()

    def validate_parameters(self, scan_task) -> bool:
        if self.param_TE > self.param_TR:
            self.problem_list.append("TE cannot be longer than TR")
        return self.is_valid()

    def calculate_sequence(self, scan_task) -> bool:
        log.info("Calculating sequence " + self.get_name())
        ipc_comm.send_status(f"Calculating sequence...")

        if config.get_config().is_hardware_simulation():
            scan_task.processing.recon_mode = "bypass"
        else:
            scan_task.processing.recon_mode = "basic3d"

        scan_task.processing.dim = 3
        scan_task.processing.dim_size = f"{self.param_Slices},{self.param_Base_Resolution},{2*self.param_Base_Resolution}"
        scan_task.processing.oversampling_read = 2
        self.seq_file_path = self.get_working_folder() + "/seq/acq0.seq"

        fa_exc = cfg.DBG_FA_EXC
        fa_ref = cfg.DBG_FA_REF
        if "FA1" in scan_task.other:
            fa_exc = int(scan_task.other["FA1"])
        if "FA2" in scan_task.other:
            fa_ref = int(scan_task.other["FA2"])

        if not make_tse_3D.pypulseq_tse3D(
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
                "Ordering": self.param_Ordering,
                "Plot_Timing": self.param_plot_timing,
                "dummy_shots": self.param_dummy_shots,
                "FA1": fa_exc,
                "FA2": fa_ref,
            },
            check_timing=True,
            output_file=self.seq_file_path,
            pe_order_file=self.get_working_folder() + "/rawdata/pe_order.npy",
            output_folder=self.get_working_folder(),
        ):
            log.warning("Unable to calculate sequence")
            return False

        log.info("Done calculating sequence " + self.get_name())
        self.calculated = True

        return True

    def run_sequence(self, scan_task) -> bool:
        log.info("Running sequence " + self.get_name())
        ipc_comm.send_status(f"Preparing scan...")

        expected_duration_sec = int(
            self.param_TR
            * (
                self.param_Base_Resolution * self.param_Slices / self.param_ETL
                + self.param_dummy_shots
            )
            / 1000
        )

        plot_instructions = self.param_plot_timing

        rxd, rx_t = run_pulseq(
            seq_file=self.seq_file_path,
            rf_center=cfg.LARMOR_FREQ,
            tx_t=1,
            grad_t=10,
            tx_warmup=100,
            # TODO: Debug values used here
            # shim_x=-0.01,
            # shim_y=-0.01,
            # shim_z=-0.01,
            shim_x=0.0,
            shim_y=0.0,
            shim_z=0.0,
            grad_cal=False,
            save_np=True,
            save_mat=False,
            save_msgs=False,
            gui_test=False,
            case_path=self.get_working_folder(),
            raw_filename="raw",
            expected_duration_sec=expected_duration_sec,
            plot_instructions=plot_instructions,
            hardware_simulation=config.get_config().is_hardware_simulation() == "True",
        )
        scan_task.adjustment.rf.larmor_frequency = cfg.LARMOR_FREQ

        if plot_instructions:
            file = open(self.get_working_folder() + "/other/seq.plot", "wb")
            fig = plt.gcf()
            pickle.dump(fig, file)
            file.close()

            result = ResultItem()
            result.name = "seq_plot"
            result.description = "Timing diagram of sequence"
            result.type = "plot"
            result.file_path = "other/seq.plot"
            result.autoload_viewer = 4
            scan_task.results.append(result)

        log.info("Done running sequence " + self.get_name())
        return True
