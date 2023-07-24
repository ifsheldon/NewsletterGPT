import json

from func_timeout import func_set_timeout

from newletter_gpt.feeds import FeedItem, Tags
import logging
import openai

logger = logging.getLogger("NewsletterGPT")


@func_set_timeout(40.0)
def gen_summary_and_tags_via_llm(feed_item: FeedItem,
                                 api_base: str,
                                 api_key: str,
                                 chatgpt_deployment_name: str):
    # set up openai
    openai.api_key = api_key
    openai.api_version = "2023-07-01-preview"
    openai.api_type = "azure"
    openai.api_base = api_base
    # truncate content, max ~5000 Chinese and English character
    item_content = feed_item.content[:7000]
    function_name = "article_record"
    logger.info(f"Generating summary and tags for \"{feed_item.title}\"")
    user_message = f"""
帮我总结文章并且给文章打标签。

文章题目：{feed_item.title}
文章全文：
```
{item_content}
```

英文专业名词要保留，然后请用中文生成简短的不超过300字的文章总结。


根据以上信息，给文章打标签。可用的标签有：
aigc: 生成式AI，大语言模型，文生图模型等的相关内容
digital_human: 数字人，动作捕捉，面部捕捉，数字人形艺术等的相关内容
neural_rendering: 神经渲染器，NeRF，可微分渲染等的相关内容
computer_graphics: 图形学，渲染器，渲染，几何处理，图像处理等的相关内容
computer_vision: 计算机视觉，图像分类，目标检测，图像分割，语义分割，深度估计等的相关内容。注意: 脑机接口相关内容不属于计算机视觉的范畴
robotics: 机器人，机器狗，机械，类人机器等的相关内容
consumer_electronics: 消费电子，智能手机，智能手表等内容

一篇文章可以有多个相关标签，也可以和所有标签都不相关。

请调用 `{function_name}` 这个函数来完成我的要求。
"""
    messages = [{"role": "user", "content": user_message}]
    functions = [{
        "name": function_name,
        "description": "记录文章的总结和标签",
        "parameters": {
            "type": "object",
            "properties": {
                "summary": {
                    "type": "string",
                    "description": "中文的简短的不超过300字的文章总结"
                },
                "aigc": {
                    "type": "boolean",
                    "description": "文章是否含有生成式AI，大语言模型，文生图模型等的相关内容"
                },
                "digital_human": {
                    "type": "boolean",
                    "description": "文章是否含有数字人，动作捕捉，面部捕捉，数字人形艺术等的相关内容"
                },
                "neural_rendering": {
                    "type": "boolean",
                    "description": "文章是否含有神经渲染器，NeRF，可微分渲染等的相关内容"
                },
                "computer_graphics": {
                    "type": "boolean",
                    "description": "文章是否含有图形学，渲染器，渲染，几何处理，图像处理等的相关内容"
                },
                "computer_vision": {
                    "type": "boolean",
                    "description": "文章是否含有计算机视觉，图像分类，目标检测，图像分割，语义分割，深度估计等的相关内容。注意: 脑机接口相关内容不属于计算机视觉的范畴"
                },
                "robotics": {
                    "type": "boolean",
                    "description": "文章是否含有机器人，机器狗，机械，类人机器等的相关内容"
                },
                "consumer_electronics": {
                    "type": "boolean",
                    "description": "文章是否含有消费电子，智能手机，智能手表等内容"
                },
            },
            "required": ["summary",
                         "aigc", "digital_human", "neural_rendering", "computer_graphics", "computer_vision",
                         "robotics", "consumer_electronics"],
        },
    }]
    response = openai.ChatCompletion.create(
        engine=chatgpt_deployment_name,
        messages=messages,
        functions=functions,
        function_call={"name": function_name},  # force the model to call the function
    )
    function_call_info = response['choices'][0]['message']["function_call"]
    assert function_call_info["name"] == function_name
    function_args = json.loads(function_call_info["arguments"])
    feed_item.summary = function_args["summary"]
    feed_item.tags = Tags(function_args["aigc"],
                          function_args["digital_human"],
                          function_args["neural_rendering"],
                          function_args["computer_graphics"],
                          function_args["computer_vision"],
                          function_args["robotics"],
                          function_args["consumer_electronics"])
