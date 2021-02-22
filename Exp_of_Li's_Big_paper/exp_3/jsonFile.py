import json


# 从文件获取需要调整的参数的 json 对象
def get_args_json():
    with open("args.json", 'r', encoding='utf-8') as f:
        return json.load(f)


# 写入 json 参数对象到文件中
def write_args_json(json_obj):
    with open("args.json", 'w', encoding='utf-8') as f:
        json.dump(json_obj, f)

# 从文件获取需要调整的参数的 json 对象
def get_sendDelay():
    with open("sendDelay.json", 'r', encoding='utf-8') as f:
        return float(json.load(f))


# 写入 json 参数对象到文件中
def write_sendDelay(json_obj):
    with open("sendDelay.json", 'w', encoding='utf-8') as f:
        json.dump(json_obj, f)


