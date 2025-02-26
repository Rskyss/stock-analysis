import unittest
from stock_analyzer.main import StockAnalyzer

class TestStockAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = StockAnalyzer()
        self.test_symbol = 'AAPL'
    
    def test_analyze_stock(self):
        result = self.analyzer.analyze_stock(self.test_symbol)
        self.assertIsNotNone(result)
        
    def test_invalid_symbol(self):
        result = self.analyzer.analyze_stock('INVALID')
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main() 