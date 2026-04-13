from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional, List
import socket
import os


class Settings(BaseSettings):
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True
    )
    
    # 项目基本信息
    PROJECT_NAME: str = "运维文档管理系统"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False
    
    # 服务器网络配置
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8002
    
    # 数据库配置 - 从环境变量读取，默认使用本地文件
    # 使用绝对路径，确保数据库文件在backend目录下
    DATABASE_URL: str = f"sqlite:///{os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'yunwei_docs.db'))}"
    TEST_DATABASE_URL: Optional[str] = None
    
    # 安全配置
    SECRET_KEY: str = "REQUIRED_SET_IN_ENV_FILE"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    # 文件上传配置
    UPLOAD_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'uploads'))
    MAX_FILE_SIZE: int = 10485760  # 10MB
    ALLOWED_EXTENSIONS: str = "pdf,doc,docx,txt,md,xls,xlsx,csv,jpg,jpeg,png,bmp,tiff,gif,webp"
    
    # Redis配置
    REDIS_URL: str = "redis://localhost:6379"
    
    # Elasticsearch配置
    ELASTICSEARCH_URL: str = "http://localhost:9200"
    
    # 时区配置
    TIMEZONE: str = "Asia/Shanghai"  # 默认时区为北京时间
    
    # AI功能开关
    ENABLE_CONTENT_EXTRACTION: bool = True
    ENABLE_AI_ANALYSIS: bool = False
    ENABLE_SEARCH: bool = True
    ENABLE_USER_ANALYTICS: bool = True
    
    # AI服务配置
    AI_DEFAULT_PROVIDER: str = "openai"
    
    # OpenAI配置
    AI_OPENAI_API_KEY: str = ""
    AI_OPENAI_API_URL: str = "https://api.openai.com/v1/chat/completions"
    AI_OPENAI_MODEL: str = "gpt-4o-mini"
    AI_OPENAI_MAX_TOKENS: int = 2000
    AI_OPENAI_TEMPERATURE: float = 0.3
    
    # Anthropic配置
    AI_ANTHROPIC_API_KEY: str = ""
    AI_ANTHROPIC_API_URL: str = "https://api.anthropic.com/v1/messages"
    AI_ANTHROPIC_MODEL: str = "claude-3-haiku-20240307"
    
    # 阿里云通义配置
    AI_ALIBABA_API_KEY: str = ""
    AI_ALIBABA_ENDPOINT: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    AI_ALIBABA_MODEL: str = "qwen-plus"
    
    # 智谱AI配置
    AI_ZHIPU_API_KEY: str = ""
    AI_ZHIPU_API_URL: str = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    AI_ZHIPU_MODEL: str = "glm-4-flash"
    
    # MiniMax配置
    AI_MINIMAX_API_KEY: str = ""
    AI_MINIMAX_API_URL: str = "https://api.minimaxi.com/anthropic"
    AI_MINIMAX_MODEL: str = "MiniMax-M2.7"
    AI_MINIMAX_GROUP_ID: str = ""
    
    # AI通用配置
    AI_MAX_RETRIES: int = 3
    AI_TIMEOUT: int = 30
    
    # AI限流配置
    AI_RATE_LIMIT_ENABLED: bool = True
    AI_RATE_LIMIT_REQUESTS: int = 10
    AI_RATE_LIMIT_PER_USER: int = 5
    
    # AI缓存配置
    AI_CACHE_STRATEGY: str = "memory"
    AI_CACHE_TTL: int = 3600
    
    # AI成本控制
    AI_COST_LIMIT_ENABLED: bool = False
    AI_COST_LIMIT_DAILY: float = 10.0
    
    # AI降级配置
    AI_FALLBACK_ENABLED: bool = True
    AI_FALLBACK_TO_TRADITIONAL: bool = True
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/app.log"
    LOG_TO_CONSOLE: bool = True
    
    # 性能配置
    WORKERS: int = 0
    RELOAD: bool = False
    REQUEST_TIMEOUT: int = 30
    
    # 部署环境标识
    DEPLOY_ENV: str = "production"
    DEPLOY_SERVER: str = "auto-detect"
    
    # 监控配置
    ENABLE_MONITORING: bool = False
    MONITORING_DATA_PATH: str = "./monitoring"
    
    # 自定义配置
    ADMIN_EMAIL: str = "admin@runyang.com"
    ENABLE_NOTIFICATIONS: bool = False
    
    # CORS配置 - 新的灵活配置系统
    CORS_ORIGINS: str = ""  # 手动指定的CORS源（逗号分隔）
    CORS_CUSTOM_ORIGINS: str = ""  # 新增：自定义CORS源（为了兼容）
    CORS_MODE: str = "auto"  # 配置模式：auto/manual/mixed
    CORS_AUTO_DETECT: bool = True  # 是否自动检测本机IP
    CORS_INCLUDE_LOCALHOST: bool = True  # 是否包含localhost
    CORS_INCLUDE_HTTPS: bool = True  # 是否包含HTTPS变体
    CORS_FRONTEND_PORT: str = "5173"  # 前端端口（开发和生产统一）
    CORS_EXTRA_PORTS: str = "3000,8080,9000,5174,5175"  # 额外端口（添加了5174和5175）
    
    @property
    def BACKEND_CORS_ORIGINS(self) -> List[str]:
        """动态获取CORS允许的源"""
        origins = []
        
        # 手动模式：仅使用指定的地址
        if self.CORS_MODE.lower() == "manual":
            manual_origins = []
            # 支持旧的CORS_ORIGINS和新的CORS_CUSTOM_ORIGINS
            cors_config = self.CORS_CUSTOM_ORIGINS or self.CORS_ORIGINS
            if cors_config:
                manual_origins = [origin.strip() for origin in cors_config.split(",") if origin.strip()]
                print(f"[CORS] 手动模式：使用指定地址 {manual_origins}")
                return manual_origins
            else:
                print("[CORS] 警告：手动模式但未指定CORS源，回退到localhost")
                return [f"http://localhost:{self.CORS_FRONTEND_PORT}"]
        
        # 自动模式或混合模式：智能检测和配置
        else:  # auto or mixed mode
            mode_name = "混合模式" if self.CORS_MODE.lower() == "mixed" else "自动模式"
            print(f"[CORS] {mode_name}：智能检测CORS配置")
            
            # 1. 包含localhost地址
            if self.CORS_INCLUDE_LOCALHOST:
                frontend_port = int(self.CORS_FRONTEND_PORT) if self.CORS_FRONTEND_PORT.isdigit() else 5173
                base_ports = [frontend_port]
                
                extra_ports = []
                if self.CORS_EXTRA_PORTS:
                    try:
                        extra_ports = [int(p.strip()) for p in self.CORS_EXTRA_PORTS.split(",") if p.strip()]
                    except ValueError:
                        pass
                
                all_ports = base_ports + extra_ports
                for port in all_ports:
                    origins.extend([
                        f"http://localhost:{port}",
                        f"http://127.0.0.1:{port}"
                    ])
                    if self.CORS_INCLUDE_HTTPS:
                        origins.extend([
                            f"https://localhost:{port}",
                            f"https://127.0.0.1:{port}"
                        ])
            
            # 2. 添加手动指定的地址
            cors_config = self.CORS_CUSTOM_ORIGINS or self.CORS_ORIGINS
            if cors_config:
                manual_origins = [origin.strip() for origin in cors_config.split(",") if origin.strip()]
                origins.extend(manual_origins)
                print(f"[CORS] 添加手动指定地址：{manual_origins}")
            
            # 3. 自动检测本机IP地址
            if self.CORS_AUTO_DETECT:
                try:
                    detected_ips = self._detect_local_ips()
                    if detected_ips:
                        base_ports = [5173]  # 只使用主要前端端口
                        extra_ports = []
                        if self.CORS_EXTRA_PORTS:
                            try:
                                extra_ports = [int(p.strip()) for p in self.CORS_EXTRA_PORTS.split(",") if p.strip()]
                            except ValueError:
                                pass
                        
                        all_ports = base_ports + extra_ports
                        for ip in detected_ips:
                            for port in all_ports:
                                origins.append(f"http://{ip}:{port}")
                                if self.CORS_INCLUDE_HTTPS:
                                    origins.append(f"https://{ip}:{port}")
                        
                        print(f"[CORS] 检测到本机IP：{detected_ips}")
                except Exception as e:
                    print(f"[CORS] 警告：IP自动检测失败: {e}")
            
            # 去重并返回
            unique_origins = list(set(origins))
            print(f"[CORS] 最终配置：{len(unique_origins)} 个源")
            return unique_origins
    
    def _detect_local_ips(self) -> List[str]:
        """检测本机IP地址"""
        local_ips = []
        try:
            # 方法1：通过socket连接检测主要IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            primary_ip = s.getsockname()[0]
            s.close()
            if primary_ip and not primary_ip.startswith("127."):
                local_ips.append(primary_ip)
        except Exception:
            pass
        
        try:
            # 方法2：通过hostname获取所有IP
            hostname = socket.gethostname()
            host_ips = socket.gethostbyname_ex(hostname)[2]
            for ip in host_ips:
                if not ip.startswith("127.") and ip not in local_ips:
                    local_ips.append(ip)
        except Exception:
            pass
        
        return local_ips
    


def get_local_ip():
    """获取本机局域网IP地址"""
    try:
        # 连接到一个不存在的地址来获取本机IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.254.254.254", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "127.0.0.1"


settings = Settings()