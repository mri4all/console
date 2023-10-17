import atexit
import errno
import json
from operator import truediv
import os
from pathlib import Path
from typing import Literal, Optional, Union
from uuid import uuid5
import uuid
from PyQt5.QtCore import pyqtSignal, pyqtSlot, QObject
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

import common.logger as logger
import threading
from pydantic import BaseModel

import common.helper as helper
from common.constants import *
import services.ui.ui_runtime as ui_runtime

class PipeFile(Enum):
    RECON = "recon_pipe"
    ACQ = "acq_pipe"
    UI_RECON = "ui_recon_pipe"
    UI_ACQ = "ui_recon_acq"

class FifoMessageType(BaseModel):
    pass

class SimpleMessage(FifoMessageType):
    type: Literal["simple"] = "simple"
    message: str

class SetStatusMessage(FifoMessageType):
    type: Literal["set_status"] = "set_status"
    message: str

    # def __init__(self, message):
    #     super().__init__(message=message)

class UserQueryMessage(FifoMessageType):
    type: Literal["user_query"] = "user_query"
    input_type: Literal["text","int","float"] = "text"
    in_min: Union[float, int] = 0
    in_max: Union[float, int] = 1000
    request: str

class UserResponseMessage(FifoMessageType):
    type: Literal["user_response"] = "user_response"
    response: Optional[Union[float,int,str]] = None

class UserAlertMessage(BaseModel):
    type: Literal["user_alert"] = "user_alert"
    message: str
    alert_type: Literal["information", "warning", "critical"] = "information"

    
class Message(BaseModel):
    # TODO: Add missing entries from registration form
    id: str = str(uuid.uuid1())
    value: Union[UserResponseMessage, UserQueryMessage, UserAlertMessage, SetStatusMessage]
    error: bool = False


log = logger.get_logger()

class FifoPipe(QObject):
    recieved = pyqtSignal(object)
    receive_thread = None
    base = "/tmp/mri4all/pipes"

    def __init__(self,in_, out_):
        super().__init__()
        Path(self.base).mkdir(parents=True,exist_ok=True)

        self.in_file = str(Path(self.base,in_.value))
        self.out_file = str(Path(self.base,out_.value))

        self.mkfifo(str(self.in_file))
        atexit.register(self.cleanup)

    def cleanup(self):
        os.unlink(self.in_file)

    def listen(self):
        self.receive_thread = threading.Thread(target=self._listen_emit, daemon=True)
        self.receive_thread.start()

    def send(self, obj, error=False):
        print(f"send to {self.out_file}")
        if not os.path.exists(self.out_file):
            return False
        with open(self.out_file,"w") as f:
            f.write(Message(value=obj,error=error).model_dump_json())
        return True

    def query(self, obj):
        if not self.send(obj):
            raise Exception("Other end of the pipe is not available.")

        result = next(self._listen())
        if result.error:
            raise Exception()
        return result.value
        
    def parse(self,line):
        print(json.loads(line))
        return Message(**json.loads(line))

    def mkfifo(self, FIFO):
        try:
            os.mkfifo(FIFO)
        except FileExistsError:
            os.unlink(FIFO)
            os.mkfifo(FIFO)

    def _listen(self):
        while True:
            with open(self.in_file) as fifo:
                for line in fifo:
                    yield self.parse(line)


    def _listen_emit(self):
        for o in self._listen():
            self.recieved.emit(o)
            # self.handle(o)


if __name__=="__main__":
    k = FifoPipe(PipeFile.RECON, PipeFile.UI_RECON)
    # result = k.query(UserQueryMessage(request="test request",input_type="float"))
    k.send(SetStatusMessage(message="OK"))