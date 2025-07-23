"""
Risk scoring and portfolio optimization module
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class RiskMetrics:
    """Risk metrics for a signal or portfolio"""
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    var_95: float  # Value at Risk 95%
    expected_return: float
    risk_score: float  # 0-100 scale
    confidence_interval: Tuple[float, float]

class RiskScoringEngine:
    """Engine for calculating risk scores and portfolio optimization"""
    
    def __init__(self):
        self.risk_free_rate = 0.02  # 2% annual risk-free rate
        self.confidence_level = 0.95
        
    def calculate_volatility(self, returns: np.ndarray, window: int = 30) -> float:
        """Calculate rolling volatility"""
        if len(returns) < window:
            return np.std(returns) * np.sqrt(252)  # Annualized
        
        rolling_vol = pd.Series(returns).rolling(window=window).std()
        return float(rolling_vol.iloc[-1] * np.sqrt(252))
    
    def calculate_sharpe_ratio(self, returns: np.ndarray) -> float:
        """Calculate Sharpe ratio"""
        if len(returns) == 0:
            return 0.0
        
        excess_returns = returns - self.risk_free_rate / 252  # Daily risk-free rate
        if np.std(excess_returns) == 0:
            return 0.0
        
        return float(np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252))
    
    def calculate_max_drawdown(self, prices: np.ndarray) -> float:
        """Calculate maximum drawdown"""
        if len(prices) < 2:
            return 0.0
        
        peak = prices[0]
        max_dd = 0.0
        
        for price in prices:
            if price > peak:
                peak = price
            dd = (peak - price) / peak
            max_dd = max(max_dd, dd)
        
        return float(max_dd)
    
    def calculate_var(self, returns: np.ndarray, confidence: float = 0.95) -> float:
        """Calculate Value at Risk"""
        if len(returns) == 0:
            return 0.0
        
        return float(np.percentile(returns, (1 - confidence) * 100))
    
    def calculate_expected_return(self, returns: np.ndarray) -> float:
        """Calculate expected return"""
        if len(returns) == 0:
            return 0.0
        
        return float(np.mean(returns) * 252)  # Annualized
    
    def calculate_risk_score(self, metrics: RiskMetrics) -> float:
        """Calculate overall risk score (0-100, lower is better)"""
        # Normalize metrics to 0-100 scale
        vol_score = min(metrics.volatility * 100, 100)  # Volatility penalty
        sharpe_score = max(0, 100 - metrics.sharpe_ratio * 20)  # Sharpe penalty
        dd_score = metrics.max_drawdown * 100  # Drawdown penalty
        var_score = abs(metrics.var_95) * 100  # VaR penalty
        
        # Weighted average
        risk_score = (
            0.3 * vol_score +
            0.25 * sharpe_score +
            0.25 * dd_score +
            0.2 * var_score
        )
        
        return float(np.clip(risk_score, 0, 100))
    
    def analyze_signal_risk(self, signal_data: Dict[str, Any]) -> RiskMetrics:
        """Analyze risk for a single signal"""
        # Extract price history and returns
        prices = np.array(signal_data.get('price_history', []))
        if len(prices) < 2:
            # Mock data if not available
            prices = np.array([100, 102, 98, 105, 103, 107, 104, 108])
        
        # Calculate returns
        returns = np.diff(prices) / prices[:-1]
        
        # Calculate metrics
        volatility = self.calculate_volatility(returns)
        sharpe_ratio = self.calculate_sharpe_ratio(returns)
        max_drawdown = self.calculate_max_drawdown(prices)
        var_95 = self.calculate_var(returns, self.confidence_level)
        expected_return = self.calculate_expected_return(returns)
        
        # Calculate confidence interval
        std_error = np.std(returns) / np.sqrt(len(returns))
        confidence_interval = (
            expected_return - 1.96 * std_error,
            expected_return + 1.96 * std_error
        )
        
        # Create metrics object
        metrics = RiskMetrics(
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            var_95=var_95,
            expected_return=expected_return,
            risk_score=0.0,  # Will be calculated below
            confidence_interval=confidence_interval
        )
        
        # Calculate overall risk score
        metrics.risk_score = self.calculate_risk_score(metrics)
        
        return metrics
    
    def optimize_portfolio(self, signals: List[Dict[str, Any]], 
                          max_risk: float = 50.0) -> Dict[str, Any]:
        """Optimize portfolio allocation based on risk constraints"""
        if not signals:
            return {"error": "No signals provided"}
        
        # Analyze risk for each signal
        signal_risks = []
        for signal in signals:
            risk_metrics = self.analyze_signal_risk(signal)
            signal_risks.append({
                'signal_id': signal.get('id', 'unknown'),
                'risk_metrics': risk_metrics,
                'expected_return': risk_metrics.expected_return,
                'risk_score': risk_metrics.risk_score
            })
        
        # Sort by risk-adjusted return (Sharpe ratio)
        signal_risks.sort(key=lambda x: x['risk_metrics'].sharpe_ratio, reverse=True)
        
        # Simple allocation strategy: allocate more to lower risk signals
        total_allocation = 0.0
        allocations = []
        
        for i, signal_risk in enumerate(signal_risks):
            # Weight decreases with risk score
            weight = max(0.1, 1.0 - signal_risk['risk_score'] / 100)
            weight = weight / (i + 1)  # Further reduce weight for lower ranked signals
            
            allocation = min(weight, 0.3)  # Max 30% per signal
            allocations.append({
                'signal_id': signal_risk['signal_id'],
                'allocation': allocation,
                'risk_score': signal_risk['risk_score'],
                'expected_return': signal_risk['expected_return']
            })
            total_allocation += allocation
        
        # Normalize allocations
        if total_allocation > 0:
            for allocation in allocations:
                allocation['allocation'] /= total_allocation
        
        # Calculate portfolio metrics
        portfolio_return = sum(
            a['allocation'] * a['expected_return'] for a in allocations
        )
        portfolio_risk = sum(
            a['allocation'] * a['risk_score'] for a in allocations
        )
        
        return {
            'allocations': allocations,
            'portfolio_metrics': {
                'expected_return': portfolio_return,
                'risk_score': portfolio_risk,
                'diversification_score': 1.0 - portfolio_risk / 100
            },
            'risk_constraint_met': portfolio_risk <= max_risk
        }
    
    def calculate_position_size(self, signal_data: Dict[str, Any], 
                               account_balance: float,
                               max_risk_per_trade: float = 0.02) -> Dict[str, Any]:
        """Calculate optimal position size based on risk management"""
        risk_metrics = self.analyze_signal_risk(signal_data)
        
        # Kelly Criterion for position sizing
        win_rate = signal_data.get('success_rate', 0.6)
        avg_win = signal_data.get('avg_win', 0.05)
        avg_loss = signal_data.get('avg_loss', 0.03)
        
        if avg_loss > 0:
            kelly_fraction = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_win
            kelly_fraction = max(0, min(kelly_fraction, 0.25))  # Cap at 25%
        else:
            kelly_fraction = 0.1  # Default 10%
        
        # Adjust for risk score
        risk_adjustment = 1.0 - risk_metrics.risk_score / 100
        position_size = kelly_fraction * risk_adjustment * account_balance
        
        # Apply maximum risk per trade constraint
        max_position = account_balance * max_risk_per_trade
        position_size = min(position_size, max_position)
        
        return {
            'position_size': position_size,
            'position_percentage': position_size / account_balance,
            'kelly_fraction': kelly_fraction,
            'risk_adjustment': risk_adjustment,
            'risk_metrics': risk_metrics
        }
    
    def generate_risk_report(self, signals: List[Dict[str, Any]]) -> str:
        """Generate comprehensive risk report"""
        if not signals:
            return "No signals to analyze"
        
        # Analyze all signals
        risk_analyses = []
        for signal in signals:
            risk_metrics = self.analyze_signal_risk(signal)
            risk_analyses.append({
                'signal_id': signal.get('id', 'unknown'),
                'metrics': risk_metrics
            })
        
        # Portfolio optimization
        portfolio = self.optimize_portfolio(signals)
        
        # Generate report
        report = f"""
