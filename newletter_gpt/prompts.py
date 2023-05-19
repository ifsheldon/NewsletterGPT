import openai
import json
from newletter_gpt.feeds import FeedItem, Tags


def gen_summary_via_llm(feed_item: FeedItem):
    """
    Generate summary for a feed item via LLM (now gpt-3.5-turbo)
    :param feed_item: the feed item to be summarized, modified in place
    :return: None
    """
    if feed_item.with_html_noise:
        prompt_template = "帮我总结一下这篇文章，这篇文章的题目是{title}：```\n" \
                          "{text}" \
                          "\n```\n" \
                          "文章是从微信公众号获取的，有一些噪音，你可以忽略它们，例如：“参考资料：....”, “预览时标签不可点”, “微信扫一扫关注该公众号”, “编辑：....”和 “轻点两下取消在看”。" \
                          "请先清理噪音，然后再根据清理完的文本来总结。文章总结不要超过300字。结果请严格按照JSON格式返回，格式如下：\n" \
                          "{{ \"cleaned_text\": \"清理完的文本\", \"summary\": \"文章的总结\" }}"
    else:
        prompt_template = "帮我总结一下这篇文章，这篇文章的题目是{title}：```\n" \
                          "{text}" \
                          "\n```\n" \
                          "文章总结不要超过300字。结果请严格按照JSON格式返回，格式如下：\n" \
                          "{{ \"summary\": \"文章的总结\" }}"

    prompt = prompt_template.format(title=feed_item.title, text=feed_item.content)
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        temperature=0.1,
        messages=[{"role": "user", "content": prompt}],
    )
    # process response
    processed_response = response.choices[0]["message"]["content"].replace("`", "")
    response_json = json.loads(processed_response)
    # set summary
    feed_item.summary = response_json["summary"]


def get_tags_via_llm(feed_item: FeedItem):
    """
    Get tags for a feed item via LLM (now gpt-3.5-turbo)
    :param feed_item: the feed item to be tagged, modified in place
    :return: None
    """
    prompt_template = "帮我给这篇文章打标签。\n" \
                      "文章标签：```{title}```\n" \
                      "文章内容：```{content}```\n" \
                      "文章总结：```{summary}```\n" \
                      "可用的标签有：\n" \
                      "* aigc: 生成式人工智能相关，例如大语言模型，文生图模型等的相关内容\n" \
                      "* digital_human: 数字人相关，例如数字人，动作捕捉，面部捕捉，数字人形艺术等的相关内容\n" \
                      "* neural_rendering: 神经渲染相关，例如神经渲染器，NeRF，可微分渲染等的相关内容\n" \
                      "* computer_graphics: 计算机图形学相关，例如渲染器，渲染，几何处理，图像处理等的相关内容\n" \
                      "* computer_vision: 计算机视觉相关，例如图像分类，目标检测，图像分割，语义分割，深度估计等的相关内容。注意: 脑机接口相关内容不属于计算机视觉的范畴。\n" \
                      "* robotics: 和机器人相关，例如机器狗，机械，类人机器等的相关内容。\n" \
                      "一篇文章可以有多个相关标签，也可以和所有标签都不相关，如果文章和一个标签相关，那么就返回true，否则返回false。" \
                      "请将文章的所有标签严格按照JSON格式返回，不要添加额外的符号。一个合规的例子是: " \
                      "{{\"aigc\": true, " \
                      "\"digital_human\": false, " \
                      "\"neural_rendering\": true, " \
                      "\"computer_graphics\": false, " \
                      "\"computer_vision\": false, " \
                      "\"robotics\": false, }}\n"

    prompt = prompt_template.format(title=feed_item.title, content=feed_item.content, summary=feed_item.summary)
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        temperature=0.1,
        messages=[{"role": "user", "content": prompt}],
    )
    # process response
    processed_response = response.choices[0]["message"]["content"].replace("`", "")
    response_json = json.loads(processed_response)
    # set tags
    feed_item.tags = Tags(aigc=response_json["aigc"],
                          digital_human=response_json["digital_human"],
                          neural_rendering=response_json["neural_rendering"],
                          computer_graphics=response_json["computer_graphics"],
                          computer_vision=response_json["computer_vision"],
                          robotics=response_json["robotics"])
