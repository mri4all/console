import os
from sequences.adj_shim_amplitude import CalShimAmplitude
from sequences import SequenceBase
from sequences.common.util import reading_json_parameter, writing_json_parameter
from common.types import ScanTask
from common.ipc import Communicator

from common.ipc import Communicator

import common.helper as helper
import common.logger as logger
log = logger.get_logger()



def new_user_values(values):
    # gets passed in the new values ... will need to respond 
    # SET SHIMX, SHIMY, SHIMZ

    configuration_data=reading_json_parameter()

    configuration_data.shim_parameters.shim_x = values['x']/1000
    configuration_data.shim_parameters.shim_y = values['y']/1000
    configuration_data.shim_parameters.shim_z = values['z']/1000

    writing_json_parameter(config_data=configuration_data)

    print(values)


def new_signal(temp_folder):
    # Run the rf_se with the updated shim parameters
    scan_task = ScanTask()

    sequence_name = "rf_se"

    sequence_instance = SequenceBase.get_sequence(sequence_name)()
    # Get the default parameters from the sequence as an example
    scan_parameters = sequence_instance.get_default_parameters()
    scan_parameters["debug_plot"] = False
    # Configure the sequence with the default parameters. Normally, the parameters would come from the JSON file.
    sequence_instance.set_parameters(scan_parameters, scan_task)
    sequence_instance.set_working_folder(temp_folder)
    sequence_instance.calculate_sequence(scan_task)
    sequence_instance.run_sequence(scan_task)
    # return the new signal that is produced by user values. should return the FFT or whatever
    # MEASURE THE FFT OF THE SIGNAL
    rxd = abs(sequence_instance.rxd)
    return rxd.tolist()


if __name__ == "__main__":
    k = Communicator(Communicator.RECON)

    result = k.do_shim(new_user_values, new_signal)
    print("Final result", result)
    # k.shim_start()
    # while True:
    #     result = k.shim_get()
    #     print(result)
    #     k.shim_put(np.random.normal(size=20).tolist())
    #     sleep(0.1)
    #     if result.response["complete"] == True:
    #         break
    # # exit()
    # # result = k.query_user(request="test request", input_type="float")
    # r = k.show_plot(
    #     xlabel="x axis",
    #     ylabel="y axis",
    #     title="title",
    #     data=[[x**y for x in range(-10, 11)] for y in range(2, 4)],
    # )
    # print(r)

    # r = k.show_dicoms([str(x) for x in Path("/vagrant/SE000000").glob("*.dcm")])
    # print(r)
    # r = k.show_image(
    #     data=[
    #         [[0, 0, 255, 255], [0, 0, 255, 255], [255, 255, 0, 0], [255, 255, 0, 0]],
    #         [[0, 0, 255, 255], [0, 0, 255, 255], [255, 255, 0, 0], [255, 255, 0, 0]],
    #         [[0, 0, 255, 255], [0, 0, 255, 255], [255, 255, 0, 0], [255, 255, 0, 0]],
    #     ]
    # )
    # r = k.send_user_alert(message=f"You typed {r}")
