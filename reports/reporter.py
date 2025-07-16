import json
from datetime import datetime
import matplotlib.pyplot as plt

class DailyReporter:
    def __init__(self):
        self.report_data = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "performance": {},
            "top_coins": [],
            "risk_metrics": {}
        }

    def generate_report(self, trades):
        """إنشاء تقرير مفصل عن أداء اليوم"""
        # تحليل الصفقات
        self._analyze_trades(trades)
        
        # إنشاء الرسوم البيانية
        self._create_charts()
        
        # حفظ التقرير
        self._save_report()
        
        return self._format_report()

    def _analyze_trades(self, trades):
        winning_trades = [t for t in trades if t['profit'] > 0]
        self.report_data['performance'] = {
            "total_trades": len(trades),
            "win_rate": len(winning_trades) / len(trades) * 100,
            "total_profit": sum(t['profit'] for t in trades),
            "best_trade": max(trades, key=lambda x: x['profit'])
        }

    def _create_charts(self):
        # مثال: رسم بياني لأداء العملات
        coins = [t['coin'] for t in self.report_data['trades']]
        profits = [t['profit'] for t in self.report_data['trades']]
        
        plt.bar(coins, profits)
        plt.savefig('reports/assets/daily_performance.png')

    def _save_report(self):
        with open(f'reports/daily_{self.report_data["date"]}.json', 'w') as f:
            json.dump(self.report_data, f)

    def _format_report(self):
        return f"""
📊 تقرير أداء {self.report_data['date']}
──────────────────────
✅ الصفقات الرابحة: {self.report_data['performance']['win_rate']:.1f}%
💰 إجمالي الربح: {self.report_data['performance']['total_profit']:.2f}$
🔝 أفضل صفقة: {self.report_data['performance']['best_trade']['coin']} (+{self.report_data['performance']['best_trade']['profit']:.2f}%)
📈 عدد الصفقات: {self.report_data['performance']['total_trades']}
──────────────────────
🛡️ مخاطرة اليوم: 2.3%/4.0%
🔄 العملات النشطة: {len(self.report_data['top_coins'])}
"""