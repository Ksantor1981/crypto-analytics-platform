#!/usr/bin/env python3
"""
Анализ текущего состояния проекта и сравнение с задачами
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple, Set
import json

class ProjectAnalyzer:
    def __init__(self):
        self.root = Path.cwd()
        self.status_map = {
            'IMPL': '✅ ГОТОВО',
            'PARTIAL': '🔄 ЧАСТИЧНО', 
            'TBD': '⬜ НЕ ГОТОВО'
        }
        
    def analyze_frontend_structure(self) -> Dict[str, bool]:
        """Анализ структуры frontend"""
        frontend_path = self.root / 'frontend'
        results = {}
        
        # Проверка основных файлов и папок
        results['next.js проект'] = (frontend_path / 'package.json').exists()
        results['typescript конфигурация'] = (frontend_path / 'tsconfig.json').exists()
        results['tailwind конфигурация'] = (frontend_path / 'tailwind.config.js').exists()
        results['eslint конфигурация'] = (frontend_path / '.eslintrc.json').exists()
        results['prettier конфигурация'] = (frontend_path / '.prettierrc').exists()
        results['husky pre-commit'] = (frontend_path / '.husky').exists()
        
        # Проверка основных страниц
        pages_path = frontend_path / 'pages'
        results['главная страница'] = (pages_path / 'index.tsx').exists()
        results['страница демо'] = (pages_path / 'demo.tsx').exists()
        results['страница входа'] = (pages_path / 'auth' / 'login.tsx').exists()
        results['страница регистрации'] = (pages_path / 'auth' / 'register.tsx').exists()
        results['дашборд'] = (pages_path / 'dashboard.tsx').exists()
        
        # Проверка компонентов
        components_path = frontend_path / 'components'
        results['ui компоненты'] = (components_path / 'ui').exists()
        results['language switcher'] = (components_path / 'LanguageSwitcher.tsx').exists()
        results['language context'] = (frontend_path / 'contexts' / 'LanguageContext.tsx').exists()
        
        # Проверка стилей
        results['глобальные стили'] = (frontend_path / 'styles' / 'globals.css').exists()
        results['shadcn/ui переменные'] = self._check_shadcn_variables()
        
        return results
    
    def _check_shadcn_variables(self) -> bool:
        """Проверка наличия CSS переменных для shadcn/ui"""
        css_file = self.root / 'frontend' / 'styles' / 'globals.css'
        if not css_file.exists():
            return False
        
        content = css_file.read_text(encoding='utf-8')
        return ':root' in content and '--background' in content
    
    def analyze_backend_structure(self) -> Dict[str, bool]:
        """Анализ структуры backend"""
        backend_path = self.root / 'backend'
        results = {}
        
        # Основные файлы
        results['fastapi приложение'] = (backend_path / 'main.py').exists()
        results['requirements.txt'] = (backend_path / 'requirements.txt').exists()
        results['dockerfile'] = (backend_path / 'Dockerfile').exists()
        
        # API endpoints
        api_path = backend_path / 'app' / 'api'
        if api_path.exists():
            results['auth endpoints'] = (api_path / 'auth.py').exists()
            results['channels endpoints'] = (api_path / 'channels.py').exists()
            results['signals endpoints'] = (api_path / 'signals.py').exists()
        
        # Модели и база данных
        models_path = backend_path / 'app' / 'models'
        results['модели данных'] = models_path.exists()
        results['миграции alembic'] = (backend_path / 'alembic').exists()
        
        return results
    
    def analyze_ml_service(self) -> Dict[str, bool]:
        """Анализ ML сервиса"""
        ml_path = self.root / 'ml-service'
        results = {}
        
        results['ml сервис существует'] = ml_path.exists()
        if ml_path.exists():
            results['main.py'] = (ml_path / 'main.py').exists()
            results['requirements.txt'] = (ml_path / 'requirements.txt').exists()
            results['dockerfile'] = (ml_path / 'Dockerfile').exists()
            results['модели ml'] = (ml_path / 'models').exists()
        
        return results
    
    def analyze_workers(self) -> Dict[str, bool]:
        """Анализ workers"""
        workers_path = self.root / 'workers'
        results = {}
        
        results['workers папка'] = workers_path.exists()
        if workers_path.exists():
            results['celery конфигурация'] = (workers_path / 'celery_app.py').exists()
            results['tasks'] = (workers_path / 'tasks.py').exists()
            results['dockerfile'] = (workers_path / 'Dockerfile').exists()
        
        return results
    
    def analyze_docker_setup(self) -> Dict[str, bool]:
        """Анализ Docker конфигурации"""
        results = {}
        
        results['docker-compose.yml'] = (self.root / 'docker-compose.yml').exists()
        results['docker-compose.override.yml'] = (self.root / 'docker-compose.override.yml').exists()
        results['.env файл'] = (self.root / '.env').exists()
        results['.env.example'] = (self.root / '.env.example').exists()
        
        return results
    
    def analyze_documentation(self) -> Dict[str, bool]:
        """Анализ документации"""
        results = {}
        
        results['README.md'] = (self.root / 'README.md').exists()
        results['TASKS2.md'] = (self.root / 'TASKS2.md').exists()
        results['ТЗ документ'] = (self.root / 'ТЗ.md').exists()
        results['API документация'] = (self.root / 'docs' / 'api.md').exists()
        
        return results
    
    def get_task_status(self, task_name: str, component_results: Dict[str, bool]) -> str:
        """Определение статуса задачи на основе анализа"""
        task_lower = task_name.lower()
        
        # Frontend задачи
        if 'next.js' in task_lower or 'typescript' in task_lower:
            if 'next.js проект' in component_results and component_results['next.js проект']:
                return 'IMPL'
            return 'TBD'
        
        if 'eslint' in task_lower or 'prettier' in task_lower or 'husky' in task_lower:
            if all([
                component_results.get('eslint конфигурация', False),
                component_results.get('prettier конфигурация', False),
                component_results.get('husky pre-commit', False)
            ]):
                return 'IMPL'
            elif any([
                component_results.get('eslint конфигурация', False),
                component_results.get('prettier конфигурация', False),
                component_results.get('husky pre-commit', False)
            ]):
                return 'PARTIAL'
            return 'TBD'
        
        if 'главная страница' in task_lower or 'landing' in task_lower:
            if component_results.get('главная страница', False):
                return 'IMPL'
            return 'TBD'
        
        if 'регистрация' in task_lower or 'вход' in task_lower or 'auth' in task_lower:
            if all([
                component_results.get('страница входа', False),
                component_results.get('страница регистрации', False)
            ]):
                return 'IMPL'
            elif any([
                component_results.get('страница входа', False),
                component_results.get('страница регистрации', False)
            ]):
                return 'PARTIAL'
            return 'TBD'
        
        if 'dashboard' in task_lower or 'дашборд' in task_lower:
            if component_results.get('дашборд', False):
                return 'IMPL'
            return 'TBD'
        
        if 'docker' in task_lower:
            if component_results.get('docker-compose.yml', False):
                return 'IMPL'
            return 'TBD'
        
        # По умолчанию
        return 'TBD'
    
    def analyze_all(self) -> Dict[str, Dict[str, bool]]:
        """Полный анализ проекта"""
        return {
            'frontend': self.analyze_frontend_structure(),
            'backend': self.analyze_backend_structure(),
            'ml_service': self.analyze_ml_service(),
            'workers': self.analyze_workers(),
            'docker': self.analyze_docker_setup(),
            'documentation': self.analyze_documentation()
        }
    
    def generate_report(self) -> str:
        """Генерация отчета"""
        analysis = self.analyze_all()
        
        report = []
        report.append('# АНАЛИЗ ТЕКУЩЕГО СОСТОЯНИЯ ПРОЕКТА')
        report.append('')
        report.append('## Общая сводка по компонентам')
        report.append('')
        
        for component, results in analysis.items():
            total = len(results)
            implemented = sum(1 for v in results.values() if v)
            percentage = (implemented / total * 100) if total > 0 else 0
            
            report.append(f'### {component.upper()}')
            report.append(f'- Реализовано: {implemented}/{total} ({percentage:.1f}%)')
            report.append('')
            
            for item, status in results.items():
                status_icon = '✅' if status else '⬜'
                report.append(f'- {status_icon} {item}')
            report.append('')
        
        # Сохранение детального анализа в JSON
        json_path = self.root / 'project_analysis.json'
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)
        
        report.append(f'Детальный анализ сохранен в: {json_path}')
        
        return '\n'.join(report)

def main():
    analyzer = ProjectAnalyzer()
    report = analyzer.generate_report()
    
    # Сохранение отчета
    report_path = Path.cwd() / 'CURRENT_PROJECT_STATUS.md'
    report_path.write_text(report, encoding='utf-8')
    
    print("Анализ завершен!")
    print(f"Отчет сохранен в: {report_path}")
    print(f"Детальный анализ в: project_analysis.json")
    
    return 0

if __name__ == '__main__':
    exit(main())
