# edu-lark-bot

仓库地址：https://github.com/roostinghawk/edu-lark-bot
爱丁飞书机器人推送每日诗句及图片的实现原理：
1. github action 触发每日定时任务；
2. 请求“今日诗词” api 随机选择一句中国古诗词；
3. 将诗词作为参数，使用 Bing 生成图片并保存；
4. 调用飞书 api 上传图片，返回 image_key（需要注册飞书应用并开启权限）；
5. 组装飞书消息格式富文本（text + img）；
6. 推送到对应群的机器人 webhook；
7. 飞书群收到消息

TODO：
+ 使用飞书应用推送消息而不是用 webhook；
+ 使用 openai 的 api先将诗句翻译为英文再生成图片，效果可能更好；
+ 生成的四张图片可否以缩略图方式都推送到飞书



