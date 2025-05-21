import json
import os
import random
import sys
import threading
import time

from colorama import Fore, Style
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("API_KEY"), base_url="https://api.deepseek.com")

log = False


stop_event = threading.Event()


def logging(head: str, content: str, level: str = "info"):
    if level == "debug":
        print(f"\n{Fore.YELLOW}[#] {head}: {Style.RESET_ALL} {content}")
    elif level == "error":
        print(f"\n{Fore.RED}[x] {head}: {Style.RESET_ALL} {content}")
    elif level == "success":
        print(f"\n{Fore.GREEN}[+] {head}: {Style.RESET_ALL} {content}")
    elif level == "warning":
        print(f"\n{Fore.YELLOW}[!] {head}: {Style.RESET_ALL} {content}")
    else:
        print(f"\n{Fore.CYAN}[~] {head}: {Style.RESET_ALL} {content}")


def loading_animation(message: str):
    # spinner = ["⣾", "⣷", "⣯", "⣟", "⡿", "⢿", "⣻", "⣽"]
    spinner = ["🌑", "🌒", "🌓", "🌔", "🌕", "🌖", "🌗", "🌘"]
    i = 0
    running_time = 0
    while not stop_event.is_set():
        sys.stdout.write(f"\r{message} {spinner[i % len(spinner)]} {running_time:.2f}s")
        sys.stdout.flush()
        time.sleep(0.1)
        i += 1
        running_time += 0.1
    sys.stdout.flush()


def translate_segments(prompt: str, segments: list) -> str:
    messages = []
    messages.append({"role": "system", "content": prompt})
    messages.append(
        {
            "role": "user",
            "content": "\n\n".join(segments),
        }
    )
    if log:
        logging("Request", f"{messages}", level="debug")
    result = request_llm(messages)
    return str(result)


def request_llm(messages: list) -> str:
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            max_tokens=8192,
            temperature=0.6,
            stream=False,
            timeout=600,
        )
        if log:
            logging("Response", f"{response}", level="debug")
        result = response.choices[0].message.content
        return str(result)
    except Exception as e:
        stop_event.set()
        logging("Error", f"{e}", level="error")
        exit(0)


def translate(
    title_cn: str, content: str, paragraph_batch_size: int, use_cache: bool
) -> str:
    system_prompt_template = """{}
    你是一个中英文翻译专家，并且精通克苏鲁文学。现在需要将用户输入的克苏鲁英语原著翻译为中文。要求:
    1. 翻译之前，定位并排除那些明显没有表达任何意义且与上下文无关的段落，这些段落可能是在文本解析过程中产生的冗余文本，通常非常短。
    2. 翻译过程中，要求：
        - 使用维多利亚哥特式、诡异恐怖的风格**逐句翻译**成对应的中文语句
        - 忠实原文内容和意图，不要添加原文中不存在的内容
        - 让语句尽可能通俗流畅易懂
        - 不要在译文中添加任何子标题
    3. 翻译完成后，检查是否存在中英文混杂的情况，例如“让我在握紧的 flesh 上如受刀刃钳制般尖叫”，如果有，重新翻译该句子并纠正。
    4. 翻译结束后，输出翻译后的文本，不要包含诸如译注、翻译手法说明在内的任何说明性内容
    
"""
    paragraphs = content.split("\n\n")
    # show animation
    stop_event.clear()
    animation_thread = threading.Thread(
        target=loading_animation,
        args=(f"{Fore.CYAN}[~] Translating: {title_cn} {Style.RESET_ALL}",),
    )
    animation_thread.daemon = True
    animation_thread.start()

    if use_cache:
        system_prompt = system_prompt_template.format("")
    else:
        # all segments of the same article shares the same system prompt seed to hit cache
        system_prompt = system_prompt_template.format(random.randint(0, 10000000))
    segments = []
    # should be joined by \n\n
    translated_segments = []
    for n, p in enumerate(paragraphs):
        segments.append(p)
        if n % paragraph_batch_size == 0 and n != 0:
            try:
                result = translate_segments(system_prompt, segments)
                translated_segments.append(result)

            except Exception as e:
                stop_event.set()
                animation_thread.join()
                logging("Error", f"{e}", level="error")
                exit(0)

            segments = []

    if len(segments) > 0:
        try:
            result = translate_segments(system_prompt, segments)
            translated_segments.append(result)
        except Exception as e:
            stop_event.set()
            animation_thread.join()
            logging("Error", f"{e}", level="error")
            exit(0)

    stop_event.set()
    animation_thread.join()
    translated_content = "\n\n".join(translated_segments)
    logging("Output", translated_content, level="success")

    return translated_content


