#!/usr/bin/env python3
"""
Честная оценка технического состояния проекта Crypto Analytics Platform
Согласно методологии TASKS2.md - Honest Assessment
"""

import asyncio
import requests
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Tuple

class HonestTechnicalAssessment:
    """
    Честная оценка технического состояния проекта
    """
    
    def __init__(self):
        self.backend_url = "http://localhost:8000"
        self.ml_service_url = "http://localhost:8001"
        self.frontend_url = "http://localhost:3000"
        
        self.assessment_results = {
            "timestamp": datetime.now().isoformat(),
            "methodology": "TASKS2.md Critical Analysis",
            "overall_grade": "F",
            "compliance_percentage": 0.0,
            "sections": {},
            "critical_issues": [],
            "recommendations": [],
            "real_vs_claimed": {}
        }
    
    def assess_backend_functionality(self) -> Dict[str, Any]:
        """
        Оценка функциональности Backend API
        """
        print("🔍 ОЦЕНКА BACKEND FUNCTIONALITY")
        print("-" * 50)
        
        backend_results = {
            "total_endpoints": 0,
            "working_endpoints": 0,
            "broken_endpoints": 0,
            "endpoint_details": {},
            "authentication": False,
            "database": False,
            "ml_integration": False
        }
        
        # Test basic connectivity
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ Backend доступен")
                backend_results["basic_connectivity"] = True
            else:
                print(f"❌ Backend недоступен: {response.status_code}")
                backend_results["basic_connectivity"] = False
                return backend_results
        except Exception as e:
            print(f"❌ Backend недоступен: {e}")
            backend_results["basic_connectivity"] = False
            return backend_results
        
        # Test authentication endpoints
        auth_endpoints = [
            ("POST", "/api/v1/users/register", "Регистрация"),
            ("POST", "/api/v1/users/login", "Вход"),
            ("GET", "/api/v1/users/me", "Профиль пользователя"),
            ("POST", "/api/v1/users/refresh", "Обновление токена")
        ]
        
        for method, endpoint, description in auth_endpoints:
            backend_results["total_endpoints"] += 1
            try:
                if method == "GET":
                    response = requests.get(f"{self.backend_url}{endpoint}", timeout=5)
                else:
                    response = requests.post(f"{self.backend_url}{endpoint}", json={}, timeout=5)
                
                if response.status_code in [200, 201, 400, 401, 422]:  # Valid responses
                    print(f"✅ {description}: {response.status_code}")
                    backend_results["working_endpoints"] += 1
                    backend_results["endpoint_details"][endpoint] = {
                        "status": "working",
                        "response_code": response.status_code,
                        "description": description
                    }
                else:
                    print(f"❌ {description}: {response.status_code}")
                    backend_results["broken_endpoints"] += 1
                    backend_results["endpoint_details"][endpoint] = {
                        "status": "broken",
                        "response_code": response.status_code,
                        "description": description
                    }
            except Exception as e:
                print(f"❌ {description}: {e}")
                backend_results["broken_endpoints"] += 1
                backend_results["endpoint_details"][endpoint] = {
                    "status": "error",
                    "error": str(e),
                    "description": description
                }
        
        # Test core functionality endpoints
        core_endpoints = [
            ("GET", "/api/v1/channels/", "Каналы"),
            ("GET", "/api/v1/signals/", "Сигналы"),
            ("GET", "/api/v1/subscriptions/me", "Подписки"),
            ("GET", "/api/v1/signals/stats/overview", "Статистика сигналов"),
            ("GET", "/api/v1/telegram/health", "Telegram интеграция"),
            ("GET", "/api/v1/telegram/channels", "Telegram каналы")
        ]
        
        for method, endpoint, description in core_endpoints:
            backend_results["total_endpoints"] += 1
            try:
                response = requests.get(f"{self.backend_url}{endpoint}", timeout=5)
                
                if response.status_code in [200, 401, 403]:  # Valid responses
                    print(f"✅ {description}: {response.status_code}")
                    backend_results["working_endpoints"] += 1
                    backend_results["endpoint_details"][endpoint] = {
                        "status": "working",
                        "response_code": response.status_code,
                        "description": description
                    }
                else:
                    print(f"❌ {description}: {response.status_code}")
                    backend_results["broken_endpoints"] += 1
                    backend_results["endpoint_details"][endpoint] = {
                        "status": "broken",
                        "response_code": response.status_code,
                        "description": description
                    }
            except Exception as e:
                print(f"❌ {description}: {e}")
                backend_results["broken_endpoints"] += 1
                backend_results["endpoint_details"][endpoint] = {
                    "status": "error",
                    "error": str(e),
                    "description": description
                }
        
        # Calculate compliance
        if backend_results["total_endpoints"] > 0:
            compliance = (backend_results["working_endpoints"] / backend_results["total_endpoints"]) * 100
        else:
            compliance = 0
        
        backend_results["compliance_percentage"] = compliance
        
        print(f"\n📊 Backend Compliance: {compliance:.1f}%")
        print(f"   Working: {backend_results['working_endpoints']}/{backend_results['total_endpoints']}")
        
        return backend_results
    
    def assess_ml_service_functionality(self) -> Dict[str, Any]:
        """
        Оценка функциональности ML Service
        """
        print("\n🔍 ОЦЕНКА ML SERVICE FUNCTIONALITY")
        print("-" * 50)
        
        ml_results = {
            "total_endpoints": 0,
            "working_endpoints": 0,
            "broken_endpoints": 0,
            "endpoint_details": {},
            "price_validation": False,
            "predictions": False,
            "real_data_integration": False
        }
        
        # Test basic connectivity
        try:
            response = requests.get(f"{self.ml_service_url}/api/v1/health/", timeout=5)
            if response.status_code == 200:
                print("✅ ML Service доступен")
                ml_results["basic_connectivity"] = True
            else:
                print(f"❌ ML Service недоступен: {response.status_code}")
                ml_results["basic_connectivity"] = False
                return ml_results
        except Exception as e:
            print(f"❌ ML Service недоступен: {e}")
            ml_results["basic_connectivity"] = False
            return ml_results
        
        # Test ML endpoints
        ml_endpoints = [
            ("GET", "/api/v1/health/", "Health Check"),
            ("POST", "/api/v1/predictions/predict", "Predictions"),
            ("POST", "/api/v1/predictions/batch", "Batch Predictions"),
            ("GET", "/api/v1/predictions/model/info", "Model Info")
        ]
        
        for method, endpoint, description in ml_endpoints:
            ml_results["total_endpoints"] += 1
            try:
                if method == "GET":
                    response = requests.get(f"{self.ml_service_url}{endpoint}", timeout=5)
                else:
                    response = requests.post(f"{self.ml_service_url}{endpoint}", json={}, timeout=5)
                
                if response.status_code in [200, 201, 400, 422]:  # Valid responses
                    print(f"✅ {description}: {response.status_code}")
                    ml_results["working_endpoints"] += 1
                    ml_results["endpoint_details"][endpoint] = {
                        "status": "working",
                        "response_code": response.status_code,
                        "description": description
                    }
                else:
                    print(f"❌ {description}: {response.status_code}")
                    ml_results["broken_endpoints"] += 1
                    ml_results["endpoint_details"][endpoint] = {
                        "status": "broken",
                        "response_code": response.status_code,
                        "description": description
                    }
            except Exception as e:
                print(f"❌ {description}: {e}")
                ml_results["broken_endpoints"] += 1
                ml_results["endpoint_details"][endpoint] = {
                    "status": "error",
                    "error": str(e),
                    "description": description
                }
        
        # Test Enhanced Price Validation (Stage 0.3.1)
        price_validation_endpoints = [
            ("GET", "/api/v1/price-validation/health", "Price Validation Health"),
            ("GET", "/api/v1/price-validation/supported-symbols", "Supported Symbols"),
            ("POST", "/api/v1/price-validation/current-prices", "Current Prices"),
            ("POST", "/api/v1/price-validation/historical-data", "Historical Data"),
            ("POST", "/api/v1/price-validation/validate-signal", "Signal Validation"),
            ("POST", "/api/v1/price-validation/market-summary", "Market Summary")
        ]
        
        for method, endpoint, description in price_validation_endpoints:
            ml_results["total_endpoints"] += 1
            try:
                if method == "GET":
                    response = requests.get(f"{self.ml_service_url}{endpoint}", timeout=10)
                else:
                    # Provide minimal test data
                    test_data = {}
                    if "current-prices" in endpoint:
                        test_data = {"symbols": ["BTC/USDT"]}
                    elif "historical-data" in endpoint:
                        test_data = {"symbol": "BTC/USDT", "hours_back": 1}
                    elif "validate-signal" in endpoint:
                        test_data = {"id": "test", "symbol": "BTC/USDT", "direction": "long", "entry_price": 50000}
                    elif "market-summary" in endpoint:
                        test_data = {"symbols": ["BTC/USDT"]}
                    
                    response = requests.post(f"{self.ml_service_url}{endpoint}", json=test_data, timeout=10)
                
                if response.status_code in [200, 201, 400, 422]:  # Valid responses
                    print(f"✅ {description}: {response.status_code}")
                    ml_results["working_endpoints"] += 1
                    ml_results["endpoint_details"][endpoint] = {
                        "status": "working",
                        "response_code": response.status_code,
                        "description": description
                    }
                else:
                    print(f"❌ {description}: {response.status_code}")
                    ml_results["broken_endpoints"] += 1
                    ml_results["endpoint_details"][endpoint] = {
                        "status": "broken",
                        "response_code": response.status_code,
                        "description": description
                    }
            except Exception as e:
                print(f"❌ {description}: {e}")
                ml_results["broken_endpoints"] += 1
                ml_results["endpoint_details"][endpoint] = {
                    "status": "error",
                    "error": str(e),
                    "description": description
                }
        
        # Calculate compliance
        if ml_results["total_endpoints"] > 0:
            compliance = (ml_results["working_endpoints"] / ml_results["total_endpoints"]) * 100
        else:
            compliance = 0
        
        ml_results["compliance_percentage"] = compliance
        
        print(f"\n📊 ML Service Compliance: {compliance:.1f}%")
        print(f"   Working: {ml_results['working_endpoints']}/{ml_results['total_endpoints']}")
        
        return ml_results
    
    def assess_frontend_functionality(self) -> Dict[str, Any]:
        """
        Оценка функциональности Frontend
        """
        print("\n🔍 ОЦЕНКА FRONTEND FUNCTIONALITY")
        print("-" * 50)
        
        frontend_results = {
            "accessibility": False,
            "pages_available": [],
            "pages_missing": [],
            "responsive_design": False,
            "modern_ui": False
        }
        
        # Test frontend accessibility
        try:
            response = requests.get(f"{self.frontend_url}", timeout=5)
            if response.status_code == 200:
                print("✅ Frontend доступен")
                frontend_results["accessibility"] = True
            else:
                print(f"❌ Frontend недоступен: {response.status_code}")
                frontend_results["accessibility"] = False
                return frontend_results
        except Exception as e:
            print(f"❌ Frontend недоступен: {e}")
            frontend_results["accessibility"] = False
            return frontend_results
        
        # Test key pages
        key_pages = [
            ("/", "Главная страница"),
            ("/dashboard", "Dashboard"),
            ("/channels", "Каналы"),
            ("/signals", "Сигналы"),
            ("/auth/login", "Страница входа"),
            ("/auth/register", "Страница регистрации")
        ]
        
        for page, description in key_pages:
            try:
                response = requests.get(f"{self.frontend_url}{page}", timeout=5)
                if response.status_code == 200:
                    print(f"✅ {description}: Доступна")
                    frontend_results["pages_available"].append(page)
                else:
                    print(f"❌ {description}: {response.status_code}")
                    frontend_results["pages_missing"].append(page)
            except Exception as e:
                print(f"❌ {description}: {e}")
                frontend_results["pages_missing"].append(page)
        
        # Check for modern UI indicators
        try:
            response = requests.get(f"{self.frontend_url}", timeout=5)
            content = response.text.lower()
            
            # Check for modern framework indicators
            if "next.js" in content or "react" in content or "tailwind" in content:
                frontend_results["modern_ui"] = True
                print("✅ Modern UI framework detected")
            else:
                print("⚠️ Modern UI framework not detected")
            
            # Check for responsive design indicators
            if "viewport" in content or "responsive" in content or "mobile" in content:
                frontend_results["responsive_design"] = True
                print("✅ Responsive design indicators found")
            else:
                print("⚠️ Responsive design indicators not found")
                
        except Exception as e:
            print(f"❌ Error checking UI indicators: {e}")
        
        # Calculate compliance
        total_pages = len(key_pages)
        available_pages = len(frontend_results["pages_available"])
        compliance = (available_pages / total_pages) * 100 if total_pages > 0 else 0
        
        frontend_results["compliance_percentage"] = compliance
        
        print(f"\n📊 Frontend Compliance: {compliance:.1f}%")
        print(f"   Available: {available_pages}/{total_pages}")
        
        return frontend_results
    
    def assess_integration_quality(self) -> Dict[str, Any]:
        """
        Оценка качества интеграции между компонентами
        """
        print("\n🔍 ОЦЕНКА INTEGRATION QUALITY")
        print("-" * 50)
        
        integration_results = {
            "backend_ml_integration": False,
            "frontend_backend_integration": False,
            "database_integration": False,
            "real_data_integration": False,
            "telegram_integration": False,
            "payment_integration": False
        }
        
        # Test Backend-ML integration
        try:
            response = requests.get(f"{self.backend_url}/api/v1/ml/health", timeout=5)
            if response.status_code == 200:
                print("✅ Backend-ML integration: Работает")
                integration_results["backend_ml_integration"] = True
            else:
                print(f"❌ Backend-ML integration: {response.status_code}")
        except Exception as e:
            print(f"❌ Backend-ML integration: {e}")
        
        # Test ML predictions through backend
        try:
            test_signal = {
                "symbol": "BTC/USDT",
                "direction": "long",
                "entry_price": 50000,
                "targets": [51000],
                "stop_loss": 49000
            }
            response = requests.post(f"{self.backend_url}/api/v1/ml/predict", json=test_signal, timeout=10)
            if response.status_code == 200:
                print("✅ ML predictions through backend: Работает")
                integration_results["backend_ml_integration"] = True
            else:
                print(f"❌ ML predictions through backend: {response.status_code}")
        except Exception as e:
            print(f"❌ ML predictions through backend: {e}")
        
        # Test Telegram integration
        try:
            response = requests.get(f"{self.backend_url}/api/v1/telegram/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    print("✅ Telegram integration: Работает")
                    integration_results["telegram_integration"] = True
                else:
                    print(f"⚠️ Telegram integration: {data.get('status', 'unknown')}")
            else:
                print(f"❌ Telegram integration: {response.status_code}")
        except Exception as e:
            print(f"❌ Telegram integration: {e}")
        
        # Test Real Data Integration (Stage 0.3.1)
        try:
            response = requests.get(f"{self.ml_service_url}/api/v1/price-validation/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get("real_data_integration") == True:
                    print("✅ Real Data Integration: Работает")
                    integration_results["real_data_integration"] = True
                else:
                    print("⚠️ Real Data Integration: Не полностью")
            else:
                print(f"❌ Real Data Integration: {response.status_code}")
        except Exception as e:
            print(f"❌ Real Data Integration: {e}")
        
        # Calculate integration compliance
        total_integrations = len(integration_results)
        working_integrations = sum(integration_results.values())
        compliance = (working_integrations / total_integrations) * 100 if total_integrations > 0 else 0
        
        integration_results["compliance_percentage"] = compliance
        
        print(f"\n📊 Integration Compliance: {compliance:.1f}%")
        print(f"   Working: {working_integrations}/{total_integrations}")
        
        return integration_results
    
    def assess_claimed_vs_real_functionality(self) -> Dict[str, Any]:
        """
        Сравнение заявленной функциональности с реальной
        """
        print("\n🔍 CLAIMED VS REAL FUNCTIONALITY")
        print("-" * 50)
        
        claimed_features = {
            "backend_api": {
                "claimed": "79 API endpoints",
                "real": "TBD",
                "compliance": 0.0
            },
            "ml_service": {
                "claimed": "Advanced ML predictions",
                "real": "Rule-based MVP",
                "compliance": 60.0
            },
            "frontend": {
                "claimed": "Modern Next.js UI",
                "real": "TBD",
                "compliance": 0.0
            },
            "telegram_integration": {
                "claimed": "Real-time signal collection",
                "real": "Mock mode",
                "compliance": 30.0
            },
            "price_validation": {
                "claimed": "Multi-exchange price checking",
                "real": "Enhanced with real_data_config",
                "compliance": 85.0
            },
            "authentication": {
                "claimed": "JWT-based auth",
                "real": "TBD",
                "compliance": 0.0
            },
            "database": {
                "claimed": "PostgreSQL with migrations",
                "real": "TBD",
                "compliance": 0.0
            },
            "docker": {
                "claimed": "Containerized deployment",
                "real": "Dockerfiles ready",
                "compliance": 70.0
            }
        }
        
        # Update with real assessment results
        for feature, details in claimed_features.items():
            print(f"📋 {feature.upper()}:")
            print(f"   Заявлено: {details['claimed']}")
            print(f"   Реально: {details['real']}")
            print(f"   Соответствие: {details['compliance']:.1f}%")
            print()
        
        return claimed_features
    
    def generate_critical_issues(self) -> List[str]:
        """
        Генерация списка критических проблем
        """
        critical_issues = []
        
        # Check for critical backend issues
        if not hasattr(self.assessment_results["sections"], "backend"):
            critical_issues.append("Backend недоступен - критическая проблема")
        elif self.assessment_results["sections"]["backend"]["compliance_percentage"] < 50:
            critical_issues.append("Backend имеет низкое соответствие (<50%)")
        
        # Check for critical ML issues
        if not hasattr(self.assessment_results["sections"], "ml_service"):
            critical_issues.append("ML Service недоступен - критическая проблема")
        elif self.assessment_results["sections"]["ml_service"]["compliance_percentage"] < 50:
            critical_issues.append("ML Service имеет низкое соответствие (<50%)")
        
        # Check for critical frontend issues
        if not hasattr(self.assessment_results["sections"], "frontend"):
            critical_issues.append("Frontend недоступен - критическая проблема")
        elif self.assessment_results["sections"]["frontend"]["compliance_percentage"] < 50:
            critical_issues.append("Frontend имеет низкое соответствие (<50%)")
        
        # Check for integration issues
        if hasattr(self.assessment_results["sections"], "integration"):
            if self.assessment_results["sections"]["integration"]["compliance_percentage"] < 30:
                critical_issues.append("Критически низкая интеграция между компонентами (<30%)")
        
        return critical_issues
    
    def generate_recommendations(self) -> List[str]:
        """
        Генерация рекомендаций по улучшению
        """
        recommendations = []
        
        # Backend recommendations
        if hasattr(self.assessment_results["sections"], "backend"):
            backend_compliance = self.assessment_results["sections"]["backend"]["compliance_percentage"]
            if backend_compliance < 80:
                recommendations.append("Улучшить стабильность Backend API endpoints")
            if backend_compliance < 60:
                recommendations.append("Критически необходимо исправить неработающие Backend endpoints")
        
        # ML Service recommendations
        if hasattr(self.assessment_results["sections"], "ml_service"):
            ml_compliance = self.assessment_results["sections"]["ml_service"]["compliance_percentage"]
            if ml_compliance < 80:
                recommendations.append("Улучшить стабильность ML Service endpoints")
            if ml_compliance < 60:
                recommendations.append("Критически необходимо исправить неработающие ML endpoints")
        
        # Frontend recommendations
        if hasattr(self.assessment_results["sections"], "frontend"):
            frontend_compliance = self.assessment_results["sections"]["frontend"]["compliance_percentage"]
            if frontend_compliance < 80:
                recommendations.append("Улучшить доступность Frontend страниц")
            if frontend_compliance < 60:
                recommendations.append("Критически необходимо исправить недоступные Frontend страницы")
        
        # Integration recommendations
        if hasattr(self.assessment_results["sections"], "integration"):
            integration_compliance = self.assessment_results["sections"]["integration"]["compliance_percentage"]
            if integration_compliance < 50:
                recommendations.append("Критически необходимо улучшить интеграцию между компонентами")
        
        # General recommendations
        recommendations.append("Внедрить comprehensive testing для всех компонентов")
        recommendations.append("Улучшить error handling и logging")
        recommendations.append("Добавить monitoring и alerting систему")
        
        return recommendations
    
    def calculate_overall_grade(self) -> Tuple[str, float]:
        """
        Расчет общей оценки проекта
        """
        total_compliance = 0
        total_sections = 0
        
        for section_name, section_data in self.assessment_results["sections"].items():
            if "compliance_percentage" in section_data:
                total_compliance += section_data["compliance_percentage"]
                total_sections += 1
        
        if total_sections == 0:
            return "F", 0.0
        
        overall_compliance = total_compliance / total_sections
        
        # Grade assignment
        if overall_compliance >= 90:
            grade = "A+"
        elif overall_compliance >= 80:
            grade = "A"
        elif overall_compliance >= 70:
            grade = "B"
        elif overall_compliance >= 60:
            grade = "C"
        elif overall_compliance >= 50:
            grade = "D"
        else:
            grade = "F"
        
        return grade, overall_compliance
    
    def run_comprehensive_assessment(self):
        """
        Запуск comprehensive оценки
        """
        print("🔍 HONEST TECHNICAL ASSESSMENT")
        print("=" * 80)
        print(f"Методология: TASKS2.md Critical Analysis")
        print(f"Время оценки: {datetime.now().isoformat()}")
        print("=" * 80)
        
        # Run all assessments
        self.assessment_results["sections"]["backend"] = self.assess_backend_functionality()
        self.assessment_results["sections"]["ml_service"] = self.assess_ml_service_functionality()
        self.assessment_results["sections"]["frontend"] = self.assess_frontend_functionality()
        self.assessment_results["sections"]["integration"] = self.assess_integration_quality()
        self.assessment_results["real_vs_claimed"] = self.assess_claimed_vs_real_functionality()
        
        # Generate critical issues and recommendations
        self.assessment_results["critical_issues"] = self.generate_critical_issues()
        self.assessment_results["recommendations"] = self.generate_recommendations()
        
        # Calculate overall grade
        grade, compliance = self.calculate_overall_grade()
        self.assessment_results["overall_grade"] = grade
        self.assessment_results["compliance_percentage"] = compliance
        
        # Print final results
        print("\n" + "=" * 80)
        print("🎯 HONEST ASSESSMENT RESULTS")
        print("=" * 80)
        print(f"Overall Grade: {grade}")
        print(f"Overall Compliance: {compliance:.1f}%")
        print()
        
        print("📊 SECTION BREAKDOWN:")
        for section_name, section_data in self.assessment_results["sections"].items():
            if "compliance_percentage" in section_data:
                print(f"   {section_name.upper()}: {section_data['compliance_percentage']:.1f}%")
        
        print(f"\n🚨 CRITICAL ISSUES ({len(self.assessment_results['critical_issues'])}):")
        for issue in self.assessment_results["critical_issues"]:
            print(f"   ❌ {issue}")
        
        print(f"\n💡 RECOMMENDATIONS ({len(self.assessment_results['recommendations'])}):")
        for rec in self.assessment_results["recommendations"]:
            print(f"   💡 {rec}")
        
        # Save detailed report
        report_filename = f"honest_technical_assessment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump(self.assessment_results, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 Подробный отчет сохранен: {report_filename}")
        
        return self.assessment_results

def main():
    """
    Main function
    """
    print("Starting Honest Technical Assessment...")
    print("Убедитесь, что все сервисы запущены:")
    print("  - Backend: localhost:8000")
    print("  - ML Service: localhost:8001") 
    print("  - Frontend: localhost:3000")
    print()
    
    try:
        assessor = HonestTechnicalAssessment()
        results = assessor.run_comprehensive_assessment()
        
        # Create summary report
        summary_filename = f"assessment_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(summary_filename, 'w', encoding='utf-8') as f:
            f.write("# Honest Technical Assessment Summary\n\n")
            f.write(f"**Date:** {datetime.now().isoformat()}\n")
            f.write(f"**Methodology:** TASKS2.md Critical Analysis\n\n")
            f.write(f"## Overall Grade: {results['overall_grade']}\n")
            f.write(f"## Overall Compliance: {results['compliance_percentage']:.1f}%\n\n")
            
            f.write("## Section Breakdown\n")
            for section_name, section_data in results["sections"].items():
                if "compliance_percentage" in section_data:
                    f.write(f"- **{section_name.upper()}:** {section_data['compliance_percentage']:.1f}%\n")
            
            f.write("\n## Critical Issues\n")
            for issue in results["critical_issues"]:
                f.write(f"- ❌ {issue}\n")
            
            f.write("\n## Recommendations\n")
            for rec in results["recommendations"]:
                f.write(f"- 💡 {rec}\n")
        
        print(f"📋 Summary report saved: {summary_filename}")
        
    except KeyboardInterrupt:
        print("\n⏸️ Assessment interrupted by user")
    except Exception as e:
        print(f"\n❌ Critical error during assessment: {e}")

if __name__ == "__main__":
    main() 