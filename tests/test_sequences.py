import sys

# setting path
sys.path.append("../")

from sequences import SequenceBase
import common.logger as logger
import common.runtime as rt
import common.helper as helper

rt.set_service_name("tests")
log = logger.get_logger()

if __name__ == "__main__":
    log.info("Testing sequences...")

    sequence_rfse = SequenceBase.get_sequence("rfse")()
    sequence_rfse.run()

    sequence_rftse = SequenceBase.get_sequence("rftse")()
    sequence_rftse.run()

    sequence_adj_frequence = SequenceBase.get_sequence("adj_frequency")()
    sequence_adj_frequence.run()
