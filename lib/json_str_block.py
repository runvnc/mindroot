import json
# we need a partial json parser
# library. there is a good on in pypi
# here we import it:
import partialjson


# scan line by line
# does the line contain "RAWSTRING ?
# if so, put begginging part in final_string
# scan until you find another RAWSTRING"
# or run into the end of the string
# escape the raw string part as json string
# add it to the final_string
# add the rest of the line to final_string
def replace_raw_blocks(jsonish):
    final_string = ""
    in_raw = False
    raw_string = ""
    for line in jsonish.split("\n"):
        if in_raw:
            if "END_RAW" in line:
                line = line.replace("\nEND_RAW", "")
                line = line.replace("END_RAW", "")
                final_string += json.dumps(raw_string) + line
                in_raw = False
            else:
                raw_string += line + "\n"
        else:
            if "START_RAW" in line:
                in_raw = True
                raw_string = ""
                line = line.replace("START_RAW\n", "")
                line = line.replace("START_RAW", "")
                final_string += line
            else:
                final_string += line + "\n"
    return final_string


if __name__ == "__main__":
    # read test example 1 from ex1.txt
    with open("ex1.txt") as f:
        #with open("test_case_1.json") as f:
        jsonish = f.read()
    new_json = replace_raw_blocks(jsonish)

    print(new_json)

    data = json.loads(new_json)

    print('-----------------------------------------')
    print(data)


