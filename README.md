# 概要
- 此项目是分析指定bangumi用户的动漫，游戏等分布，并做成横轴是标准差，纵轴是平均分的二维散点图。
# 配置方法
- 首先运行bangumi_auto.py USER_ID填写要分析用户的ID（不是用户名），ACCESS_TOKEN可以到[开发者平台](https://next.bgm.tv/demo/access-token)自动生成，OUTPUT_CSV是生成scv文件的名字，下面文件名称建议不要动。
- 如果想要生成图片请运行bgm_see.py，会读取csv文件生成图片。
# 依赖
- 需要python 3.9以上版本，更低版本没进行测试，需要以下第三方库，请通过pip指令下载：第三方库写在了requirements文件内。
