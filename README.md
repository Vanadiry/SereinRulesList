# SereinRulesList

这是 [Serein](https://github.com/Vanadiry/Serein/) 项目的官方规则源。  
要订阅这个规则源，请在 Serein 配置中的 `[[rule_sources]]` 部分，加入下面内容：

```text
url = "https://raw.githubusercontent.com/Vanadiry/SereinRulesList/refs/heads/main/_source.json"
```

## 创建或提交规则

若要创建或提交自己的规则，请前往 [此处](https://github.com/Vanadiry/Serein/blob/main/docs/rules/_rules.md) 查看自定义规则和规则源的方式。

如果想为本仓库提交规则，请在仓库根目录创建以你的名字命名的文件夹（仅允许大小写字母、数字、下划线和连字符），并在里面创建 `_source.json`。  
然后，在根目录的 `_source.json` 中，加入你刚才创建的 json 路径即可。  
之后，你就可以创建并提交你的规则了。每次更新，都记得将你文件夹中的 `_source.json` 版本号递增一位。

另外，下列类型的软件规则不被接受：

1. 盗版或恶意的
2. 来自非官方源的
3. 完全依赖中心化网络的（例如大多数社交媒体/即时聊天软件等）
4. 必须登录才能获取版本信息的
5. 滥用更新检查的

## 须知

此处记录的软件均为官方正版源。  
部分软件需要注册和登录账户，并有对应的授权才可使用，这和本项目无关。
