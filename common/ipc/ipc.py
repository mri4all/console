import atexit
import json
import os
from pathlib import Path
from typing import Any, Dict, Literal, Optional, Union
from uuid import uuid5
import uuid

from PyQt5.QtCore import pyqtSignal, pyqtSlot, QObject
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

import common.logger as logger
import threading
from pydantic import BaseModel

from common.constants import *
from common.ipc.messages import *

class PipeFile(Enum):
    RECON = "recon_pipe"
    ACQ = "acq_pipe"
    UI_RECON = "ui_recon_pipe"
    UI_ACQ = "ui_recon_acq"

    
class CommunicatorEnvelope(BaseModel):
    # TODO: Add missing entries from registration form
    id: str = str(uuid.uuid1())
    value: Union[UserResponseMessage, UserQueryMessage, UserAlertMessage, SetStatusMessage]
    error: bool = False


log = logger.get_logger()

class PipeEnd(Enum):
    RECON = (PipeFile.RECON, PipeFile.UI_RECON)
    ACQ = (PipeFile.ACQ, PipeFile.UI_ACQ)
    UI_ACQ = (PipeFile.UI_ACQ,PipeFile.ACQ)
    UI_RECON = (PipeFile.UI_RECON, PipeFile.RECON)

class Communicator(QObject, Helper):
    RECON = PipeEnd.RECON
    ACQ = PipeEnd.ACQ
    UI_ACQ = PipeEnd.UI_ACQ
    UI_RECON = PipeEnd.UI_RECON

    recieved = pyqtSignal(object)
    receive_thread = None
    base = "/tmp/mri4all/pipes"
    pipe_end = None
    def __init__(self, pipe_end: PipeEnd):
        in_, out_ = pipe_end.value
        self.pipe_end = pipe_end
        super().__init__()
        Path(self.base).mkdir(parents=True,exist_ok=True)

        self.in_file = str(Path(self.base,in_.value))
        self.out_file = str(Path(self.base,out_.value))

        self.mkfifo(str(self.in_file))
        atexit.register(self.cleanup)


    def is_open(self):
        if not os.path.exists(self.out_file):
            return False
        return True

    def cleanup(self):
        os.unlink(self.in_file)

    def listen(self):
        if (self.receive_thread):
            raise Exception("already listening")
        self.receive_thread = threading.Thread(target=self._listen_emit, daemon=True)
        self.receive_thread.start()

    def _send(self, obj:FifoMessageType, error=False):
        if not os.path.exists(self.out_file):
            return False
        with open(self.out_file,"w") as f:
            f.write(CommunicatorEnvelope(value=obj,error=error).model_dump_json())
        return True

    def _query(self, obj):
        if not self._send(obj):
            raise Exception("Other end of the pipe is not available.")

        result = next(self._listen())
        if result.error:
            raise Exception()
        return result.value
        
    def parse(self,line):
        print(json.loads(line))
        return CommunicatorEnvelope(**json.loads(line))

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
    k = Communicator(Communicator.RECON)
    result = k.query_user(request="test request",input_type="float")
    k.send_user_alert(message=f"You typed {result}")