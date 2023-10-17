from typing import Any, Dict, Literal, Optional, Union
from pydantic import BaseModel

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

class Helper():
    def send_user_response(self, response=None, error=False):
        """
        Sends the user's response from the UI.
        """
        return self._send(UserResponseMessage(response=response),error=error)

    def send_user_alert(self, message:str, type: Literal["information", "warning", "critical"] = "information"):
        """
        Present the user with an alert box. 
        type: Whether the alert looks like an infobox, warning, or critical error
        """
        return self._send(UserAlertMessage(message=message,alert_type=type))

    def query_user(self, request, input_type:Optional[Literal["text","int","float"]]=None, in_min:Optional[Union[int,float]]=None, in_max:Optional[Union[int,float]]=None) -> Optional[Union[str,int,float]]:
        """
        Present the user with an input dialog. 
        input_type: Which kind of input dialog. Interprets result as this type.
        in_min, in_max: the min/max value for a float or integer type. 
        """
        args:Dict[str,Any] = {}
        if input_type is not None:
            args["input_type"] = input_type
        if in_min is not None:
            args["in_min"] = in_min
        if in_max is not None:
            args["in_max"] = in_max

        return self._query(UserQueryMessage(request=request,**args)).response
    
    def send_status(self, message:str):
        return self._send(SetStatusMessage(message=message))

    def _send(self, x, error=False):
        pass
    def _query(self,x):
        pass