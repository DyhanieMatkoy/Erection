from typing import Dict, Any

class RuleEngine:
    """
    Evaluates conditional formatting rules.
    """
    
    @staticmethod
    def evaluate_condition(data: Dict[str, Any], condition: Dict[str, Any]) -> bool:
        """
        Evaluate if data matches condition.
        Condition format: {"field": "status", "operator": "eq", "value": "Draft"}
        Supported operators: eq, neq, gt, lt, gte, lte, contains, in
        """
        field = condition.get('field')
        operator = condition.get('operator', 'eq')
        target_value = condition.get('value')
        
        if not field:
            return False
            
        # Get value from data (support nested?)
        # Simple for now
        actual_value = data.get(field)
        
        # Handle types?
        # Assuming compatible types or string comparison
        
        try:
            if operator == 'eq':
                return actual_value == target_value
            elif operator == 'neq':
                return actual_value != target_value
            elif operator == 'gt':
                return actual_value > target_value
            elif operator == 'lt':
                return actual_value < target_value
            elif operator == 'gte':
                return actual_value >= target_value
            elif operator == 'lte':
                return actual_value <= target_value
            elif operator == 'contains':
                return str(target_value) in str(actual_value)
            elif operator == 'in':
                return actual_value in target_value
        except Exception:
            return False
            
        return False

    @staticmethod
    def apply_rules(data: Dict[str, Any], rules: list) -> Dict[str, Any]:
        """
        Apply list of rules to data.
        Returns merged style dictionary.
        Rules should be sorted by priority (descending) if later rules override earlier,
        BUT usually high priority wins.
        If we process in order, we should start from lowest or merge carefully.
        Better: Iterate rules. If match, merge style.
        If we want High Priority to win, we should apply Low Priority first?
        Or apply High Priority and don't overwrite?
        Let's assume rules are sorted by Priority DESC.
        We apply them. If multiple match, we merge.
        Wait, if Priority 10 says color=Red, and Priority 5 says color=Blue.
        Red should win.
        So we should apply Priority 5 first, then 10?
        Or apply 10, then 5 only if key not present?
        Let's assume "Cascading": Higher priority overrides.
        So apply in ASC order of priority?
        `order_by(priority.desc())` gives high priority first.
        If I iterate high -> low:
        Style = {}
        Rule 10 (Red): matches -> Style{color: Red}
        Rule 5 (Blue): matches -> Style{color: Blue} -> Overwrites Red? NO.
        So iterate Low -> High (ASC).
        
        Let's sort by priority ASC.
        """
        # Helper to get priority
        def get_prio(r):
            if isinstance(r, dict):
                return r.get('priority', 0)
            return getattr(r, 'priority', 0)

        # Sort rules by priority ASC
        sorted_rules = sorted(rules, key=get_prio)
        
        final_style = {}
        for rule in sorted_rules:
            # Rule object or dict?
            condition = rule.condition if hasattr(rule, 'condition') else rule.get('condition')
            style = rule.style if hasattr(rule, 'style') else rule.get('style')
            
            if RuleEngine.evaluate_condition(data, condition):
                final_style.update(style)
                
        return final_style
