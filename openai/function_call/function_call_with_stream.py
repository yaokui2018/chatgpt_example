# -*- coding: utf-8 -*-
# Author: 薄荷你玩
# Date: 2024/01/26

from openai import OpenAI
import json

api_key = "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
# api_base = "https://api.openai.com/v1"

# client = OpenAI(api_key=api_key, base_url=api_base)
client = OpenAI(api_key=api_key)


def get_user_name(user_id: int):
    """
    根据用户id获取用户名（模拟）
    :param user_id: 用户ID
    :return:
    """
    if user_id == 1001:
        return "张三"
    elif user_id == 1002:
        return "李四"
    else:
        return "-"


def get_weather(city: str, date: str = None):
    """
    获取城市当天天气信息（模拟）
    :param city: 城市名
    :param date: 日期（暂时不使用）
    :return:
    """
    data = {}
    if city == "杭州":
        data['weather'] = "晴天"
        data['temperature'] = "20℃"
    elif city == "北京":
        data['weather'] = "中雨"
        data['temperature'] = "15℃"

    return json.dumps(data)


def gpt_ask_with_stream(messages: list[dict], tools: list[dict]):
    response = client.chat.completions.create(
        model="gpt-4-0125-preview",
        messages=messages,
        tools=tools,
        tool_choice="auto",
        stream=True
    )
    tool_calls = []
    for chunk in response:
        # print("***", chunk)
        if chunk.choices:
            choice = chunk.choices[0]
            if choice.delta.tool_calls:  # function_calling
                for idx, tool_call in enumerate(choice.delta.tool_calls):
                    tool = choice.delta.tool_calls[idx]

                    # 2024-03-27 兼容 gpt-4-0125-preview/gpt-4-1106-preview
                    if tool_call.index:
                        idx = max(tool_call.index, idx)

                    if len(tool_calls) <= idx:
                        tool_calls.append(tool)
                        continue
                    if tool.function.arguments:
                        # function参数为流式响应，需要拼接
                        tool_calls[idx].function.arguments += tool.function.arguments
            elif choice.finish_reason:
                # print(f"choice.finish_reason: {choice.finish_reason}")
                break
            elif not choice.delta.content:  # 2024-03-27 兼容 gpt-4-0125-preview/gpt-4-1106-preview（首条chunk无实际数据）
                continue
            else:  # 普通回答
                yield ""  # 第一条返回无意义，便于后续检测回复消息类型
                yield choice.delta.content

    # 如果是function_call请求，返回数据
    if tool_calls:
        yield tool_calls


def run_conversation(content: str):
    messages = [{"role": "user", "content": content}]
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "获取城市今天的天气信息",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "enum": ["杭州", "北京"],
                            "description": "城市名",
                        },
                        "date": {
                            "type": "string",
                            "description": "查询的日期，格式：%Y-%m-%d。默认为当天日期",
                        }
                    },
                    "required": ["city"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_user_name",
                "description": "根据用户id获取用户名",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "integer",
                            "description": "用户id",
                        }
                    },
                    "required": ["user_id"],
                },
            },
        }
    ]

    response = gpt_ask_with_stream(messages, tools)
    tool_calls = []
    for res in response:
        # 如果响应数据第一条是list则表明是function_call，如果是str就是普通回答
        if type(res) == list:
            tool_calls = res
        break
    # 判断是否是 function_call 请求
    while tool_calls:
        available_functions = {
            "get_weather": get_weather,
            "get_user_name": get_user_name
        }
        # 手动构建gpt返回消息，tool_calls暂时置空，后面循环调用function的时候再赋值
        assistant_message = {
            "role": "assistant",
            "tool_calls": [],
            "content": None
        }
        messages.append(assistant_message)
        # send the info for each function call and function response to the model
        for tool_call in tool_calls:
            print("tool_calls:", tool_call)
            assistant_message['tool_calls'].append({
                "id": tool_call.id,
                "type": tool_call.type,
                "function": {
                    "name": tool_call.function.name,
                    "arguments": tool_call.function.arguments
                }
            })
            function_name = tool_call.function.name
            function_to_call = available_functions[function_name]
            function_args = json.loads(tool_call.function.arguments)
            if function_name == 'get_weather':
                function_response = function_to_call(
                    city=function_args.get("city"),
                    date=None,
                )
            else:
                function_response = function_to_call(
                    user_id=function_args.get("user_id"),
                )
            messages.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": function_name,
                "content": function_response,
            })
        # 携带 function 返回的结果再请求一次GPT
        response = gpt_ask_with_stream(messages, tools)
        # 和 while 前面写法一样，支持多轮tools调用
        tool_calls = []
        for res in response:
            if type(res) == list:
                tool_calls = res
            break
    # 返回普通回答的流式响应
    return response


if __name__ == '__main__':
    for chunk in run_conversation("杭州今天天气怎么样？ ID 1002的用户名？"):
        print(chunk, end='')
    # 输出：
    # tool_calls: ChoiceDeltaToolCall(index=0, id='call_5jSbeoAcUqDmZRXS70iVKbrL', function=ChoiceDeltaToolCallFunction(arguments='{\n  "city": "杭州"\n}', name='get_weather'), type='function')
    # tool_calls: ChoiceDeltaToolCall(index=0, id='call_ppgzqcbHAeDnfklMznrOG7lh', function=ChoiceDeltaToolCallFunction(arguments='{\n  "user_id": 1002\n}', name='get_user_name'), type='function')
    # 杭州今天是晴天，温度为20℃。ID 1002的用户名是李四。
