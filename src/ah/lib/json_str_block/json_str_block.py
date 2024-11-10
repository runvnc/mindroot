import json
from partial_json_parser import loads, ensure_json
import re

def replace_raw_blocks(jsonish):
    """
    Allows embedding raw text blocks for JSON properties, e.g.:

    [ {"write": { "filename": "/test.py",
                "text": START_RAW
    def foo():
        print('hello world')


    (with optional END_RAW and continuation of JSON):

    [ {"write": { "filename": "/test.py",
                "text": START_RAW
    def foo():
        print('hello world')
    END_RAW }
    } 
    ]
    """
    final_string = ""
    in_raw = False
    raw_string = ""
    for line in jsonish.split("\n"):
        if in_raw:
            if "END_RAW" in line:
                line = line.replace("\nEND_RAW\n\"", "") 
                line = line.replace("\nEND_RAW\"", "")
                line = line.replace("\nEND_RAW", "")
                line = line.replace("END_RAW\"", "")
                line = line.replace("END_RAW", "")
                final_string += json.dumps(raw_string) + line
                in_raw = False
            else:
                raw_string += line + "\n"
        else:
            if "START_RAW" in line:
                in_raw = True
                raw_string = ""
                line = line.replace("\"START_RAW\n", "")
                line = line.replace("\"START_RAW", "")
                line = line.replace("START_RAW \n", "")
                line = line.replace("START_RAW\n", "")
                line = line.replace("START_RAW", "")
                final_string += line
            else:
                final_string += line + "\n"
    if in_raw:
        final_string += json.dumps(raw_string)

    final_string = re.sub(r'(?<!")""(?!")', '"', final_string)
    # check if parsable as partial json
    try:
        ensure_json(final_string)
    except Exception as e:
        # try converting to valid JSON string
        return json.dumps(final_string)
    return final_string


#if __name__ == "__main__":
    # read test example 1 from ex1.txt
    #with open("ex6.txt") as f:
    #    #with open("test_case_1.json") as f:
    #    jsonish = f.read()
    #new_json = replace_raw_blocks(jsonish)

    #print(new_json)

    #data = loads(new_json)

    #print('-----------------------------------------')
    #print(data)


