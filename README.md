# bond-calendar-notify
新债每天九点定时微信推送

* 利用GitHub Action每天定时推送最新的新债
* Server酱提供从服务器到微信端的推送
1.GitHub Actions
是一项持续集成和部署服务，可用于自动化构建、测试和部署你的代码。 配置 GitHub Actions 主要包括以下步骤： 在你的代码仓库中创建 .github/workflows 目录。 在 .github/workflows 目录中创建一个 YAML 格式的配置文件，命名为 [workflow-name].yml，其中 [workflow-name] 是你自定义的工作流名称。

编辑工作流配置文件，使用 YAML 语法描述工作流程的结构和步骤。配置文件中可以包含触发条件、环境变量、任务步骤、依赖项等。 保存配置文件后，GitHub 将自动检测并运行你的工作流程。

完成配置后，将配置文件推送到代码仓库中的 .github/workflows 目录中，GitHub 将会自动运行你的工作流程。

【Github Actions生成 secrets参考链接】： https://blog.csdn.net/weixin_45178716/article/details/106416925
