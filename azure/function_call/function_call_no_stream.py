# -*- coding: utf-8 -*-
# Author: 薄荷你玩
# Date: 2024/01/26

from openai import AzureOpenAI
import json

api_key = "xxxxxxxxxxxxxxxxxxxxxxxxxxxx"
api_url = 'https://xxxx.openai.azure.com'
azure_openai_client = AzureOpenAI(api_key=api_key, api_version="2023-12-01-preview", azure_endpoint=api_url)


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

    response = azure_openai_client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        tools=tools,
        tool_choice="auto",
    )
    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls
    # 判断是否是 function_call 请求
    if tool_calls:
        available_functions = {
            "get_weather": get_weather,
            "get_user_name": get_user_name
        }
        messages.append(response_message)
        # send the info for each function call and function response to the model
        for tool_call in tool_calls:
            print("tool_calls:", tool_call)
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
        second_response = azure_openai_client.chat.completions.create(
            model='gpt-4',
            messages=messages,
        )
        return second_response.choices[0].message


if __name__ == '__main__':
    print(run_conversation("杭州今天天气怎么样？"))
    print(run_conversation("ID 1002的用户名？").content)
    # 输出：
    # tool_calls: ChatCompletionMessageToolCall(id='call_7wLKbqsCQh2n9vOkzxnnyznK', function=Function(arguments='{"city":"杭州"}', name='get_weather'), type='function')
    # ChatCompletionMessage(content='杭州今天天气是晴天，气温大概是20°C。', role='assistant', function_call=None, tool_calls=None)
    # tool_calls: ChatCompletionMessageToolCall(id='call_uxqXCkWIu6pqmr8smLIi2WOH', function=Function(arguments='{"user_id":1002}', name='get_user_name'), type='function')
    # ID 1002的用户名是李四。
