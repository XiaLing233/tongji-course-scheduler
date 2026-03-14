# TONGJI-COURSE-SCHEDULER

## 使用方法

访问[网站](https://xk.xialing.icu)。

## 单机调试方法

1. **配置环境**。推荐使用 `conda` 进行环境配置，创建一个虚拟环境，运行 `pip install -r requirements.txt`，使用 `backend` 或者 `crawler` 下的均可，二者内容相同；
2. **配置文件设定**。在 `backend` 和 `crawler` 文件夹下，分别新建 `config.ini` 文件，具体字段如 `config.ini.template` 所示，需要替换为你的相关信息。关键在于补充你的学号、密码，以及 MySQL 的用户与密码，邮件部分的配置可以忽略，不影响本地调试；
3. **数据库初始化**。先在 `crawler` 下执行 `initNewDB.py` 初始化一个数据库，并给用户赋予权限（若嫌麻烦，账户可以全写 root）；
4. **数据获取**。还是在 `crawler` 下执行 `fetchCourseList.py`，它会根据 `config.ini` 中设定的学期和深度爬取最近几个学期的信息，请耐心等待。理论上可以通过多线程等方式优化速度，但为了避免爬坏济网，采取当前的策略；
5. **启动后端**。在项目**根目录**下运行 `docker compose up -d --build` 运行后端容器；
6. **启动前端**。在 `xkFrontendts` 下运行 `npm install` 安装依赖，之后运行 `npm run dev` 启动前端，并在浏览器中访问页面。

## 部署项目

### 前端

1. 运行 `npm run build`，将前端在 `dist` 下的构建产物移动到服务器 `/var/www` 下；
2. 配置 nginx，在 `/etc/sites-available` 下增加一个 server 块配置文件，并软链接到 `sites-enabled`；
3. （可选）购买域名与通过 `certbot` 配置 HTTPS 证书。

### 后端

和本地调试的方法无差别。

### 数据库

1. 需要将数据库的绑定地址修改为 `0.0.0.0`，这样容器中的后端才能够连接到数据库（为了安全，可以在云服务商的防火墙中配置禁止外网访问 3306）；
2. 其余方式和本地调试相同，可能需要掌握通过 CLI 的方式与数据库交互，而不是 GUI 界面。

## 自动化相关

1. **CI/CD流水线**。使用 Github Actions，每当项目的代码更新后，ssh 到服务器，进行项目的更新（前端复制构建产物，后端重启容器）；
2. **定时爬取**。使用 crontab 定时任务，每周六早 7 点同步课程数据；
