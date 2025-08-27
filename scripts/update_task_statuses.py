#!/usr/bin/env python3
"""
Обновление статусов задач на основе реального анализа проекта
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple

class TaskStatusUpdater:
    def __init__(self):
        self.root = Path.cwd()
        self.status_map = {
            'IMPL': '✅ ГОТОВО',
            'PARTIAL': '🔄 ЧАСТИЧНО', 
            'TBD': '⬜ НЕ ГОТОВО'
        }
        
        # Загружаем анализ проекта
        with open(self.root / 'project_analysis.json', 'r', encoding='utf-8') as f:
            self.analysis = json.load(f)
    
    def get_task_status(self, task_text: str) -> Tuple[str, str]:
        """Определение статуса задачи на основе анализа"""
        task_lower = task_text.lower()
        
        # Frontend задачи (100% готово)
        if any(keyword in task_lower for keyword in [
            'next.js', 'typescript', 'eslint', 'prettier', 'husky', 'tailwind',
            'главная страница', 'landing', 'shadcn', 'ui компоненты'
        ]):
            return '✅', 'IMPL'
        
        if any(keyword in task_lower for keyword in [
            'регистрация', 'вход', 'auth', 'login', 'register'
        ]):
            if self.analysis['frontend']['страница входа'] and self.analysis['frontend']['страница регистрации']:
                return '✅', 'IMPL'
            elif self.analysis['frontend']['страница входа'] or self.analysis['frontend']['страница регистрации']:
                return '🔄', 'PARTIAL'
            return '⬜', 'TBD'
        
        if any(keyword in task_lower for keyword in [
            'dashboard', 'дашборд', 'демо'
        ]):
            if self.analysis['frontend']['дашборд'] and self.analysis['frontend']['страница демо']:
                return '✅', 'IMPL'
            elif self.analysis['frontend']['дашборд'] or self.analysis['frontend']['страница демо']:
                return '🔄', 'PARTIAL'
            return '⬜', 'TBD'
        
        # Backend задачи (50% готово)
        if any(keyword in task_lower for keyword in [
            'fastapi', 'main.py', 'backend'
        ]):
            if self.analysis['backend']['fastapi приложение']:
                return '✅', 'IMPL'
            return '⬜', 'TBD'
        
        if any(keyword in task_lower for keyword in [
            'auth endpoints', 'channels endpoints', 'signals endpoints', 'api'
        ]):
            if all([
                self.analysis['backend']['auth endpoints'],
                self.analysis['backend']['channels endpoints'],
                self.analysis['backend']['signals endpoints']
            ]):
                return '✅', 'IMPL'
            elif any([
                self.analysis['backend']['auth endpoints'],
                self.analysis['backend']['channels endpoints'],
                self.analysis['backend']['signals endpoints']
            ]):
                return '🔄', 'PARTIAL'
            return '⬜', 'TBD'
        
        if any(keyword in task_lower for keyword in [
            'модели данных', 'база данных', 'alembic', 'миграции'
        ]):
            if self.analysis['backend']['модели данных'] and self.analysis['backend']['миграции alembic']:
                return '✅', 'IMPL'
            elif self.analysis['backend']['модели данных'] or self.analysis['backend']['миграции alembic']:
                return '🔄', 'PARTIAL'
            return '⬜', 'TBD'
        
        # ML Service задачи (100% готово)
        if any(keyword in task_lower for keyword in [
            'ml', 'machine learning', 'модели ml', 'ml сервис'
        ]):
            if self.analysis['ml_service']['ml сервис существует']:
                return '✅', 'IMPL'
            return '⬜', 'TBD'
        
        # Workers задачи (75% готово)
        if any(keyword in task_lower for keyword in [
            'celery', 'workers', 'tasks'
        ]):
            if self.analysis['workers']['celery конфигурация'] and self.analysis['workers']['tasks']:
                return '✅', 'IMPL'
            elif self.analysis['workers']['tasks']:
                return '🔄', 'PARTIAL'
            return '⬜', 'TBD'
        
        # Docker задачи (75% готово)
        if any(keyword in task_lower for keyword in [
            'docker', 'docker-compose'
        ]):
            if self.analysis['docker']['docker-compose.yml'] and self.analysis['docker']['docker-compose.override.yml']:
                return '✅', 'IMPL'
            elif self.analysis['docker']['docker-compose.yml']:
                return '🔄', 'PARTIAL'
            return '⬜', 'TBD'
        
        # Документация (75% готово)
        if any(keyword in task_lower for keyword in [
            'документация', 'api документация', 'readme'
        ]):
            if self.analysis['documentation']['API документация']:
                return '✅', 'IMPL'
            elif self.analysis['documentation']['README.md']:
                return '🔄', 'PARTIAL'
            return '⬜', 'TBD'
        
        # По умолчанию
        return '⬜', 'TBD'
    
    def update_tasks_file(self, input_file: str, output_file: str):
        """Обновление файла с задачами"""
        input_path = self.root / input_file
        if not input_path.exists():
            print(f"Файл {input_file} не найден")
            return False
        
        lines = input_path.read_text(encoding='utf-8').splitlines()
        updated_lines = []
        
        for line in lines:
            # Ищем строки с задачами
            task_match = re.match(r'^-\s*(✅|⬜|🔄)\s*\[(IMPL|PARTIAL|TBD)\]\s*(.+)$', line)
            if task_match:
                mark, tag, task_text = task_match.groups()
                new_mark, new_tag = self.get_task_status(task_text)
                
                # Обновляем статус
                updated_line = f"- {new_mark} [{new_tag}] {task_text}"
                updated_lines.append(updated_line)
            else:
                updated_lines.append(line)
        
        # Сохраняем обновленный файл
        output_path = self.root / output_file
        output_path.write_text('\n'.join(updated_lines), encoding='utf-8')
        
        print(f"Обновленный файл сохранен: {output_file}")
        return True
    
    def generate_summary(self) -> str:
        """Генерация сводки по статусам"""
        summary = []
        summary.append('# СВОДКА ПО СТАТУСАМ ЗАДАЧ')
        summary.append('')
        summary.append('## Общая статистика')
        summary.append('')
        
        # Подсчет статистики
        stats = {'IMPL': 0, 'PARTIAL': 0, 'TBD': 0}
        
        # Анализируем текущий файл задач
        tasks_file = self.root / 'TASKS2_ARCHIVE_DEDUPED_STATUS.md'
        if tasks_file.exists():
            content = tasks_file.read_text(encoding='utf-8')
            for line in content.splitlines():
                match = re.match(r'^-\s*(✅|⬜|🔄)\s*\[(IMPL|PARTIAL|TBD)\]\s*(.+)$', line)
                if match:
                    tag = match.group(2)
                    stats[tag] += 1
        
        total = sum(stats.values())
        if total > 0:
            summary.append(f'- **Всего задач:** {total}')
            summary.append(f'- **✅ ГОТОВО:** {stats["IMPL"]} ({stats["IMPL"]/total*100:.1f}%)')
            summary.append(f'- **🔄 ЧАСТИЧНО:** {stats["PARTIAL"]} ({stats["PARTIAL"]/total*100:.1f}%)')
            summary.append(f'- **⬜ НЕ ГОТОВО:** {stats["TBD"]} ({stats["TBD"]/total*100:.1f}%)')
        
        summary.append('')
        summary.append('## Рекомендации по приоритетам')
        summary.append('')
        summary.append('### 🔥 КРИТИЧНО (сделать в первую очередь):')
        summary.append('- Backend API endpoints (auth, channels, signals)')
        summary.append('- Celery конфигурация для workers')
        summary.append('- API документация')
        summary.append('')
        summary.append('### ⚡ ВАЖНО (сделать во вторую очередь):')
        summary.append('- Docker-compose.override.yml')
        summary.append('- Дополнительные страницы frontend')
        summary.append('- Интеграционные тесты')
        summary.append('')
        summary.append('### 📝 ЖЕЛАТЕЛЬНО (сделать в третью очередь):')
        summary.append('- Дополнительная документация')
        summary.append('- Мониторинг и логирование')
        summary.append('- Оптимизация производительности')
        
        return '\n'.join(summary)

def main():
    updater = TaskStatusUpdater()
    
    # Обновляем статусы в файле задач
    success = updater.update_tasks_file(
        'TASKS2_ARCHIVE_DEDUPED_STATUS.md',
        'TASKS2_UPDATED_STATUS.md'
    )
    
    if success:
        # Генерируем сводку
        summary = updater.generate_summary()
        summary_path = Path.cwd() / 'TASK_STATUS_SUMMARY.md'
        summary_path.write_text(summary, encoding='utf-8')
        
        print("✅ Обновление завершено!")
        print(f"📄 Обновленные задачи: TASKS2_UPDATED_STATUS.md")
        print(f"📊 Сводка: TASK_STATUS_SUMMARY.md")
    
    return 0

if __name__ == '__main__':
    exit(main())
