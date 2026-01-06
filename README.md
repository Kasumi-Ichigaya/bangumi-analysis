##概要
此项目是分析指定bangumi用户的动漫，游戏等分布，并做成横轴是标准差，纵轴是平局分的二维散点图
##配置方法
首先运行bgm2.py USER_ID填写要分析用户的ID（不是用户名），ACCESS_TOKEN可以到开发者平台自动生成，OUTPUT_CSV是输出csv的名字，然后下面的 type 可以修改要分析的类型。
bgm_see.py是一个在本地读取csv文件生成图片的脚本
make_html.py则是把csv文件变成html文件，可以在网上观看
