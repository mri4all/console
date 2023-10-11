import sys

# setting path
sys.path.append("../")

from sequences import SequenceBase

if __name__ == "__main__":
    print(SequenceBase.registered_sequences())

    currentSequence = SequenceBase.registered_sequence("flash")()
    print(currentSequence.get_name())

    currentSequence = SequenceBase.registered_sequence("tse")()
    print(currentSequence.get_name())
    # print(isinstance(currentSequence, SequenceFlash))