# Risk Analysis Report
Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}

## Signal Risk Analysis
"""
        
        for analysis in risk_analyses:
            metrics = analysis['metrics']
            report += f"""
### Signal {analysis['signal_id']}
- Risk Score: {metrics.risk_score:.1f}/100
- Expected Return: {metrics.expected_return:.2%}
- Volatility: {metrics.volatility:.2%}
- Sharpe Ratio: {metrics.sharpe_ratio:.2f}
- Max Drawdown: {metrics.max_drawdown:.2%}
- VaR (95%): {metrics.var_95:.2%}
"""
        
        # Portfolio summary
        if 'portfolio_metrics' in portfolio:
            pm = portfolio['portfolio_metrics']
            report += f"""
## Portfolio Summary
- Expected Return: {pm['expected_return']:.2%}
- Portfolio Risk Score: {pm['risk_score']:.1f}/100
- Diversification Score: {pm['diversification_score']:.2f}
- Risk Constraint Met: {'✅' if portfolio['risk_constraint_met'] else '❌'}
"""
        
        return report


def main():
    """Test risk scoring functionality"""
    engine = RiskScoringEngine()
    
    # Mock signal data
    mock_signals = [
        {
            'id': 'signal_1',
            'price_history': [100, 102, 98, 105, 103, 107, 104, 108],
            'success_rate': 0.7,
            'avg_win': 0.05,
            'avg_loss': 0.03
        },
        {
            'id': 'signal_2', 
            'price_history': [100, 98, 95, 97, 99, 101, 103, 105],
            'success_rate': 0.6,
            'avg_win': 0.04,
            'avg_loss': 0.02
        }
    ]
    
    # Test risk analysis
    for signal in mock_signals:
        risk_metrics = engine.analyze_signal_risk(signal)
        print(f"Signal {signal['id']} - Risk Score: {risk_metrics.risk_score:.1f}")
    
    # Test portfolio optimization
    portfolio = engine.optimize_portfolio(mock_signals)
    print(f"Portfolio Risk Score: {portfolio['portfolio_metrics']['risk_score']:.1f}")
    
    # Generate report
    report = engine.generate_risk_report(mock_signals)
    print("Risk report generated successfully")


if __name__ == "__main__":
    main() 