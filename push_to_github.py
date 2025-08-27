#!/usr/bin/env python3
"""
Скрипт для автоматического пуша изменений в GitHub
"""

import subprocess
import sys
import os
from datetime import datetime

def run_command(command, description):
    """Выполняет команду и выводит результат"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        print(f"✅ {description} завершено (код: {result.returncode})")
        if result.stdout:
            print(f"Вывод: {result.stdout[:300]}...")
        if result.stderr:
            print(f"Ошибки: {result.stderr[:300]}...")
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Ошибка при {description}: {e}")
        return False

def main():
    """Основная функция"""
    print("🚀 АВТОМАТИЧЕСКИЙ ПУШ В GITHUB")
    print("=" * 50)
    
    # Проверяем, что мы в git репозитории
    if not os.path.exists('.git'):
        print("❌ Не найден .git каталог. Убедитесь, что вы в git репозитории.")
        return
    
    # Получаем текущую ветку
    branch_result = subprocess.run(['git', 'branch', '--show-current'], 
                                 capture_output=True, text=True)
    current_branch = branch_result.stdout.strip() if branch_result.stdout else 'main'
    print(f"📋 Текущая ветка: {current_branch}")
    
    # Добавляем все файлы
    if not run_command("git add .", "Добавление файлов"):
        print("❌ Не удалось добавить файлы")
        return
    
    # Проверяем статус
    if not run_command("git status", "Проверка статуса"):
        print("❌ Не удалось проверить статус")
        return
    
    # Создаем коммит
    commit_message = f"🎯 Комплексная система анализа торговых сигналов - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    if not run_command(f'git commit -m "{commit_message}"', "Создание коммита"):
        print("❌ Не удалось создать коммит")
        return
    
    # Пушим в GitHub
    if not run_command(f"git push origin {current_branch}", "Пуш в GitHub"):
        print("❌ Не удалось запушить в GitHub")
        return
    
    print("\n🎉 УСПЕШНО ЗАПУШЕНО В GITHUB!")
    print(f"📝 Коммит: {commit_message}")
    print(f"🌿 Ветка: {current_branch}")

if __name__ == "__main__":
    main()
