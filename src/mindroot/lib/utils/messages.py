import json

def concat_text_lists(message):
    """Concatenate text lists into a single string"""
    out_str = ''
    if isinstance(message['content'], str):
        return message
    else:
        for item in message['content']:
            if isinstance(item, str):
                out_str += item + '\n'
            elif 'text' in item:
                out_str += item['text'] + '\n'
    message.update({'content': out_str})
    return message
x = '\ndef concat_text_lists(message):\n    # if the message[\'content\'] is a list\n    # then we need to concatenate the list into a single string\n    out_str = ""\n    if isinstance(message[\'content\'], str):\n        return message\n    else:\n        for item in message[\'content\']:\n            if isinstance(item, str):\n                if len(out_str) > 0:\n                    out_str += "\n"\n                out_str += item\n            else:\n                if len(out_str) > 0:\n                    out_str += "\n"\n                out_str += item[\'text\']\n    message.update({\'content\': out_str})\n    return message\n'

def concat_all_texts(messages):
    json_str = json.dumps(messages)
    copy = json.loads(json_str)
    return [concat_text_lists(m) for m in copy]

def x(messages):
    out = concat_all_texts(messages)

def test():
    messages = [{'content': [{'text': 'a'}, {'text': 'c'}]}, {'content': 'b'}]
    x(messages)