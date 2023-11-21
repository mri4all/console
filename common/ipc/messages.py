import os
import common.logger as logger


from time import sleep
from typing import Any, Dict, List, Literal, Optional, Union
import numpy as np
from pydantic import BaseModel

import common.helper as helper_common
from common.types import IntensityMapResult, TimeSeriesResult


class FifoMessageType(BaseModel):
    pass


class SimpleMessage(FifoMessageType):
    type: Literal["simple"] = "simple"
    message: str


class SetStatusMessage(FifoMessageType):
    type: Literal["set_status"] = "set_status"
    message: str


class UserQueryMessage(FifoMessageType):
    type: Literal["user_query"] = "user_query"
    input_type: Literal["text", "int", "float"] = "text"
    in_min: Union[float, int] = 0
    in_max: Union[float, int] = 1000
    request: str


class UserResponseMessage(FifoMessageType):
    type: Literal["user_response"] = "user_response"
    response: Optional[Union[float, int, str, dict]] = None


class UserAlertMessage(FifoMessageType):
    type: Literal["user_alert"] = "user_alert"
    message: str
    alert_type: Literal["information", "warning", "critical"] = "information"


class ShowPlotMessage(FifoMessageType):
    type: Literal["show_plot"] = "show_plot"
    plot: Union[TimeSeriesResult, IntensityMapResult]


class ShowDicomMessage(FifoMessageType):
    type: Literal["show_dicom"] = "show_dicom"
    dicom_files: List[str]


class DoShimMessage(FifoMessageType):
    type: Literal["shim"] = "shim"
    message: Literal["start", "put", "get"]
    data: Optional[List[Any]] = None


class AcqDataMessage(FifoMessageType):
    type: Literal["acq_data"] = "acq_data"
    start_time: str
    expected_duration_sec: int = 0
    disable_statustimer: bool = False


class Helper:
    def show_dicoms(self, dicoms: List[str]):
        return self._query(ShowDicomMessage(dicom_files=dicoms))

    def do_shim(self, new_user_values, new_signal, signal_tick_mul=4, values_tick=0.1):
        log = logger.get_logger()
        self.shim_start()

        temp_folder = "/tmp/" + helper_common.generate_uid()

        try:
            os.mkdir(temp_folder)
            os.mkdir(temp_folder + "/other")
            os.mkdir(temp_folder + "/dicom")
            os.mkdir(temp_folder + "/rawdata")
        except:
            log.error(f"Could not create temporary folder {temp_folder}.")

        n = 0
        while True:
            result = self.shim_get()
            new_user_values(result.response["values"])
            if result.response["complete"] == True:
                return result.response["values"]
            if n >= signal_tick_mul:
                n = 0
                self.shim_put(new_signal(temp_folder))
            n = n + 1
            sleep(values_tick)

    def shim_start(self):
        return self._query(DoShimMessage(message="start"))

    def shim_get(self):
        return self._query(DoShimMessage(message="get"))

    def shim_put(self, data):
        self._send(DoShimMessage(message="put", data=data))

    def show_image(
        self,
        plot: Optional[IntensityMapResult] = None,
        *,
        xlabel: str = "",
        ylabel: str = "",
        title: str = "",
        data: Union[List[List[Any]], List[List[List[Any]]]],
        fmt: Union[str, list[str]] = [],
    ):
        if not plot:
            plot = IntensityMapResult(
                xlabel=xlabel, ylabel=ylabel, title=title, data=data
            )
        return self._query(ShowPlotMessage(plot=plot))

    def show_plot(
        self,
        plot: Optional[TimeSeriesResult] = None,
        *,
        xlabel: str = "",
        ylabel: str = "",
        title: str = "",
        data: Union[List[List[float]], List[float]],
        fmt: Union[str, list[str]] = [],
    ):
        if not plot:
            plot = TimeSeriesResult(
                xlabel=xlabel, ylabel=ylabel, title=title, data=data, fmt=fmt
            )
        return self._query(ShowPlotMessage(plot=plot))

    def send_user_response(self, response=None, error=False):
        """
        Sends the user's response from the UI.
        """
        return self._send(UserResponseMessage(response=response), error=error)

    def send_user_alert(
        self,
        message: str,
        type: Literal["information", "warning", "critical"] = "information",
    ):
        """
        Present the user with an alert box.
        type: Whether the alert looks like an infobox, warning, or critical error
        """
        return self._query(UserAlertMessage(message=message, alert_type=type))

    def query_user(
        self,
        request,
        input_type: Optional[Literal["text", "int", "float"]] = None,
        in_min: Optional[Union[int, float]] = None,
        in_max: Optional[Union[int, float]] = None,
    ) -> Optional[Union[str, int, float]]:
        """
        Present the user with an input dialog.
        input_type: Which kind of input dialog. Interprets result as this type.
        in_min, in_max: the min/max value for a float or integer type.
            Default minimum: 0
            Default maximum: 1000
        """
        args: Dict[str, Any] = {}
        if input_type is not None:
            args["input_type"] = input_type
        if in_min is not None:
            args["in_min"] = in_min
        if in_max is not None:
            args["in_max"] = in_max

        return self._query(UserQueryMessage(request=request, **args)).response

    def send_status(self, message: str):
        return self._send(SetStatusMessage(message=message))

    def _send(self, x: FifoMessageType, error=False):
        pass

    def _query(self, x: FifoMessageType):
        pass

    def send_acq_data(
        self,
        start_time: str,
        expected_duration_sec: int = -1,
        disable_statustimer: bool = False,
    ):
        return self._send(
            AcqDataMessage(
                start_time=start_time,
                expected_duration_sec=expected_duration_sec,
                disable_statustimer=disable_statustimer,
            )
        )
