from unstructured.partition.auto import partition
import sys

def read(filename):
    elements = partition(filename=filename)
    return elements

if __name__ == "__main__":
    elements = read(sys.argv[1])
    print("\n\n-----------------------------------------------------------------------\n\n".join([str(el) for el in elements]))

