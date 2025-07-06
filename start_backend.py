#!/usr/bin/env python3
"""
Скрипт для запуска Backend API сервера
Совместим с PowerShell
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    print("🚀 Запуск Backend API сервера...")
    
    # Определяем корневую директорию проекта
    project_root = Path(__file__).parent
    backend_dir = project_root / "backend"
    
    # Проверяем существование директории backend
    if not backend_dir.exists():
        print(f"❌ Директория backend не найдена: {backend_dir}")
        sys.exit(1)
    
    # Переходим в директорию backend
    os.chdir(backend_dir)
    print(f"Запуск в директории: {backend_dir}")
    
    # Команда для запуска сервера
    cmd = [
        sys.executable, "-m", "uvicorn", 
        "app.main:app", 
        "--reload", 
        "--host", "127.0.0.1", 
        "--port", "8000"
    ]
    
    print(f"Команда: {' '.join(cmd)}")
    
    try:
        # Запускаем сервер
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n🛑 Сервер остановлен пользователем")
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка запуска сервера: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 