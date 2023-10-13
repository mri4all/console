import sys

# setting path
sys.path.append("../")

from sequences import SequenceBase


if __name__ == "__main__":
    sequence_rfse = SequenceBase.get_sequence("rfse")()
    sequence_rfse.run()

    sequence_rftse = SequenceBase.get_sequence("rftse")()
    sequence_rftse.run()

    sequence_adj_frequence = SequenceBase.get_sequence("adj_frequency")()
    sequence_adj_frequence.run()
