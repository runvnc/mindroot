import json
import re
from partial_json_parser import loads as partial_json_loads

test="""
[{"say": {"text": "Wow, that's actually a really fascinating project - especially from my perspective as an AI agent!"}}][{"say": {"text": "Building a framework like that is definitely ambitious - there are so many moving parts to consider."}}][{"say": {"text": "Given how you're feeling right now, would you like to talk through just one small piece you could work on? Maybe something simple like documenting a single feature or testing one small component?"}}][{"say": {"text": "Sometimes with big projects, doing even a tiny bit helps keep the momentum going."}}]
"""

test2="""
[{"say": {"text": "Wow, that's actually a really fascinating project - especially from my perspective as an AI agent!"}}], [{"say": {"text": "Building a framework like that is definitely ambitious - there are so many moving parts to consider."}}][{"say": {"text": "Given how you're feeling right now, would you like to talk through just one small piece you could work on? Maybe something simple like documenting a single feature or testing one small component?"}}][{"say": {"text": "Sometimes with big projects, doing even a tiny bit helps keep the momentum going."}}]
"""

test3="""
[{"think": {"extensive_chain_of_thoughts": "Let me review each route file for missing imports:\n\n1. upload_routes.py:\n- Needs traceback for error handling\n\n2. processing_routes.py:\n- Needs datetime for timestamp handling\n- Needs to import load_financial_assumptions\n\n3. results_routes.py:\n- Needs datetime for current_datetime usage\n\n4. common.py looks complete\n\nLet me update these files one at a time with the missing imports."}}], {"write": {"fname": "/xfiles/maverickcre/plugins/cre_b
"""

def merge_json_arrays(data, partial=False):
    #print("merge_json_arrays, partial=", partial)
    if partial:
        load_json = partial_json_loads
        ##print("load_json is partial_json_loads")
    else:
        ##print("load_json is json.loads")
        load_json = json.loads

    return load_json(data)

    xxx = """
    data = data.strip()
    parts = re.split(r"\]\s*,*\s*\[", data)
    if len(parts) == 1 and parts[0] == data:
        parts = re.split(r"\]\s*,*\s*\{", data)
    arrays = []
    for part in parts:
        if part.startswith("{"):
            part = "[" + part
        if not part.startswith("["):
            part = "[" + part
        if part.endswith(","):
            part = part[:-1].strip()
        if part.endswith('}') and not part.endswith("]"):
            part += "]"
        try:
            arrays.append(load_json(part))
        except Exception as e:
            try:
                part = part.replace("\n", "\\n")
                # if ends with \\n, remove it
                if part.endswith("\\n"):
                    part = part[:-2]
                part = part.strip()
                if not part.startswith('[{') and part.startswith('["'):
                    part = "[{" + part[1:]
                arrays.append(load_json(part))
            except Exception as e:
                pass
                ##print("Error parsing part: ", part)
                ##print(e)

    ##print("returning sum(arrays, []):", sum(arrays, []))
    #ret = sum(arrays, [])
    ret = list(chain.from_iterable(arrays))
    return ret
    """

#ret = merge_json_arrays(test3, False)
##print("successful parsing")
#for item in ret:
#    #print('-----------------------------------')
#    #print(item)
#    #print('-----------------------------------')

