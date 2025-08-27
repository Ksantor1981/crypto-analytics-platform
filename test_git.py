#!/usr/bin/env python3
"""
Тестовый файл для проверки работы терминала
"""

import os
import subprocess
import sys

def test_git():
    """Тестируем Git команды"""
    print("🔍 Тестирование Git команд...")
    
    try:
        # Проверяем статус
        result = subprocess.run(['git', 'status'], capture_output=True, text=True)
        print(f"Git status: {result.returncode}")
        if result.stdout:
            print("STDOUT:", result.stdout[:200])
        if result.stderr:
            print("STDERR:", result.stderr[:200])
            
        # Проверяем последние коммиты
        result = subprocess.run(['git', 'log', '--oneline', '-3'], capture_output=True, text=True)
        print(f"Git log: {result.returncode}")
        if result.stdout:
            print("Последние коммиты:")
            print(result.stdout)
            
        # Проверяем remote
        result = subprocess.run(['git', 'remote', '-v'], capture_output=True, text=True)
        print(f"Git remote: {result.returncode}")
        if result.stdout:
            print("Remote repositories:")
            print(result.stdout)
            
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    test_git()
