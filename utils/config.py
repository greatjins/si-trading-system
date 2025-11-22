"""
YAML 기반 설정 관리
"""
import os
import yaml
from typing import Any, Dict, Optional
from pathlib import Path


class Config:
    """설정 관리 클래스"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Args:
            config_path: 설정 파일 경로 (기본: config.yaml)
        """
        if config_path is None:
            config_path = "config.yaml"
        
        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        
        if self.config_path.exists():
            self.load()
    
    def load(self) -> None:
        """설정 파일 로드"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self._config = yaml.safe_load(f) or {}
        
        # 환경변수 치환
        self._substitute_env_vars(self._config)
    
    def _substitute_env_vars(self, config: Any) -> None:
        """환경변수 치환 (${VAR_NAME} 형식)"""
        if isinstance(config, dict):
            for key, value in config.items():
                if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
                    env_var = value[2:-1]
                    config[key] = os.getenv(env_var, value)
                elif isinstance(value, (dict, list)):
                    self._substitute_env_vars(value)
        elif isinstance(config, list):
            for item in config:
                self._substitute_env_vars(item)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        설정 값 조회
        
        Args:
            key: 설정 키 (점 표기법 지원, 예: "broker.api_key")
            default: 기본값
        
        Returns:
            설정 값
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """설정 값 설정"""
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def save(self) -> None:
        """설정 파일 저장"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(self._config, f, allow_unicode=True, default_flow_style=False)


# 전역 설정 인스턴스
config = Config()
