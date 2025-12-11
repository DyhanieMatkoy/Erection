"""Calculator service"""


class CalculatorService:
    @staticmethod
    def calculate_sum(quantity: float, price: float) -> float:
        """Calculate sum"""
        return quantity * price
    
    @staticmethod
    def calculate_labor(quantity: float, labor_rate: float) -> float:
        """Calculate labor"""
        return quantity * labor_rate
    
    @staticmethod
    def calculate_deviation(planned: float, actual: float) -> float:
        """Calculate deviation percentage"""
        if planned == 0.0:
            return 0.0
        return ((actual - planned) / planned) * 100.0
