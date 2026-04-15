import configparser
import json
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from enum import Enum, auto
from urllib.parse import urlencode, parse_qs, urlparse

import requests

from . import imap_email
from . import myEncrypt


CONFIG = configparser.ConfigParser()
CONFIG.read("config.ini")

IMAP_SERVER = CONFIG["IMAP"]["server_domain"]
IMAP_PORT = CONFIG["IMAP"]["server_port"]
IMAP_USERNAME = CONFIG["IMAP"]["qq_emailaddr"]
IMAP_PASSWORD = CONFIG["IMAP"]["qq_grantcode"]


class LoginState(Enum):
    FETCH_ENTRY = auto()            # 访问 1 系统, 获得基础认证信息
    SUBMIT_PASSWORD = auto()        # 登录
    REQUEST_ENHANCE_CODE = auto()   # 点击 "发送验证码" 按钮
    SUBMIT_ENHANCE_CODE = auto()    # 输入验证码
    AUTHN_ENGINE = auto()           # 验证码正确后, 给它发内容
    SESSION_LOGIN = auto()          # 在 1 系统内登录
    SUCCESS = auto()
    FAILED = auto()


@dataclass
class LoginContext:
    session: requests.Session
    state: LoginState = LoginState.FETCH_ENTRY
    entry_url: str = "https://1.tongji.edu.cn/api/ssoservice/system/loginIn"
    chain_url: str = ""
    authn_lc_key: str = ""
    sp_auth_chain_code: str = ""
    rsa_url: str = ""
    is_enhance: bool = False
    failed_reason: str = ""                     # 登录失败原因
    auth_payload: str = ""                      # 提交给 ActionAuthChain 的表单
    form_headers: dict | None = None
    entry_headers: dict | None = None
    sso_headers: dict | None = None
    response: requests.Response | None = None
    sso_url: str = ""
    login_in_url: str = ""
    ssologin_url: str = ""
    aes_url: str = ""
    retry_count: int = 0
    max_retry: int = 6
    wait_seconds: int = 15


