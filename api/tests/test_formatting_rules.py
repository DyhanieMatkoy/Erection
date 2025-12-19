import pytest
from hypothesis import given, strategies as st
from api.services.rule_engine import RuleEngine

class TestFormattingRules:
    """
    Task 11.4: Property test for conditional formatting.
    Validates: Requirements 6.3
    """
    
    @given(
        data=st.fixed_dictionaries({'status': st.sampled_from(['Draft', 'Active', 'Closed']), 'amount': st.integers()}),
        rules=st.lists(st.fixed_dictionaries({
            'condition': st.fixed_dictionaries({
                'field': st.sampled_from(['status', 'amount']),
                'operator': st.sampled_from(['eq', 'gt']),
                'value': st.one_of(st.text(), st.integers())
            }),
            'style': st.fixed_dictionaries({'color': st.sampled_from(['red', 'green'])}),
            'priority': st.integers(min_value=0, max_value=100)
        }))
    )
    def test_rule_application(self, data, rules):
        """
        Property 9: Conditional Formatting Application.
        Verify that rules are applied and priorities respected.
        """
        # We need to manually verify what should happen to check correctness
        # But for property test, we can check basic properties:
        # 1. Output is a dict
        # 2. If no rules match, output is empty (unless default?)
        
        style = RuleEngine.apply_rules(data, rules)
        
        # Check priority logic manually for a simple case
        # Filter matching rules
        matching = []
        for r in rules:
            if RuleEngine.evaluate_condition(data, r['condition']):
                matching.append(r)
        
        if not matching:
            assert style == {}
        else:
            # Find effective rule (Last one applied in ASC priority order)
            # Implementation sorts by priority ASC. 
            # If priorities equal, original order preserved.
            # Last applied wins.
            
            def get_prio(r):
                return r.get('priority', 0)
                
            matching.sort(key=get_prio) # Sort ASC
            expected_color = matching[-1]['style']['color']
            assert style['color'] == expected_color

    def test_operators(self):
        """Unit test for operators"""
        data = {'val': 10}
        assert RuleEngine.evaluate_condition(data, {'field': 'val', 'operator': 'eq', 'value': 10})
        assert RuleEngine.evaluate_condition(data, {'field': 'val', 'operator': 'gt', 'value': 5})
        assert not RuleEngine.evaluate_condition(data, {'field': 'val', 'operator': 'lt', 'value': 5})
