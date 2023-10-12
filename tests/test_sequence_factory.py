import sys

# setting path
sys.path.append("../")

from sequences import SequenceBase

if __name__ == "__main__":
    sequence_list = SequenceBase.registered_sequences()
    print("Installed sequences:")
    for seq in sequence_list:
        print(" - " + SequenceBase.registered_sequence(seq).get_readable_name())

    currentSequence = SequenceBase.registered_sequence("flash")()
    print(currentSequence.get_name())

    currentSequence = SequenceBase.registered_sequence("tse")()
    print(currentSequence.get_name())
    # print(isinstance(currentSequence, SequenceFlash))
