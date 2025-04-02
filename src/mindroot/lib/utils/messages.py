import json

def concat_text_lists(message):
    """Concatenate text lists into a single string"""
    # if the message['content'] is a list
    # then we need to concatenate the list into a single string
    out_str = ""
    if isinstance(message['content'], str):
        return message
    else:
        for item in message['content']:
            if isinstance(item, str):
                out_str += item + "\n"
            else:
                if 'text' in item:
                    out_str += item['text'] + "\n"
    message.update({'content': out_str})
    return message


x ="""
def concat_text_lists(message):
    # if the message['content'] is a list
    # then we need to concatenate the list into a single string
    out_str = ""
    if isinstance(message['content'], str):
        return message
    else:
        for item in message['content']:
            if isinstance(item, str):
                if len(out_str) > 0:
                    out_str += "\n"
                out_str += item
            else:
                if len(out_str) > 0:
                    out_str += "\n"
                out_str += item['text']
    message.update({'content': out_str})
    return message
"""


def concat_all_texts(messages):
    json_str = json.dumps(messages)
    copy = json.loads(json_str)
    return [concat_text_lists(m) for m in copy]


def x(messages):
    out = concat_all_texts(messages)
    print(out) 

def test():
    messages = [ 
        { "content": [ { "text": "a"}, { "text" :"c" } ] }, 
          { "content": "b" } 
    ]
    x(messages)
    print(messages)

#test()

