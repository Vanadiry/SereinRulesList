# SereinRulesList

这是 [Serein](https://github.com/Vanadiry/Serein/) 项目的官方规则源。  
要订阅这个规则源，请在 Serein 配置中的 `[[rule_sources]]` 部分，加入下面内容：

```text
url = "https://raw.githubusercontent.com/Vanadiry/SereinRulesList/refs/heads/main/_source.json"
```

## 创建和分发规则

若要创建自己的规则，请前往 [此处](https://github.com/Vanadiry/Serein/blob/main/docs/rules/_rules.md) 查看自定义规则和规则源的方式。

若要分发，你可以直接分享规则 toml 文件，使用者只需要将其放在 `Serein主目录/rules/_local` 内，并在 Tracker 添加对应 AppID 即可。

### 将规则提交到本仓库

在仓库根目录创建以你的名字命名的文件夹（仅允许大小写字母、数字、下划线和连字符），并在里面创建 `_source.json`。  
然后，在根目录的 `_source.json` 中，加入你刚才创建的 json 路径即可。  
之后，你就可以创建并提交你的规则了。每次更新，都记得将你文件夹中的 `_source.json` 版本号递增一位。

若软件同时存在多个系统的版本，请尽量全部列出。

另外，下列类型的软件规则不被接受：

1. 盗版或恶意的
2. 来自非官方源的
3. 完全依赖中心化网络的（例如大多数社交媒体/即时聊天软件等）
4. 必须登录才能获取版本信息的
5. 滥用更新检查的

## 停止和暂停维护的规则

一些由于软件删库等原因，不再可用的规则，将会移动到本仓库的 archive 目录下。

一些由于有更好的替代软件，或是其他原因，而暂停维护的规则，加入了 `status = ["暂停维护此规则"]`。  
这会在 Serein 的软件名旁边，展示一个黄色圆点，来指示软件本身或规则处于暂停维护状态。
