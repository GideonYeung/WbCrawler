# WbCrawler - 微博图片爬虫

批量下载指定微博用户的图片，支持多线程、断点续传（跳过已下载图片）、随机延时防反爬。

## 环境要求

- Python 3.6+

## 安装依赖

```bash
pip install requests threadpool
```

## 配置

编辑 `config.json`：

```jsonc
{
    "user_id": "6032474791",       // 目标用户的微博ID（换博主改这里）
    "cookie": "...",               // 微博Cookie（登录后从浏览器获取）
    "save_path": "D:/weibosrc/",   // 图片保存路径
    "page_start": 1,               // 起始页码
    "page_end": 10,                // 结束页码
    "thread_count": 2,             // 线程数（建议不超过3）
    "page_sleep_min": 3,           // 翻页最小间隔（秒）
    "page_sleep_max": 8,           // 翻页最大间隔（秒）
    "img_sleep_min": 1,            // 图片下载最小间隔（秒）
    "img_sleep_max": 3             // 图片下载最大间隔（秒）
}
```

### 如何获取 Cookie

1. 浏览器打开 [m.weibo.cn](https://m.weibo.cn) 并登录
2. 按 `F12` 打开开发者工具 → **Network** 标签
3. 刷新页面，点击任意请求，在 **Request Headers** 中找到 `Cookie` 字段
4. 复制完整内容粘贴到 `config.json` 的 `cookie` 字段

### 如何获取 user_id

打开目标用户的微博主页，URL 中的数字即为 `user_id`：
```
https://m.weibo.cn/u/6032474791
                     ^^^^^^^^^^
                     这就是 user_id
```

## 运行

```bash
python WbGrawler.py
```

## 功能说明

| 功能 | 说明 |
|------|------|
| 多线程下载 | 通过 `thread_count` 控制并发数 |
| 跳过已下载 | 已存在且大于 1KB 的图片自动跳过 |
| 随机延时 | 翻页和图片下载间随机等待，降低被封风险 |
| 大图优先 | 自动请求 `large` 尺寸图片 |
| 反爬提示 | 遇到 432 状态码时输出警告 |
