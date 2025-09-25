# TONGJI-COURSE-SCHEDULER

## Archived

不再打算开发。未来可以提升的空间是，在数据库表的属性中添加爬取编号，从而便于同步 1 系统数据库的内容。

## Usage

Download the project, at root folder, run

```bash
python -m venv .venv # create a virtual environment, recommended
.\venv\Scripts\activate # ACTIVATE the virtual environment
pip install -r requirements.txt # install dependencies
```

to install all dependencies.

To make login function possible, you need to add a `config.ini` file at `./crawler`, which includes your student ID and password in clear text:

```ini
# no need to add "" around values, e.g sno = "2365472" is WRONG
[Account]
sno = 2365472
passwd = 123456
```

**Or** if you are tired of securing your privacy, you can just simply replace configparser result with your student ID and password at `myEncypt.py`:

```py
# 账号密码认证部分 (Original)
STU_NO = CONFIG['Account']['sno']
STU_PWD = CONFIG['Account']['passwd']

# --------------------------------- #

# 账号密码认证部分 (Modified)
STU_NO = "2365472"
STU_PWD = "123456"
```
