# SereinRulesList

这是 [Serein](https://github.com/Vanadiry/Serein/) 项目的官方规则源。  
要订阅这个规则源，请在 Serein 配置中的 `[[rule_sources]]` 部分，加入下面内容：

```text
url = "https://raw.githubusercontent.com/Vanadiry/SereinRulesList/refs/heads/main/_source.json"
```

## 收录架构和版本规则

软件包：

- macOS：`ARM (Apple Silicon)`，dmg/pkg 优先
- Windows：`x86-64`，exe/msi 安装包优先
- Linux：`x86-64`，AppImage 优先
- iOS：仅 IPA
- Android：`arm64-v8a`，app 优先

字体：可变的、ttf 的、中文的优先。

## 停止和暂停维护的规则

对于那些有更好替代品的、上游不再维护的、不能获取版本和下载地址的，本仓库也将不再维护他们的规则。  
这些不再维护的规则文件会在 `_deleted` 目录保留一段时间，在你检查更新时，会弹出提示来提醒你尽快迁移。  
之后，在合适的时间，将会删除它们。

## 贡献

感谢你愿意为 SereinRulesList 贡献数据，请阅读[贡献指南](CONTRIBUTING.md)。
