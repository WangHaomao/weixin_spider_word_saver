from bs4 import BeautifulSoup
import requests
from time import sleep
from PIL import Image
from io import BytesIO
from tqdm import tqdm
from word_saver import WordSaver

headers = {
        "user-agent": "",
        "accept": "",
        "accept-language": ""
    }

img_headers = {
        "user-agent": "",
        "accept": "",
        "accept-language": ""
    }

def read_bytes_html(path) -> list:
    with open(path, "rb") as f:
        content = f.readlines()
    content = map(lambda x: x.decode("utf-8"), content)
    # pprint(list(content))
    return list(content)


def down_load_html(url, save_path):

    ret = requests.get(url, headers)
    if ret.status_code == 200:
        with open(save_path, "wb") as f:
            f.write(ret.content)
    return ret.status_code


def parse_html(path, cached=None):
    """
    :param path:
    :param cached: 之前保存过的，没有可以存为空
    :return:
    """
    with open(path, "rb") as f:
        content = f.readlines()
    content = map(lambda x: x.decode("utf-8"), content)
    html_content = "".join(content)

    soup = BeautifulSoup(html_content, "lxml")
    alinks = soup.findAll("a")

    idx = 0
    for target_a in alinks:
        article_name = str(target_a.text)
        if cached is not None and article_name in cached:
            continue
        if "【题练】" not in article_name and "【谷一说】" not in article_name:
            continue
        article_link = target_a["href"]
        code = down_load_html(article_link, fr"zhongji\{idx}.txt")
        print(code, article_name, article_link)
        idx = idx + 1
        sleep(0.1)


def get_img(img_url):
    """
    根据url保存图片为PIL.Image
    :param img_url: url
    :return:
    """
    response = requests.get(img_url, img_headers)
    image_data = response.content

    # 打开图片
    image = Image.open(BytesIO(image_data))
    return image


def parse_target_article(path, tot_content):
    content = "\n".join(read_bytes_html(path))
    soup = BeautifulSoup(content)
    allp = soup.findAll("p")
    start_read_flag = False

    pre_content = ""

    for ptoken in allp:
        if "全文共计" in str(ptoken.text):
            start_read_flag = True
        if "我把微店里和我当当购物车里" in str(ptoken.text) \
                or "【经验】挂科怎么看书#内附考试大纲#放射医学技术#" in str(ptoken.text):
            # end
            break
        if "【谷一说】" in str(ptoken.text) or "导读：" == str(ptoken.text):
            continue

        if pre_content == "基础知识：" and str(ptoken.text) == "第一章：":
            tot_content.pop()
            break

        if "第一章：" == str(ptoken.text) or "第二章：" == str(ptoken.text) \
                or "第三章：" == str(ptoken.text) or "第四章：" == str(ptoken.text):
            continue

        if not start_read_flag:
            continue

        pre_content = str(ptoken.text)
        tot_content.append(str(ptoken.text))

        imgs = ptoken.findChildren("img", recursive=True)
        if imgs is None or len(imgs) == 0:
            continue
        for img in imgs:
            tot_content.append(get_img(img["data-src"]))


def replace_answers(content):
    answers = ["A", "B", "C", "D", "E"]
    curr_answer = None
    for a in answers:
        if f"（{a}）" in content:
            curr_answer = f"（{a}）"
            break

    if curr_answer is not None:
        content = content.replace(curr_answer, "（  ）")

    return content, curr_answer


def parse_target_questions(path, tot_content):
    with open(path, "rb") as f:
        content = f.readlines()
    content = map(lambda x: x.decode("utf-8"), content)
    content = "\n".join(content)
    soup = BeautifulSoup(content)

    h1 = soup.find("h1", {"id": "activity-name"})
    tot_content.append(str(h1.text).strip().replace("\n", "") + "\n")
    allp = soup.findAll("p")
    start_read_flag = False
    pre_content = ""
    answer_list = []

    for ptoken in allp:
        # if len(ptoken.contents) > 0:
        #     cur_list = []
        if "看完章节内容，来这里练习一下对应习题吧。" in str(ptoken.text):
            start_read_flag = True
            continue
        if "本节内容按照技士考试大纲，不在技士考察范围内，参加技士考试的同行可以不用看。" in str(ptoken.text):
            start_read_flag = True
        if "为了大家能够先做题再对答案，答案依然是隐藏的。" in str(ptoken.text):
            # end
            break
        if str(ptoken.text).startswith("1、"):
            start_read_flag = True

        if not start_read_flag:
            continue

        if pre_content == "基础知识：" and str(ptoken.text) == "第一章：":
            tot_content.pop()
            break

        pre_content = str(ptoken.text)

        final_content, answer = replace_answers(str(ptoken.text))

        if answer is not None:
            answer_list.append(final_content.split("、")[0] + "." + answer.replace("（", "").replace("）", ""))

        tot_content.append(final_content)

        imgs = ptoken.findChildren("img", recursive=True)
        if imgs is None or len(imgs) == 0:
            continue
        for img in imgs:
            tot_content.append(get_img(img["data-src"]))
            # print(img["data-src"])
            pass
        # break
    tot_content.append(" ".join(answer_list))
    # print("\n".join(tot_content))


if __name__ == '__main__':
    # 1. download start page
    # down_load_html(
    #     # "https://mp.weixin.qq.com/s?__biz=MzAwODE0MDMzNg==&mid=2247504621&idx=2&sn=15653be86d0a23963b4f425cd1b494a1&chksm=9b71f1b2ac0678a4b1b6ad9c1f5c1acacf584c1e83f7b22e72c61d105b6934fe7ed9de8135c1&scene=21#wechat_redirect",
    #     "https://mp.weixin.qq.com/s/dkvsyvEl7GuD3B7yTpitwQ",
    #
    #     "./jishi/start.txt")

    # 2. download all links from start.txt
    parse_html("./jishi/start.txt")

    # 3. download all content from links(step 2)
    tot_content = []
    # for i in range(0, 112):
    for i in tqdm(range(0, 112)):
        parse_target_article(fr"D:\Workspace\python\localpython\zhongji\{i}.txt", tot_content)

    saver = WordSaver()
    saver.save(tot_content)
