import sys

# setting path
sys.path.append("../")
sys.path.append("/opt/mri4all/console/external/")

from sequences import SequenceBase

if __name__ == "__main__":
    sequence_list = SequenceBase.installed_sequences()
    print("Installed sequences:")
    for seq in sequence_list:
        print(" - " + SequenceBase.get_sequence(seq).get_readable_name())

    currentSequence = SequenceBase.get_sequence("flash_demo")()
    print(currentSequence.get_name())

    currentSequence = SequenceBase.get_sequence("tse3d_demo")()
    print(currentSequence.get_name())
    # print(isinstance(currentSequence, SequenceFlash))
