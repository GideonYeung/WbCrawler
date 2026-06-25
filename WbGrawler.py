import os
import time
import json
import random
import logging
import requests
import threadpool

# 加载配置
_config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
with open(_config_path, "r", encoding="utf-8") as f:
    cfg = json.load(f)

USER_ID = cfg["user_id"]
COOKIE = cfg.get("cookie", "")
SAVE_PATH = cfg["save_path"]
PAGE_START = cfg.get("page_start", 1)
PAGE_END = cfg.get("page_end", 10)
THREAD_COUNT = cfg.get("thread_count", 2)
PAGE_SLEEP = (cfg.get("page_sleep_min", 3), cfg.get("page_sleep_max", 8))
IMG_SLEEP = (cfg.get("img_sleep_min", 1), cfg.get("img_sleep_max", 3))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger(__name__)


class WbCrawler:
    def __init__(self, start=1, end=10, cookie=""):
        self.user_id = USER_ID
        self.base_url = f"https://m.weibo.cn/api/container/getIndex?containerid=107603{USER_ID}&"
        self.save_path = SAVE_PATH
        self.start_page = start
        self.end_page = end
        os.makedirs(self.save_path, exist_ok=True)

        self.session = requests.Session()
        self.session.headers.update({
            "Host": "m.weibo.cn",
            "Referer": f"https://m.weibo.cn/u/{USER_ID}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        })

        if cookie and cookie.strip():
            self.session.headers["Cookie"] = cookie.strip()
            logger.info("已从 config.json 加载Cookie")
        else:
            logger.warning("未配置Cookie！请在 config.json 中填入cookie字段")

    def fetch_page(self, page):
        """获取第page页的微博数据"""
        url = self.base_url + f"page={page}"
        try:
            resp = self.session.get(url)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("ok") == 1:
                    return data
                logger.warning(f"第{page}页无微博数据")
            elif resp.status_code == 432:
                logger.warning(f"第{page}页被反爬拦截(432)")
            else:
                logger.warning(f"第{page}页请求失败，状态码: {resp.status_code}")
        except Exception as e:
            logger.error(f"第{page}页请求异常: {e}")
        return None

    def parse_images(self, data):
        """从微博数据中提取图片列表"""
        cards = data.get("data", {}).get("cards", [])
        for card in cards:
            mblog = card.get("mblog", {})
            pics = mblog.get("pics")
            if not pics:
                continue
            for pic in pics:
                yield {
                    "pid": pic.get("pid"),
                    "url": pic.get("large", {}).get("url"),
                }

    def download_images(self, images):
        """下载图片，跳过已存在的文件"""
        for img in images:
            filename = f"{img['pid']}.jpg"
            filepath = os.path.join(self.save_path, filename)

            # 跳过已下载的图片
            if os.path.exists(filepath) and os.path.getsize(filepath) > 1024:
                logger.info(f"{filename} 已存在，跳过")
                continue

            try:
                resp = requests.get(img["url"], headers={
                    "Referer": "https://m.weibo.cn/",
                    "User-Agent": self.session.headers["User-Agent"],
                }, timeout=10)

                if resp.status_code == 200 and len(resp.content) > 1024:
                    with open(filepath, "wb") as f:
                        f.write(resp.content)
                    logger.info(f"{filename} 下载成功 ({len(resp.content) // 1024}KB)")
                else:
                    logger.warning(f"{filename} 下载失败，状态码:{resp.status_code}, 大小:{len(resp.content)}")

                time.sleep(random.uniform(*IMG_SLEEP))
            except Exception as e:
                logger.error(f"{filename} 下载异常: {e}")

    def crawl_page(self, page):
        """爬取单页：获取 -> 解析 -> 下载"""
        data = self.fetch_page(page)
        if data:
            images = list(self.parse_images(data))
            if images:
                logger.info(f"第{page}页发现 {len(images)} 张图片")
            self.download_images(images)
        time.sleep(random.uniform(*PAGE_SLEEP))


if __name__ == "__main__":
    crawler = WbCrawler(PAGE_START, PAGE_END, cookie=COOKIE)
    pool = threadpool.ThreadPool(THREAD_COUNT)
    tasks = threadpool.makeRequests(crawler.crawl_page, range(PAGE_START, PAGE_END + 1))
    for task in tasks:
        pool.putRequest(task)
    pool.wait()
    logger.info(f"全部完成！图片保存在: {SAVE_PATH}")
