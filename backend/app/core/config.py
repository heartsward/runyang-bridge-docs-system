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
    DEBUG: bool = True
    
    # 服务器网络配置
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8002
    
    # 数据库配置 - 从环境变量读取，默认使用本地文件
    # 使用绝对路径确保无论从哪个目录启动都使用同一个数据库
    DATABASE_URL: str = "sqlite:///./backend/yunwei_docs.db"
    TEST_DATABASE_URL: Optional[str] = None
    
    # 安全配置
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # 文件上传配置
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 10485760  # 10MB
    ALLOWED_EXTENSIONS: str = "pdf,doc,docx,txt,md,xls,xlsx,csv,jpg,jpeg,png"
    
    # Redis配置
    REDIS_URL: str = "redis://localhost:6379"
    
    # Elasticsearch配置
    ELASTICSEARCH_URL: str = "http://localhost:9200"
    
    # CORS配置 - 新的灵活配置系统
    CORS_ORIGINS: str = ""  # 手动指定的CORS源（逗号分隔）
    CORS_CUSTOM_ORIGINS: str = ""  # 新增：自定义CORS源（为了兼容）
    CORS_MODE: str = "auto"  # 配置模式：auto/manual/mixed
    CORS_AUTO_DETECT: bool = True  # 是否自动检测本机IP
    CORS_INCLUDE_LOCALHOST: bool = True  # 是否包含localhost
    CORS_INCLUDE_HTTPS: bool = True  # 是否包含HTTPS变体
    CORS_FRONTEND_PORT: str = "5173"  # 新增：前端端口
    CORS_EXTRA_PORTS: str = "3000,8080,9000"  # 额外端口（逗号分隔）
    
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
                        base_ports = [5173, 5174, 8002]
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