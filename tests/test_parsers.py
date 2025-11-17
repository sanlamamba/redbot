"""Tests for parser modules."""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from parsers.salary import SalaryParser


class TestSalaryParser:
    """Tests for SalaryParser."""

    def setup_method(self):
        """Setup test fixtures."""
        self.parser = SalaryParser()

    def test_range_with_k(self):
        """Test salary range with 'k' notation."""
        result = self.parser.parse("Salary: $50k-$70k per year")
        assert result is not None
        assert result.min == 50000
        assert result.max == 70000
        assert result.currency == "USD"
        assert result.period == "yearly"

    def test_range_with_commas(self):
        """Test salary range with comma separators."""
        result = self.parser.parse("Compensation: $80,000-$100,000")
        assert result is not None
        assert result.min == 80000
        assert result.max == 100000

    def test_single_value(self):
        """Test single salary value."""
        result = self.parser.parse("Offering $90k")
        assert result is not None
        assert result.min == 90000
        assert result.max == 90000

    def test_hourly_rate(self):
        """Test hourly rate conversion to annual."""
        result = self.parser.parse("$40/hour position")
        assert result is not None
        # $40/hr * 40hrs/week * 52weeks = $83,200
        assert result.min == 40 * 40 * 52
        assert result.period == "yearly"

    def test_monthly_rate(self):
        """Test monthly rate conversion to annual."""
        result = self.parser.parse("€5000/month")
        assert result is not None
        assert result.min == 5000 * 12
        assert result.currency == "EUR"

    def test_euro_currency(self):
        """Test Euro currency detection."""
        result = self.parser.parse("€60-80k annual salary")
        assert result is not None
        assert result.currency == "EUR"
        assert result.min == 60000
        assert result.max == 80000

    def test_gbp_currency(self):
        """Test GBP currency detection."""
        result = self.parser.parse("£50k-£70k")
        assert result is not None
        assert result.currency == "GBP"

    def test_currency_code(self):
        """Test currency code detection."""
        result = self.parser.parse("50-70k USD per year")
        assert result is not None
        assert result.currency == "USD"
        assert result.min == 50000

    def test_up_to(self):
        """Test 'up to' pattern."""
        result = self.parser.parse("Up to $100k")
        assert result is not None
        assert result.max == 100000
        assert result.min is None or result.min == result.max

    def test_starting_at(self):
        """Test 'starting at' pattern."""
        result = self.parser.parse("Starting at $80k")
        assert result is not None
        assert result.min == 80000

    def test_no_salary(self):
        """Test text without salary."""
        result = self.parser.parse("Great opportunity for developers")
        assert result is None

    def test_invalid_salary(self):
        """Test invalid salary amounts."""
        # Too high (10 million)
        result = self.parser.parse("$10,000k")
        assert result is None

        # Edge case: very low hourly becomes valid when annualized
        # $5/hr * 40 * 52 = $10,400 (just above minimum)
        # This is actually valid, so we won't test it as invalid

    def test_format_salary(self):
        """Test salary formatting."""
        result = self.parser.parse("$50k-$70k")
        formatted = self.parser.format_salary(result)
        assert "50,000" in formatted and "70,000" in formatted

    def test_real_world_example_1(self):
        """Test real job posting example."""
        text = """
        Senior Python Developer - Remote

        We're looking for an experienced Python developer.
        Salary range: $120,000-$150,000 per year
        """
        result = self.parser.parse(text)
        assert result is not None
        assert result.min == 120000
        assert result.max == 150000

    def test_real_world_example_2(self):
        """Test real job posting with hourly rate."""
        text = "Contract position, $65/hr, remote work"
        result = self.parser.parse(text)
        assert result is not None
        # Should be normalized to annual
        assert result.period == "yearly"
        assert result.min > 100000  # ~$135k annually

    def test_real_world_example_3(self):
        """Test European posting."""
        text = "Frontend Engineer position in Berlin. €50-65k"
        result = self.parser.parse(text)
        assert result is not None
        assert result.currency == "EUR"
        assert result.min == 50000
        assert result.max == 65000


def run_tests():
    """Run all tests manually (without pytest)."""
    import traceback

    test_class = TestSalaryParser()
    test_methods = [m for m in dir(test_class) if m.startswith('test_')]

    passed = 0
    failed = 0

    for method_name in test_methods:
        test_class.setup_method()
        try:
            method = getattr(test_class, method_name)
            method()
            print(f"✓ {method_name}")
            passed += 1
        except AssertionError as e:
            print(f"✗ {method_name}: {str(e)}")
            traceback.print_exc()
            failed += 1
        except Exception as e:
            print(f"✗ {method_name}: {str(e)}")
            traceback.print_exc()
            failed += 1

    print(f"\n{passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
