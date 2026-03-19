from pathlib import Path
import external.seq.adjustments_acq.config as cfg
from external.seq.adjustments_acq.calibration import (
    larmor_cal,
    larmor_step_search,
    load_plot_in_ui,
)
from sequences.common.util import reading_json_parameter, writing_json_parameter
from sequences import PulseqSequence  # type: ignore
from sequences.common import make_rf_se  # type: ignore
import common.logger as logger
import matplotlib.pyplot as plt
import numpy as np
import pickle
from common.types import ResultItem
log = logger.get_logger()


class AdjFrequency(PulseqSequence, registry_key=Path(__file__).stem):
    # Sequence parameters
    param_TE: int = 10
    param_TR: int = 250
    param_NSA: int = 1
    param_ADC_samples: int = 512
    param_ADC_duration: int = 5120

    @classmethod
    def get_readable_name(self) -> str:
        return "Adjust Frequency (SNR) [on startup]"

    def calculate_sequence(self, scan_task) -> bool:
        log.info("Calculating sequence " + self.get_name())

        scan_task.processing.recon_mode = "bypass"
        self.seq_file_path = self.get_working_folder() + "/seq/acq0.seq"
        log.info('Working folder:'+ str(self.get_working_folder()))
        make_rf_se.pypulseq_rfse(
            inputs={
                "TE": self.param_TE,
                "TR": self.param_TR,
                "NSA": self.param_NSA,
                "ADC_samples": self.param_ADC_samples,
                "ADC_duration": self.param_ADC_duration,
                "FA1": 90,
                "FA2": 180,
            },
            check_timing=True,
            output_file=self.seq_file_path,
        )

        self.calculated = True
        log.info("Done calculating sequence " + self.get_name())
        return True

    def run_sequence(self, scan_task) -> bool:
        log.info("Running sequence " + self.get_name())

        # Read scanner configuration data from config.json
        # TODO: Needs to be reworked
        configuration_data = reading_json_parameter()
        working_folder = self.get_working_folder()

        # TODO: Convert to classes later (using external packages for now)
        log.info("Starting frequency adjustment using SNR - coarse search")
        (
            max_peak_freq,
            max_snr_freq,
            data_dict,
            fig_snr_signal1,
            fig_snr_noise1,
            best_snr_index,
        ) = larmor_step_search(
            seq_file=self.seq_file_path,
            step_search_center=scan_task.adjustment.rf.larmor_frequency,
            steps=10,
            step_bw_MHz=1e-3,
            plot=True,  # For Debug
            shim_x=cfg.SHIM_X,
            shim_y=cfg.SHIM_Y,
            shim_z=cfg.SHIM_Z,
            delay_s=1,
            gui_test=False,
            dummy_scans=1,
        )
        
        log.info('Starting frequency adjustment using SNR - fine search') #TODO: pick peak frequency instead of SNR at this stage
        (
            max_freq_fine,
            max_snr_freq_fine,
            data_dict_fine,
            fig_snr_signal1,
            fig_snr_noise1,
            best_snr_index,
        ) = larmor_step_search(
            seq_file=self.seq_file_path,
            step_search_center=max_snr_freq,
            steps=10,
            step_bw_MHz=0.1e-3,
            plot=True,  # For Debug
            shim_x=cfg.SHIM_X,
            shim_y=cfg.SHIM_Y,
            shim_z=cfg.SHIM_Z,
            delay_s=1,
            gui_test=False,
            dummy_scans=1,        
            )
        
        log.info('Starting frequency adjustment using SNR - second fine search') #TODO: pick peak frequency instead of SNR at this stage
        (
            max_freq_fine,
            max_snr_freq_fine2,
            data_dict_fine,
            fig_snr_signal1,
            fig_snr_noise1,
            best_snr_index,
        ) = larmor_step_search(
            seq_file=self.seq_file_path,
            step_search_center=max_snr_freq_fine,
            steps=10,
            step_bw_MHz=0.05e-3,
            plot=True,  # For Debug
            shim_x=cfg.SHIM_X,
            shim_y=cfg.SHIM_Y,
            shim_z=cfg.SHIM_Z,
            delay_s=1,
            gui_test=False,
            dummy_scans=1,        
            )


        # calibrated_larmor_freq = max_snr_freq_fine
        calibrated_larmor_freq = max_snr_freq_fine2
        data_dict["rx_arr"] = data_dict_fine["rx_arr"]
        log.info(f"Calibrated Larmor frequency (using SNR) - Coarse: {max_snr_freq} MHz")
        log.info(f"Calibrated Larmor frequency (using SNR) - fine: {calibrated_larmor_freq} MHz")



        rx_signal = data_dict["rx_arr"]
        log.info(f"Shape of rx signal: {rx_signal.shape}")
        log.info('Read the signal')

        plt.clf()
        plt.title("ADC Signal Final")
        plt.grid(True, color="#333")
        plt.plot(np.abs(rx_signal), label="ADC Signal")
        plt.xlabel("Time [n]")
        plt.ylabel("Amplitude [a.u.]")
        file = open(self.get_working_folder() + "/other/plot_snr_result.plot", "wb")
        fig = plt.gcf()
        pickle.dump(fig, file)
        file.close()

        result = ResultItem()
        result.name = "ADC"
        result.description = "Recorded ADC signal"
        result.type = "plot"
        result.primary = True
        result.autoload_viewer = 1
        result.file_path = "other/plot_snr_result.plot"
        scan_task.results.append(result)


        # plot_snr_result_signal1 = load_plot_in_ui(
        #     working_folder=working_folder,
        #     file_name="plot_snr_result_signal1",
        #     fig=fig_snr_signal1,
        # )
        # scan_task.results.append(plot_snr_result_signal1)
        # plot_snr_result_noise1 = load_plot_in_ui(
        #     working_folder=working_folder,
        #     file_name="plot_snr_result_noise1",
        #     fig=fig_snr_noise1,
        # )
        # scan_task.results.append(plot_snr_result_noise1)

        # ----------------------
        
        # calibrated_larmor_freq_opt, data_dict, fig_snr1 = larmor_cal(
        #     seq_file=self.seq_file_path,
        #     larmor_start=max_snr_freq_fine,
        #     iterations=10,
        #     delay_s=1,
        #     echo_count=1,
        #     step_size=0.6,
        #     plot=True,  # For debug
        #     shim_x=cfg.SHIM_X,
        #     shim_y=cfg.SHIM_Y,
        #     shim_z=cfg.SHIM_Z,
        #     gui_test=False,
        # )

        # plot_snr_result1 = load_plot_in_ui(
        #     working_folder=working_folder, file_name="plot_snr_result1", fig=fig_snr1
        # )
        # scan_task.results.append(plot_snr_result1)

        # calibrated_larmor_freq, data_dict, fig_snr2 = larmor_cal(
        #     seq_file=self.seq_file_path,
        #     larmor_start=larmor_freq,
        #     iterations=20,
        #     delay_s=1,
        #     echo_count=1,
        #     step_size=0.2,
        #     plot=True,  # For debug
        #     shim_x=cfg.SHIM_X,
        #     shim_y=cfg.SHIM_Y,
        #     shim_z=cfg.SHIM_Z,
        #     gui_test=False,
        # )

        # plot_snr_result2 = load_plot_in_ui(
        #     working_folder=working_folder, file_name="plot_snr_result2", fig=fig_snr2
        # )
        # scan_task.results.append(plot_snr_result2)

        # calibrated_larmor_freq = calibrated_larmor_freq_opt
        # calibrated_larmor_freq = opt_max_snr_freq
        log.info(f"Final Larmor frequency (using SNR): {calibrated_larmor_freq} MHz")
        # updating the Larmor frequency in the config.json file
        configuration_data.rf_parameters.larmor_frequency_MHz = calibrated_larmor_freq
        scan_task.adjustment.rf.larmor_frequency = calibrated_larmor_freq
        writing_json_parameter(config_data=configuration_data)
        # Reload the configuration -- otherwise it does not get updated until the next start
        cfg.update()

        log.info("Done running sequence " + self.get_name())
        return True
