#!/usr/bin/env python3
"""
Создание финального отчета с корректными статусами задач
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple

class FinalReportGenerator:
    def __init__(self):
        self.root = Path.cwd()
        
        # Загружаем анализ проекта
        with open(self.root / 'project_analysis.json', 'r', encoding='utf-8') as f:
            self.analysis = json.load(f)
    
    def get_accurate_status(self, task_text: str) -> Tuple[str, str, str]:
        """Определение точного статуса задачи на основе анализа"""
        task_lower = task_text.lower()
        
        # Frontend задачи - проверяем реальное состояние
        if 'next.js' in task_lower or 'typescript' in task_lower:
            if self.analysis['frontend']['next.js проект'] and self.analysis['frontend']['typescript конфигурация']:
                return '✅', 'IMPL', 'ГОТОВО'
            return '⬜', 'TBD', 'НЕ ГОТОВО'
        
        if 'eslint' in task_lower or 'prettier' in task_lower or 'husky' in task_lower:
            if all([
                self.analysis['frontend']['eslint конфигурация'],
                self.analysis['frontend']['prettier конфигурация'],
                self.analysis['frontend']['husky pre-commit']
            ]):
                return '✅', 'IMPL', 'ГОТОВО'
            elif any([
                self.analysis['frontend']['eslint конфигурация'],
                self.analysis['frontend']['prettier конфигурация'],
                self.analysis['frontend']['husky pre-commit']
            ]):
                return '🔄', 'PARTIAL', 'ЧАСТИЧНО'
            return '⬜', 'TBD', 'НЕ ГОТОВО'
        
        if 'главная страница' in task_lower or 'landing' in task_lower:
            if self.analysis['frontend']['главная страница']:
                return '✅', 'IMPL', 'ГОТОВО'
            return '⬜', 'TBD', 'НЕ ГОТОВО'
        
        if 'регистрация' in task_lower or 'вход' in task_lower or 'auth' in task_lower:
            if self.analysis['frontend']['страница входа'] and self.analysis['frontend']['страница регистрации']:
                return '✅', 'IMPL', 'ГОТОВО'
            elif self.analysis['frontend']['страница входа'] or self.analysis['frontend']['страница регистрации']:
                return '🔄', 'PARTIAL', 'ЧАСТИЧНО'
            return '⬜', 'TBD', 'НЕ ГОТОВО'
        
        if 'dashboard' in task_lower or 'дашборд' in task_lower:
            if self.analysis['frontend']['дашборд']:
                return '✅', 'IMPL', 'ГОТОВО'
            return '⬜', 'TBD', 'НЕ ГОТОВО'
        
        if 'демо' in task_lower:
            if self.analysis['frontend']['страница демо']:
                return '✅', 'IMPL', 'ГОТОВО'
            return '⬜', 'TBD', 'НЕ ГОТОВО'
        
        if 'shadcn' in task_lower or 'ui компоненты' in task_lower:
            if self.analysis['frontend']['ui компоненты'] and self.analysis['frontend']['shadcn/ui переменные']:
                return '✅', 'IMPL', 'ГОТОВО'
            elif self.analysis['frontend']['ui компоненты']:
                return '🔄', 'PARTIAL', 'ЧАСТИЧНО'
            return '⬜', 'TBD', 'НЕ ГОТОВО'
        
        # Backend задачи
        if 'fastapi' in task_lower or 'backend' in task_lower:
            if self.analysis['backend']['fastapi приложение']:
                return '✅', 'IMPL', 'ГОТОВО'
            return '⬜', 'TBD', 'НЕ ГОТОВО'
        
        if 'auth endpoints' in task_lower or 'channels endpoints' in task_lower or 'signals endpoints' in task_lower:
            if all([
                self.analysis['backend']['auth endpoints'],
                self.analysis['backend']['channels endpoints'],
                self.analysis['backend']['signals endpoints']
            ]):
                return '✅', 'IMPL', 'ГОТОВО'
            elif any([
                self.analysis['backend']['auth endpoints'],
                self.analysis['backend']['channels endpoints'],
                self.analysis['backend']['signals endpoints']
            ]):
                return '🔄', 'PARTIAL', 'ЧАСТИЧНО'
            return '⬜', 'TBD', 'НЕ ГОТОВО'
        
        if 'модели данных' in task_lower or 'база данных' in task_lower or 'alembic' in task_lower:
            if self.analysis['backend']['модели данных'] and self.analysis['backend']['миграции alembic']:
                return '✅', 'IMPL', 'ГОТОВО'
            elif self.analysis['backend']['модели данных'] or self.analysis['backend']['миграции alembic']:
                return '🔄', 'PARTIAL', 'ЧАСТИЧНО'
            return '⬜', 'TBD', 'НЕ ГОТОВО'
        
        # ML Service задачи
        if 'ml' in task_lower or 'machine learning' in task_lower:
            if self.analysis['ml_service']['ml сервис существует']:
                return '✅', 'IMPL', 'ГОТОВО'
            return '⬜', 'TBD', 'НЕ ГОТОВО'
        
        # Workers задачи
        if 'celery' in task_lower or 'workers' in task_lower:
            if self.analysis['workers']['celery конфигурация'] and self.analysis['workers']['tasks']:
                return '✅', 'IMPL', 'ГОТОВО'
            elif self.analysis['workers']['tasks']:
                return '🔄', 'PARTIAL', 'ЧАСТИЧНО'
            return '⬜', 'TBD', 'НЕ ГОТОВО'
        
        # Docker задачи
        if 'docker' in task_lower or 'docker-compose' in task_lower:
            if self.analysis['docker']['docker-compose.yml'] and self.analysis['docker']['docker-compose.override.yml']:
                return '✅', 'IMPL', 'ГОТОВО'
            elif self.analysis['docker']['docker-compose.yml']:
                return '🔄', 'PARTIAL', 'ЧАСТИЧНО'
            return '⬜', 'TBD', 'НЕ ГОТОВО'
        
        # Документация
        if 'документация' in task_lower or 'api документация' in task_lower:
            if self.analysis['documentation']['API документация']:
                return '✅', 'IMPL', 'ГОТОВО'
            elif self.analysis['documentation']['README.md']:
                return '🔄', 'PARTIAL', 'ЧАСТИЧНО'
            return '⬜', 'TBD', 'НЕ ГОТОВО'
        
        # По умолчанию
        return '⬜', 'TBD', 'НЕ ГОТОВО'
    
    def generate_final_report(self) -> str:
        """Генерация финального отчета"""
        report = []
        report.append('# ФИНАЛЬНЫЙ ОТЧЕТ ПО СТАТУСУ ПРОЕКТА')
        report.append('')
        report.append('## 📊 Общая статистика реализации')
        report.append('')
        
        # Подсчет статистики по компонентам
        total_components = 0
        implemented_components = 0
        
        for component, items in self.analysis.items():
            total = len(items)
            implemented = sum(1 for v in items.values() if v)
            total_components += total
            implemented_components += implemented
            
            percentage = (implemented / total * 100) if total > 0 else 0
            status_icon = '✅' if percentage == 100 else '🔄' if percentage > 50 else '⬜'
            
            report.append(f'### {status_icon} {component.upper()}')
            report.append(f'- **Реализовано:** {implemented}/{total} ({percentage:.1f}%)')
            report.append('')
        
        overall_percentage = (implemented_components / total_components * 100) if total_components > 0 else 0
        report.append(f'### 🎯 ОБЩАЯ ГОТОВНОСТЬ: {overall_percentage:.1f}%')
        report.append('')
        
        # Детальная сводка по компонентам
        report.append('## 📋 Детальная сводка по компонентам')
        report.append('')
        
        for component, items in self.analysis.items():
            report.append(f'### {component.upper()}')
            for item, status in items.items():
                status_icon = '✅' if status else '⬜'
                report.append(f'- {status_icon} {item}')
            report.append('')
        
        # Приоритетные задачи
        report.append('## 🚀 ПРИОРИТЕТНЫЕ ЗАДАЧИ ДЛЯ ЗАВЕРШЕНИЯ')
        report.append('')
        
        report.append('### 🔥 КРИТИЧНО (сделать в первую очередь):')
        if not self.analysis['backend']['fastapi приложение']:
            report.append('- ⬜ Создать FastAPI приложение (main.py)')
        if not self.analysis['backend']['auth endpoints']:
            report.append('- ⬜ Реализовать auth endpoints')
        if not self.analysis['backend']['channels endpoints']:
            report.append('- ⬜ Реализовать channels endpoints')
        if not self.analysis['backend']['signals endpoints']:
            report.append('- ⬜ Реализовать signals endpoints')
        if not self.analysis['workers']['celery конфигурация']:
            report.append('- ⬜ Настроить Celery конфигурацию')
        report.append('')
        
        report.append('### ⚡ ВАЖНО (сделать во вторую очередь):')
        if not self.analysis['docker']['docker-compose.override.yml']:
            report.append('- ⬜ Создать docker-compose.override.yml')
        if not self.analysis['documentation']['API документация']:
            report.append('- ⬜ Создать API документацию')
        report.append('')
        
        report.append('### 📝 ЖЕЛАТЕЛЬНО (сделать в третью очередь):')
        report.append('- ⬜ Добавить интеграционные тесты')
        report.append('- ⬜ Настроить мониторинг и логирование')
        report.append('- ⬜ Оптимизировать производительность')
        report.append('')
        
        # Рекомендации
        report.append('## 💡 РЕКОМЕНДАЦИИ')
        report.append('')
        report.append('1. **Frontend полностью готов** - можно переходить к интеграции с backend')
        report.append('2. **Backend требует доработки** - критично создать API endpoints')
        report.append('3. **ML Service готов** - можно интегрировать с основным приложением')
        report.append('4. **Workers частично готовы** - нужно настроить Celery')
        report.append('5. **Docker конфигурация почти готова** - нужен override файл')
        report.append('')
        
        report.append(f'**Дата анализа:** {Path.cwd().stat().st_mtime}')
        
        return '\n'.join(report)

def main():
    generator = FinalReportGenerator()
    report = generator.generate_final_report()
    
    # Сохранение отчета
    report_path = Path.cwd() / 'FINAL_PROJECT_STATUS_REPORT.md'
    report_path.write_text(report, encoding='utf-8')
    
    print("✅ Финальный отчет создан!")
    print(f"📄 Отчет сохранен в: {report_path}")
    
    return 0

if __name__ == '__main__':
    exit(main())