def save_articles(index: int, title_cn: str, content_cn: str, output_dir: str):
    filename = str(index) + "-" + title_cn.replace(" ", "_") + ".md"
    path = os.path.join(output_dir, filename)
    # create output directory if not exists
    os.makedirs(output_dir, exist_ok=True)
    with open(path, "w+", encoding="utf-8") as out_f:
        out_f.write(f"# {title_cn}\n\n")
        out_f.write(content_cn)
        logging(
            "Output",
            f"Saved {title_cn} articles to {path}",
            level="success",
        )


def update_library(library_path: str, title_cn: str, content_cn: str):
    result = []
    with open(library_path, "r", encoding="utf-8") as f:
        library = json.load(f)
        for article in library:
            if article["title_cn"] == title_cn:
                article["content_cn"] = content_cn
            result.append(article)

    with open(library_path, "w+", encoding="utf-8") as out_f:
        json.dump(result, out_f, ensure_ascii=False, indent=4)
    logging("Output", f"Updated library {library_path}", level="success")


def main():
    target_titles = [
        # "希帕波利亚的缪斯女神",
        # "撒坦普拉·赛罗斯奇谭",
        # "通往土星之门",
        # "阿沙茅斯的证言",
        # "阿弗所·乌索库安的厄运",
        # "乌波 - 萨斯拉",
        # "白巫女",
        # "冰魔",
        # "白色蠕虫的到来",
        # "七咒缚",
        # "故事的结局",
        # "萨堤尔",
        # "阿韦鲁瓦涅的幽会",
        # "阿泽达莱克的圣洁",
        "伊洛涅的巨人",
        # "曼德拉草",
        # "阿韦鲁瓦涅之兽",
        # "出土维纳斯",
        # "蟾蜍之母",
        # "西莱尔的女巫",
        # "死灵术士的王朝",
        # "施虐者之岛",
        # "藏骸所之神",
        "暗黑神像",
        # "尤沃伦王的旅途",
        # "墓中织客",
        # "坟茔之嗣",
        # "西斯拉",
        # "最后的象形符文",
        # "纳特的死灵术",
        # "普图姆的黑人修道院院长",
        # "伊拉洛莎之死",
        # "阿冬法的花园",
        # "蟹之主",
        # "莫希拉",
        # "亚特兰蒂斯的缪斯女神",
        # "最后的术法",
        # "前往斯法诺莫埃的旅途",
        # "来自亚特兰蒂斯的醇酒",
        # "暗影成双",
        # "马利格里斯之死",
        "妖术师的迷宫",
        # "花之女",
        "约-冯比斯的坟窟",
        "深谷住民",
        # "乌素姆",
        # "巫师归来",
        # "无名的子嗣",
        # "亚弗戈蒙之链",
        # "踏尘者",
    ]

    translation_batch_size = 20
    use_cache = True
    library = json.load(open("C.A.Smith_articles.json", "r", encoding="utf-8"))

    filetered_library = []
    for article in library:
        if article["title_cn"] in target_titles:
            filetered_library.append(article)

    for article in filetered_library:
        title_cn = article["title_cn"]
        content = article["content"]
        index = article["index"]

        content_cn = translate(title_cn, content, translation_batch_size, use_cache)
        save_articles(
            index,
            title_cn,
            content_cn,
            "./data/translated/C.A.Smith",
        )
        update_library("./C.A.Smith_articles_all.json", title_cn, content_cn)


if __name__ == "__main__":
    main()
