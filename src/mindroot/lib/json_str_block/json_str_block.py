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
    final_string = ''
    in_raw = False
    raw_string = ''
    lines = jsonish.split('\n')
    lines_ = []
    for line_ in lines:
        if 'START_RAW' in line_:
            all = line_.split('\\n')
            for a in all:
                lines_.append(a)
        elif 'END_RAW' in line_:
            all = line_.split('\\n')
            for a in all:
                lines_.append(a)
        else:
            lines_.append(line_)
    for line in lines_:
        if in_raw:
            if 'END_RAW' in line:
                line = line.replace('\\nEND_RAW\n"', '')
                line = line.replace('\nEND_RAW\n"', '')
                line = line.replace('\nEND_RAW"', '')
                line = line.replace('\nEND_RAW', '')
                line = line.replace('END_RAW"', '')
                line = line.replace('END_RAW', '')
                final_string += json.dumps(raw_string) + line
                in_raw = False
            else:
                raw_string += line + '\n'
        elif 'START_RAW' in line:
            in_raw = True
            raw_string = ''
            line = line.replace('"START_RAW\\n', '')
            line = line.replace('"START_RAW\n', '')
            line = line.replace('"START_RAW', '')
            line = line.replace('START_RAW \n', '')
            line = line.replace('START_RAW\n', '')
            line = line.replace('START_RAW', '')
            final_string += line
        else:
            final_string += line + '\n'
    if in_raw:
        final_string += json.dumps(raw_string)
    final_string = re.sub('(?<!")""(?!")', '"', final_string)
    if 'START_RAW' in final_string:
        final_string = final_string.replace('START_RAW', '"')
    try:
        ensure_json(final_string)
    except Exception as e:
        escaped_nl_in_fenced = re.sub('```[\\s\\S]*?```', lambda m: m.group(0).replace('\n', '\\n'), final_string)
        try:
            ensure_json(escaped_nl_in_fenced)
            return escaped_nl_in_fenced
        except Exception as e:
            try:
                final_string = final_string.strip().replace('\n', '\\n')
                ensure_json(final_string)
                return final_string
            except Exception as e:
                return final_string
    return final_string
if __name__ == '__main__':
    with open('ex9.txt') as f:
        jsonish = f.read()
    new_json = replace_raw_blocks(jsonish)
    data = loads(new_json)