class SSOLoginStateMachine:
    def __init__(self):
        self.ctx = LoginContext(session=requests.Session())
        self.ctx.form_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Origin": "https://iam.tongji.edu.cn",
            "Host": "iam.tongji.edu.cn",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        }
        self.ctx.entry_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Referer": "https://1.tongji.edu.cn/ssologin",
        }
        self.ctx.sso_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        }

    def run(self) -> requests.Session | None:
        while self.ctx.state not in {LoginState.SUCCESS, LoginState.FAILED}:
            try:
                self._step()
            except Exception as exc:
                if not self._handle_retry(exc):
                    self.ctx.state = LoginState.FAILED

        if self.ctx.state == LoginState.SUCCESS:
            return self.ctx.session
        return None

    def _step(self) -> None:
        if self.ctx.state == LoginState.FETCH_ENTRY:
            self._fetch_entry_page()
            return
        if self.ctx.state == LoginState.SUBMIT_PASSWORD:
            self._submit_password()
            return
        if self.ctx.state == LoginState.REQUEST_ENHANCE_CODE:
            self._request_enhance_code()
            return
        if self.ctx.state == LoginState.SUBMIT_ENHANCE_CODE:
            self._submit_enhance_code()
            return
        if self.ctx.state == LoginState.AUTHN_ENGINE:
            self._authn_engine()
            return
        if self.ctx.state == LoginState.SESSION_LOGIN:
            self._session_login()
            return
        raise RuntimeError(f"Unknown state: {self.ctx.state}")

    def _fetch_entry_page(self) -> None:
        session = self.ctx.session
        session.headers.clear()
        session.headers.update(self.ctx.entry_headers or {})

        response = session.get(self.ctx.entry_url)              # 这里允许自动重定向, 直接进入到 ActionAuthChain 链接
        self.ctx.response = response
        self.ctx.chain_url = response.url
        
        # 添加一个 Referer
        self.ctx.form_headers["Referer"] = self.ctx.chain_url
        
        self.ctx.authn_lc_key = response.url.split("=")[-1]     # key 是最后一个参数

        for line in response.text.split("\n"):
            if "crypt.js" in line:
                self.ctx.rsa_url = "https://iam.tongji.edu.cn/idp/" + line.split('src="')[1].split('"')[0]
                break

        if not self.ctx.rsa_url:
            raise RuntimeError("无法解析 RSA URL")

        self.ctx.sp_auth_chain_code = myEncrypt.getspAuthChainCode(response.text)
        self.ctx.state = LoginState.SUBMIT_PASSWORD

    def _submit_password(self) -> None:
        data = urlencode(
            {
                "j_username": myEncrypt.STU_NO,
                "j_password": myEncrypt.encryptPassword(self.ctx.rsa_url),
                "j_checkcode": "请输入验证码",
                "op": "login",
                "spAuthChainCode": self.ctx.sp_auth_chain_code,
                "authnLcKey": self.ctx.authn_lc_key,
            }
        )

        session = self.ctx.session
        session.headers.clear()
        session.headers.update(self.ctx.form_headers or {})

        response = session.post(self.ctx.chain_url, data=data, allow_redirects=False)
        self.ctx.response = response

        auth_data = self._parse_auth_response(response.text)

        """
        返回内容形如:

        {
            "authnArguments": null,
            "op": "biometrics",
            "face": "人脸认证",
            "popViewException": "Pop2",
            "loginFailed": "popViewException",
            "servletPath": "/authcenter/ActionAuthChain",
            "actionUrl": "/idp/authcenter/ActionAuthChain",
            "mobile": "123*****456",
            "show_username": "2365472",
            "authnErrorTip": "认证失败,验证码不正确",
            "email": "s***@qq.com"
        }
        """

        login_failed = str(auth_data.get("loginFailed", "")).strip().lower()
        self.ctx.is_enhance = login_failed != "" and login_failed != "false"

        if self.ctx.is_enhance:     # 如果增强认证, 请求发送验证码
            self.ctx.state = LoginState.REQUEST_ENHANCE_CODE
            self.ctx.failed_reason = self._extract_authn_error_tip(auth_data)
        else:                       # 如果不需要增强认证, 说明登录成功, 跳转到 AUTHN_ENGINE
            self.ctx.state = LoginState.AUTHN_ENGINE

    def _request_enhance_code(self) -> None:
        data = urlencode({"j_username": myEncrypt.STU_NO, "type": "email"})

        session = self.ctx.session
        session.headers.clear()
        session.headers.update(self.ctx.form_headers or {})

        session.post(
            "https://iam.tongji.edu.cn/idp/sendCheckCode.do",
            data=data,
            allow_redirects=False,
        )

        self.ctx.state = LoginState.SUBMIT_ENHANCE_CODE

    def _submit_enhance_code(self) -> None:
        time.sleep(self.ctx.wait_seconds)

        with imap_email.EmailVerifier(
            IMAP_USERNAME, IMAP_PASSWORD, IMAP_SERVER, IMAP_PORT
        ) as verifier:
            code = verifier.get_latest_verification_code()

        if not code:
            raise RuntimeError("未读取到验证码")

        data = urlencode(
            {
                "j_username": myEncrypt.STU_NO,
                "type": "email",
                "sms_checkcode": code,
                "popViewException": "Pop2",
                "j_checkcode": "请输入验证码",
                "op": "login",
                "spAuthChainCode": self.ctx.sp_auth_chain_code,
                # "authnLcKey": self.ctx.authn_lc_key,  不需要, 因为在 URL 的 param 里
            }
        )

        session = self.ctx.session
        session.headers.clear()
        session.headers.update(self.ctx.form_headers or {})

        self.ctx.auth_payload = data
        
        response = session.post(
            self.ctx.chain_url,
            data=self.ctx.auth_payload,
            allow_redirects=False
        )
        self.ctx.response = response

        auth_data = self._parse_auth_response(response.text)
        login_failed = str(auth_data.get("loginFailed", "")).strip().lower()
        if login_failed != "" and login_failed != "false":
            error_tip = self._extract_authn_error_tip(auth_data)
            raise RuntimeError(error_tip or "验证码未通过")                 # 没通过, 下一次还在该状态

        self.ctx.state = LoginState.AUTHN_ENGINE        # 通过了, 给 AUTHN_ENGINE 发内容

    def _authn_engine(self) -> None:
        if self.ctx.is_enhance:
            current_auth = "urn_oasis_names_tc_SAML_2.0_ac_classes_SMSUsernamePassword"
        else:
            current_auth = "urn_oasis_names_tc_SAML_2.0_ac_classes_BAMUsernamePassword"

        auth_url = (
            "https://iam.tongji.edu.cn/idp/AuthnEngine?"
            f"currentAuth={current_auth}&authnLcKey={self.ctx.authn_lc_key}&entityId=SYS20230001"
        )

        response = self.ctx.session.post(
            auth_url,
            data=self.ctx.auth_payload,
            allow_redirects=False,
        )
        self.ctx.response = response

        location_url = response.headers.get("Location")

        # 这里必须要换请求头, 手动请求一次才行
        self.ctx.session.headers.clear()
        self.ctx.session.headers.update(self.ctx.sso_headers)

        response = self.ctx.session.get(location_url, allow_redirects=True)
        self.ctx.response = response

        # 跟随重定向后落到 1 系统页面。
        self.ctx.ssologin_url = response.url

        for part in response.text.split(">"):
            if "/static/js/app." in part:
                self.ctx.aes_url = "https://1.tongji.edu.cn" + part.split("src=")[1].split(">")[0]
                print(f"AES URL: {self.ctx.aes_url}")
                break

        self.ctx.state = LoginState.SESSION_LOGIN

    def _session_login(self) -> None:
        url_params = self.ctx.ssologin_url.split("?")[1].split("&")
        login_req_body = {
            "token": url_params[0].split("=")[1],
            "ts": url_params[2].split("=")[1],
            "uid": url_params[1].split("=")[1],
        }

        response = self.ctx.session.post(
            "https://1.tongji.edu.cn/api/sessionservice/session/login",
            data=login_req_body,
        )

        self.ctx.response = response
        if response.status_code != 200:
            raise RuntimeError(f"session login failed: status={response.status_code}")

        print("登录成功！")
        self.ctx.state = LoginState.SUCCESS

    def _handle_retry(self, exc: Exception) -> bool:
        self.ctx.retry_count += 1
        print(f"状态 {self.ctx.state.name} 发生异常: {exc}")

        if self.ctx.retry_count >= self.ctx.max_retry:
            print("登录失败，重试次数已达上限")
            return False

        # 增强认证失败后，回到发送验证码状态；其它失败回到入口状态重走。
        if self.ctx.is_enhance:
            self.ctx.state = LoginState.REQUEST_ENHANCE_CODE
            self.ctx.wait_seconds = min(10 + 5 * self.ctx.retry_count, 60)
        else:
            self.ctx.state = LoginState.FETCH_ENTRY
            self.ctx.wait_seconds = 5

        return True

    @staticmethod
    def _parse_auth_response(response_text: str) -> dict[str, str]:
        try:
            payload = json.loads(response_text)
            if isinstance(payload, dict):
                return {k: "" if v is None else str(v) for k, v in payload.items()}
        except json.JSONDecodeError:
            pass

        # 兼容旧返回: <JSONObject>...</JSONObject>
        xml_root = ET.fromstring(response_text)
        auth_data: dict[str, str] = {}
        for child in xml_root:
            auth_data[child.tag] = "" if child.text is None else child.text.strip()
        return auth_data

    @staticmethod
    def _extract_authn_error_tip(auth_data: dict[str, str]) -> str:
        return auth_data.get("authnErrorTip", "").strip()


def login() -> requests.Session | None:
    machine = SSOLoginStateMachine()
    return machine.run()


def logout(session: requests.Session) -> None:
    logout_data = {
        "sessionid": session.cookies.get_dict().get("sessionid", ""),
        "uid": myEncrypt.STU_NO,
    }

    payload = json.dumps(logout_data, separators=(",", ":"))

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://1.tongji.edu.cn/",
        "Referer": "https://1.tongji.edu.cn/workbench",
        "Content-Type": "application/json",
    }

    session.headers.update(headers)
    response = session.post(
        "https://1.tongji.edu.cn/api/sessionservice/session/logout", data=payload
    )

    if response.status_code == 200:
        print("退出登录成功！")
    else:
        print("退出登录失败！")
        print("状态码：", response.status_code)
