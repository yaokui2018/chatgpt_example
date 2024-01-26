## chatgpt_example
![GitHub last commit](https://img.shields.io/github/last-commit/yaokui2018/chatgpt_example)
![](https://img.shields.io/badge/python-3.9-blue?logo=python&logoColor=FED643)

GPT一些功能应用示例。

`openai/`: openai接口

`azure/`: 微软openai接口

### 环境依赖
`pip install openai==1.9.0`



### 1. function_calling
- 非流式输出
`python function_call/function_call_no_stream.py`
- 流式输出
`python function_call/function_call_with_stream.py`
```text
>>> 杭州今天天气怎么样？ ID 1002的用户名？

tool_calls: ChoiceDeltaToolCall(index=0, id='call_gL0GGNcJ5CqOWSSTc97wR0b1', function=ChoiceDeltaToolCallFunction(arguments='{"city": "杭州"}', name='get_weather'), type='function')
tool_calls: ChoiceDeltaToolCall(index=1, id='call_rVNFF8szfWpHPcy2G7UAC9fr', function=ChoiceDeltaToolCallFunction(arguments='{"user_id": 1002}', name='get_user_name'), type='function')
杭州今天的天气是晴天，温度为20℃。ID 1002的用户名是李四。
```
