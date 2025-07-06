#!/usr/bin/env python3
"""
Скрипт для запуска ML Service сервера
Совместим с PowerShell
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    print("🤖 Запуск ML Service сервера...")
    
    # Определяем корневую директорию проекта
    project_root = Path(__file__).parent
    ml_service_dir = project_root / "ml-service"
    
    # Проверяем существование директории ml-service
    if not ml_service_dir.exists():
        print(f"❌ Директория ml-service не найдена: {ml_service_dir}")
        sys.exit(1)
    
    # Переходим в директорию ml-service
    os.chdir(ml_service_dir)
    print(f"Запуск в директории: {ml_service_dir}")
    
    # Команда для запуска сервера
    cmd = [
        sys.executable, "-m", "uvicorn", 
        "main:app", 
        "--reload", 
        "--host", "127.0.0.1", 
        "--port", "8001"
    ]
    
    print(f"Команда: {' '.join(cmd)}")
    
    try:
        # Запускаем сервер
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n🛑 ML Service остановлен пользователем")
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка запуска ML Service: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 