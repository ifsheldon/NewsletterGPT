from newletter_gpt.feeds import FeedItem, Tags
import guidance
import logging

logger = logging.getLogger("NewsletterGPT")

def gen_summary_and_tags_via_llm(feed_item: FeedItem, api_base: str, api_key: str):
    # Notice: NEED TO MODIFY guidance/llms/_openai.py:315 IF YOU ARE USING AZURE OPENAI SERVICE
    # truncate content, max 3000 Chinese and English character
    item_content = feed_item.content[:3000]
    logger.info(f"Generating summary for {feed_item.title}")
    guidance.llm = guidance.llms.OpenAI(model="gpt-3.5-turbo",
                                        api_base=api_base,
                                        api_type="azure",
                                        api_version="2023-03-15-preview",
                                        api_key=api_key)
    create_plan = guidance('''
{{#user~}}
文章题目：{{title}}
文章全文：```
{{content}}
```
{{extra_note}}

英文专业名词要保留，然后请用中文生成简短的不超过300字的文章总结。

文章总结：
{{~/user}}

{{#assistant~}}
{{gen 'summary' temperature=0.1 max_tokens=500}}
{{~/assistant}}
''')

    if feed_item.with_html_noise:
        extra = "\n文章是从微信公众号获取的，有一些可以忽略的噪音，例如：“参考资料：....”, “预览时标签不可点”, “微信扫一扫关注该公众号”, “编辑：....”和 “轻点两下取消在看”。"
    else:
        extra = ""

    output = create_plan(title=feed_item.title,
                         content=item_content,
                         extra_note=extra)
    summary = output["summary"]
    feed_item.summary = summary

    logger.info(f"Generating tags for {feed_item.title}")
    guidance.llm = guidance.llms.OpenAI(model="text-davinci-003",
                                        api_base=api_base,
                                        api_type="azure",
                                        api_version="2022-12-01",
                                        api_key=api_key)

    # truncate content, max 1200 Chinese and English character
    item_content = feed_item.content[:1200]
    create_plan = guidance("""
文章题目：{{title}}
文章全文：```
{{content}}
```
{{extra_note}}

根据以上信息，给文章打标签。可用的标签有：
aigc: 生成式AI，大语言模型，文生图模型等的相关内容
digital_human: 数字人，动作捕捉，面部捕捉，数字人形艺术等的相关内容
neural_rendering: 神经渲染器，NeRF，可微分渲染等的相关内容
computer_graphics: 图形学，渲染器，渲染，几何处理，图像处理等的相关内容
computer_vision: 计算机视觉，图像分类，目标检测，图像分割，语义分割，深度估计等的相关内容。注意: 脑机接口相关内容不属于计算机视觉的范畴
robotics: 机器人，机器狗，机械，类人机器等的相关内容
consumer_electronics: 消费电子，智能手机，智能手表等内容

一篇文章可以有多个相关标签，也可以和所有标签都不相关。如果文章和一个标签相关，返回1，否则返回0。文章的所有标签严格按照JSON格式返回。

该文章分类的标签如下：{
"aigc":{{#select 'aigc'}}1{{or}}0{{/select}},
"digital_human":{{#select 'digital_human'}}1{{or}}0{{/select}},
"neural_rendering":{{#select 'neural_rendering'}}1{{or}}0{{/select}},
"computer_graphics":{{#select 'computer_graphics'}}1{{or}}0{{/select}},
"computer_vision":{{#select 'computer_vision'}}1{{or}}0{{/select}},
"robotics":{{#select 'robotics'}}1{{or}}0{{/select}},
"consumer_electronics":{{#select 'consumer_electronics'}}1{{or}}0{{/select}},
}""")

    output = create_plan(title=feed_item.title,
                         content=item_content,
                         extra_note=extra)
    aigc = int(output["aigc"]) == 1
    digital_human = int(output["digital_human"]) == 1
    neural_rendering = int(output["neural_rendering"]) == 1
    computer_graphics = int(output["computer_graphics"]) == 1
    computer_vision = int(output["computer_vision"]) == 1
    robotics = int(output["robotics"]) == 1
    consumer_electronics = int(output["consumer_electronics"]) == 1
    tags = Tags(aigc, digital_human, neural_rendering, computer_graphics, computer_vision, robotics,
                consumer_electronics)
    feed_item.tags = tags
