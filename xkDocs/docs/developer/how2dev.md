# 怎样基于现有代码进行学习开发

## 项目结构

| 文件夹 | 功能 |
| ----- | ---- |
| backend | 后端代码 |
| crawler | 爬虫程序 |
| xkFrontendts | 前端代码 |
| xkDocs | 本文档 |
| .github/workflows | CI/CD 流水线 |

## 后端

后端结构简单，技术基于 `Flask`。主要是 `app.py` 作为 `Flask` 的入口文件。当然，单文件的架构在大型项目中不推荐。可以通过 `blueprint` 的方式来导入路由。

`utils` 存放了工具和数据库函数。`bckndSql.py` 涉及和数据库交互的 SQL 语句，`bckndTools.py` 涉及一些工具，如切分原始数据等。

记得补充 `config.ini`，按照 `config.ini.template` 的格式。

运行后端的方式是**切换到 `backend` 文件夹**，激活 `Python` 的虚拟环境，运行 `flask run --port=1239`。之所以是 1239，是因为在 `xkFrontendts/vite.config.ts` 中指定了，也可以换成不同的端口号。

## 爬虫

爬虫部分可以按照使用方法来叙述。首先，需要补充 `config.ini` 文件。其中 Account 是你的学号和密码；Sql 是数据库的相关信息；IMAP 是当发生加强认证时，接收验证码的邮箱；SMTP 是爬取结束后，发送给自己一个邮件提醒；Spider 指定了爬取的最新学期和爬取深度。

上面 SMTP 不是必须的，其余都要有。IMAP 需要根据实际绑定的邮箱来替换。因为我绑定的是 QQ 邮箱，所以按照 QQ 邮箱的相关代码来配置。如果使用其他邮箱的服务，需要根据实际修改配置文件。

第一次爬虫运行之前，需要先运行 `initNewDB.py` 来初始化数据库的结构，数据库的结构来源于 `course_template.sql`，初始化的数据库的名称取决于 `config.ini`。

运行爬虫 `fetchCourseList.py`！首先调用 `loginout.py` 中的代码进行用户登录，这个文件会调用 `myEncrypt.py` 来完成相关的加密处理。
如果需要加强认证，则调用 `imap_email.py` 中的相关函数通过邮箱接收验证码(用手机号自动接收验证码太难了)。
爬取过程中，使用 `tjSql.py` 中的函数完成数据库的写入操作。
最后，使用 `smtp_email.py` 的函数来发送爬取结束的邮件。

## 前端

前端基于 `Vue3` + `TypeScript`。这个项目重前端，需要完成许多和课程冲突相关的逻辑。写的我很痛苦，我其实不太擅长页面交互。

先切换到 `xkFrontendts` 文件夹，运行 `npm install` 安装依赖，再运行 `npm run dev` 进行开发和预览。`npm run build` 生成最终的部署文件。

前端中，`src/` 里存放了主要源代码。`components` 存放了好多页面组件，如页眉、页脚、高级检索、时间表等；
`store` 存放了一些公共的变量，以及和持久化相关的内容；
所谓的 `vuex`，从程序设计的角度来看，就是全局变量，通过 getters 来读取，通过 mutations 来进行值的变更；
所谓的持久化，就是把 `vuex` 保存的内容存到 `localStorage`，不然关闭浏览器后再次访问网站，内容就丢掉了；
`utils` 还是一些工具函数；
`assets` 里是一些图片文件。

剩下的让 AI 解释吧，有了 AI 后，前端好写多了。

## 文档

文档基于 `Vitepress`。需要切换到 `xkDocs` 文件夹，运行 `npm install` 安装依赖；`npm run dev` 进行页面预览；`npm run build` 生成可部署的文件。

## 流水线

流水线在 `.github/workflow` 下，当对应文件夹的代码发生变化时，可以自动进行同步。

我这里的同步比较简单。前端同步的方法是，先在 runner 中生成可部署的 dist，随后通过 SSH 移动到服务器对应的前端位置；
后端同步的方法是，通过 SSH 连接到服务器，拉取仓库中的最新内容并进行系统服务的重启。

## 其他

有关云服务器、`Linux`、`crontab`、`gunicorn`、`systemctl`、`nginx`、域名、`DNS`、`Cloudflare`、`GitHub` 相关的技术，不再赘述了。
