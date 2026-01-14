#!/usr/bin/env python3
"""
Simple Python Calculator

A fully functional calculator that supports:
- Multiple operations in a single session
- Session state management
- Batch operations
- Comprehensive error handling
- Input validation

Author: Calculator Team
Version: 1.0.0
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class Operation(Enum):
    """Valid calculator operations"""
    ADD = '+'
    SUBTRACT = '-'
    MULTIPLY = '*'
    DIVIDE = '/'


@dataclass
class CalculatorState:
    """Represents the current state of the calculator"""
    current_value: float = 0
    previous_value: float = 0
    operation: Optional[Operation] = None
    should_reset_display: bool = False
    history: List[str] = None

    def __post_init__(self):
        if self.history is None:
            self.history = []


class Calculator:
    """
    A simple calculator supporting basic arithmetic operations.

    Features:
    - Single operation at a time
    - Multiple calculations per session
    - Full operation typing (no shortcuts)
    - Simple error handling
    - Operation history tracking
    """

    MAX_HISTORY_SIZE = 50
    MAX_DISPLAY_LENGTH = 15

    def __init__(self):
        """Initialize the calculator with default state"""
        self.current_value: float = 0
        self.previous_value: float = 0
        self.operation: Optional[Operation] = None
        self.should_reset_display: bool = False
        self.history: List[str] = []

        self._validate_state()

    def _validate_state(self) -> None:
        """
        Validate the current state of the calculator.

        Raises:
            ValueError: If state is invalid
        """
        if not isinstance(self.current_value, (int, float)):
            raise ValueError("Invalid calculator state: current_value must be numeric")
        if not isinstance(self.previous_value, (int, float)):
            raise ValueError("Invalid calculator state: previous_value must be numeric")

    def input_number(self, num: Any) -> float:
        """
        Add a number to the current display value.

        Args:
            num: The number to add (int, float, or string representation)

        Returns:
            float: The updated current value

        Raises:
            ValueError: If input is invalid
        """
        try:
            # Parse and validate input
            number = self._parse_input(num)

            # Reset display if needed (after an operation)
            if self.should_reset_display:
                self.current_value = number
                self.should_reset_display = False
            else:
                # Append digit to current value
                current_str = str(self.current_value)
                if '.' in current_str and str(number) == '.':
                    raise ValueError("Decimal point already present")

                self.current_value = float(current_str + str(number))

            # Prevent excessively long numbers
            if len(str(abs(self.current_value))) > self.MAX_DISPLAY_LENGTH:
                raise ValueError("Number too large to display")

            return self.current_value

        except ValueError as error:
            self._handle_error(error)

    def input_decimal(self) -> float:
        """
        Add a decimal point to current value.

        Returns:
            float: The updated current value

        Raises:
            ValueError: If decimal already exists
        """
        try:
            current_str = str(self.current_value)

            if '.' in current_str:
                raise ValueError("Decimal point already present")

            if self.should_reset_display:
                self.current_value = 0.0
                self.should_reset_display = False
            else:
                self.current_value = float(current_str + '.')

            return self.current_value

        except ValueError as error:
            self._handle_error(error)

    def set_operation(self, op: str) -> float:
        """
        Set the operation and store current value.

        Args:
            op: The operation (+, -, *, /)

        Returns:
            float: The previous value

        Raises:
            ValueError: If operation is invalid
        """
        try:
            # Validate and convert operation string to enum
            try:
                operation = Operation(op)
            except ValueError:
                valid_ops = [o.value for o in Operation]
                raise ValueError(
                    f"Invalid operation: {op}. Valid operations are: {', '.join(valid_ops)}"
                )

            # If there's a pending operation, calculate it first
            if self.operation is not None and not self.should_reset_display:
                self.calculate()

            self.previous_value = self.current_value
            self.operation = operation
            self.should_reset_display = True

            return self.previous_value

        except ValueError as error:
            self._handle_error(error)

    def calculate(self) -> float:
        """
        Perform the pending calculation.

        Returns:
            float: The result of the calculation

        Raises:
            ValueError: If operation is invalid or division by zero
        """
        try:
            # No operation to perform
            if self.operation is None:
                return self.current_value

            # Perform the calculation
            if self.operation == Operation.ADD:
                result = self.previous_value + self.current_value
            elif self.operation == Operation.SUBTRACT:
                result = self.previous_value - self.current_value
            elif self.operation == Operation.MULTIPLY:
                result = self.previous_value * self.current_value
            elif self.operation == Operation.DIVIDE:
                if self.current_value == 0:
                    raise ValueError("Division by zero is not allowed")
                result = self.previous_value / self.current_value
            else:
                raise ValueError(f"Unknown operation: {self.operation}")

            # Log operation to history
            self._add_to_history(
                f"{self.previous_value} {self.operation.value} {self.current_value} = {result}"
            )

            # Round to avoid floating point errors
            result = round(result, 10)

            self.current_value = result
            self.operation = None
            self.should_reset_display = True

            return result

        except ValueError as error:
            self._handle_error(error)

    def clear(self) -> float:
        """
        Clear the calculator and reset to initial state.

        Returns:
            float: Zero (the reset value)
        """
        self.current_value = 0
        self.previous_value = 0
        self.operation = None
        self.should_reset_display = False
        return 0

    def get_history(self) -> List[str]:
        """
        Get the complete calculation history.

        Returns:
            List[str]: Array of historical operations
        """
        return self.history.copy()

    def clear_history(self) -> None:
        """Clear the calculation history"""
        self.history.clear()

    def _add_to_history(self, entry: str) -> None:
        """
        Add an operation to history with size limit.

        Args:
            entry: The history entry to add
        """
        self.history.append(entry)

        # Maintain max history size
        if len(self.history) > self.MAX_HISTORY_SIZE:
            self.history.pop(0)

    def _parse_input(self, input_value: Any) -> float:
        """
        Parse and validate input.

        Args:
            input_value: The input to parse

        Returns:
            float: The parsed number

        Raises:
            ValueError: If input is invalid
        """
        try:
            parsed = float(input_value)
        except (ValueError, TypeError):
            raise ValueError(f'Invalid input: "{input_value}" is not a valid number')

        if not (float('-inf') < parsed < float('inf')):
            raise ValueError("Input results in infinity or NaN")

        return parsed

    def _handle_error(self, error: Exception) -> None:
        """
        Handle and log errors.

        Args:
            error: The error to handle

        Raises:
            The same error
        """
        print(f"Calculator Error: {error}")
        raise error

    def get_display(self) -> float:
        """
        Get current display value.

        Returns:
            float: The current value to display
        """
        return self.current_value

    def get_state(self) -> Dict[str, Any]:
        """
        Get current state for debugging.

        Returns:
            Dict: Current calculator state
        """
        return {
            'current_value': self.current_value,
            'previous_value': self.previous_value,
            'operation': self.operation.value if self.operation else None,
            'should_reset_display': self.should_reset_display,
            'history_size': len(self.history)
        }


# ============================================================================
# TESTING AND VALIDATION
# ============================================================================

class CalculatorTests:
    """Test suite for the Calculator class"""

    def __init__(self):
        self.passed = 0
        self.failed = 0

    def test(self, description: str, test_fn) -> None:
        """
        Run a single test.

        Args:
            description: Test description
            test_fn: Test function
        """
        try:
            test_fn()
            self.passed += 1
            print(f"✓ {description}")
        except AssertionError as error:
            self.failed += 1
            print(f"✗ {description}")
            print(f"  Error: {error}")
        except Exception as error:
            self.failed += 1
            print(f"✗ {description}")
            print(f"  Unexpected Error: {error}")

    def assert_equal(self, actual: Any, expected: Any, message: str = "") -> None:
        """
        Assert that two values are equal.

        Args:
            actual: The actual value
            expected: The expected value
            message: Error message

        Raises:
            AssertionError: If values don't match
        """
        assert actual == expected, (
            message or f"Expected {expected}, but got {actual}"
        )

    def assert_true(self, condition: bool, message: str = "") -> None:
        """
        Assert that a condition is true.

        Args:
            condition: The condition to check
            message: Error message

        Raises:
            AssertionError: If condition is false
        """
        assert condition, message or "Condition is not true"

    def run_all(self) -> bool:
        """
        Run all tests.

        Returns:
            bool: True if all tests passed
        """
        print("\n" + "=" * 60)
        print("CALCULATOR TEST SUITE")
        print("=" * 60 + "\n")

        # Test 1: Basic Addition
        self.test('Basic Addition: 5 + 3 = 8', lambda: (
            calc := Calculator(),
            calc.input_number(5),
            calc.set_operation('+'),
            calc.input_number(3),
            self.assert_equal(calc.calculate(), 8, 'Addition failed')
        )[-1])

        # Test 2: Basic Subtraction
        self.test('Basic Subtraction: 10 - 4 = 6', lambda: (
            calc := Calculator(),
            calc.input_number(10),
            calc.set_operation('-'),
            calc.input_number(4),
            self.assert_equal(calc.calculate(), 6, 'Subtraction failed')
        )[-1])

        # Test 3: Basic Multiplication
        self.test('Basic Multiplication: 6 * 7 = 42', lambda: (
            calc := Calculator(),
            calc.input_number(6),
            calc.set_operation('*'),
            calc.input_number(7),
            self.assert_equal(calc.calculate(), 42, 'Multiplication failed')
        )[-1])

        # Test 4: Basic Division
        self.test('Basic Division: 20 / 4 = 5', lambda: (
            calc := Calculator(),
            calc.input_number(20),
            calc.set_operation('/'),
            calc.input_number(4),
            self.assert_equal(calc.calculate(), 5, 'Division failed')
        )[-1])

        # Test 5: Division by Zero
        def test_division_by_zero():
            calc = Calculator()
            calc.input_number(10)
            calc.set_operation('/')
            calc.input_number(0)
            try:
                calc.calculate()
                raise AssertionError('Should have thrown division by zero error')
            except ValueError as e:
                self.assert_true('Division by zero' in str(e), 'Wrong error message')

        self.test('Division by Zero throws error', test_division_by_zero)

        # Test 6: Multiple Operations in Session
        def test_multiple_ops():
            calc = Calculator()
            calc.input_number(10)
            calc.set_operation('+')
            calc.input_number(5)
            result = calc.calculate()
            self.assert_equal(result, 15, 'First calculation failed')

            calc.set_operation('*')
            calc.input_number(2)
            result = calc.calculate()
            self.assert_equal(result, 30, 'Second calculation failed')

            calc.set_operation('-')
            calc.input_number(5)
            result = calc.calculate()
            self.assert_equal(result, 25, 'Third calculation failed')

        self.test('Multiple operations in one session', test_multiple_ops)

        # Test 7: Decimal Numbers
        def test_decimals():
            calc = Calculator()
            calc.input_number(3)
            calc.input_decimal()
            calc.input_number(5)
            calc.set_operation('+')
            calc.input_number(2)
            calc.input_decimal()
            calc.input_number(5)
            result = calc.calculate()
            self.assert_equal(result, 6.0, 'Decimal addition failed')

        self.test('Decimal number handling: 3.5 + 2.5 = 6', test_decimals)

        # Test 8: Clear Function
        def test_clear():
            calc = Calculator()
            calc.input_number(42)
            calc.set_operation('+')
            calc.clear()
            self.assert_equal(calc.get_display(), 0, 'Clear failed')

        self.test('Clear function resets calculator', test_clear)

        # Test 9: History Tracking
        def test_history():
            calc = Calculator()
            calc.input_number(5)
            calc.set_operation('+')
            calc.input_number(3)
            calc.calculate()

            history = calc.get_history()
            self.assert_true(len(history) > 0, 'History not recorded')
            self.assert_true('5.0 + 3.0 = 8.0' in history[0], 'History entry incorrect')

        self.test('History tracking works correctly', test_history)

        # Test 10: Invalid Operation
        def test_invalid_op():
            calc = Calculator()
            calc.input_number(5)
            try:
                calc.set_operation('%')
                raise AssertionError('Should have thrown invalid operation error')
            except ValueError as e:
                self.assert_true('Invalid operation' in str(e), 'Wrong error message')

        self.test('Invalid operation throws error', test_invalid_op)

        # Test 11: Invalid Input
        def test_invalid_input():
            calc = Calculator()
            try:
                calc.input_number('abc')
                raise AssertionError('Should have thrown invalid input error')
            except ValueError as e:
                self.assert_true('Invalid input' in str(e), 'Wrong error message')

        self.test('Invalid input throws error', test_invalid_input)

        # Test 12: State Management
        def test_state():
            calc = Calculator()
            calc.input_number(10)
            calc.set_operation('+')
            calc.input_number(5)

            state = calc.get_state()
            self.assert_equal(state['current_value'], 5, 'Current value incorrect')
            self.assert_equal(state['previous_value'], 10, 'Previous value incorrect')
            self.assert_equal(state['operation'], '+', 'Operation incorrect')

        self.test('State management maintains consistency', test_state)

        # Print summary
        print("\n" + "=" * 60)
        print(f"RESULTS: {self.passed} passed, {self.failed} failed")
        print("=" * 60 + "\n")

        return self.failed == 0


# ============================================================================
# INTERACTIVE CLI INTERFACE
# ============================================================================

class CalculatorCLI:
    """Interactive command-line interface for the calculator"""

    def __init__(self):
        self.calculator = Calculator()
        self.running = False

    def display_help(self) -> None:
        """Display the help menu"""
        help_text = """
╔════════════════════════════════════════════════════════════╗
║               PYTHON CALCULATOR - HELP MENU               ║
╚════════════════════════════════════════════════════════════╝

OPERATIONS:
  <number>        Input a number (supports decimals)
  +               Addition
  -               Subtraction
  *               Multiplication
  /               Division
  =               Calculate result
  .               Add decimal point
  c               Clear calculator
  h               Show history
  ?               Show this help
  q               Quit

EXAMPLES:
  5 + 3 =         Result: 8
  10 - 4 =        Result: 6
  6 * 7 =         Result: 42
  20 / 4 =        Result: 5

FEATURES:
  • Multiple operations per session
  • Calculation history tracking
  • Full operation typing
  • Simple error handling

════════════════════════════════════════════════════════════
"""
        print(help_text)

    def display_history(self) -> None:
        """Display calculation history"""
        history = self.calculator.get_history()
        if not history:
            print("\nNo calculation history yet.\n")
            return

        print("\n" + "=" * 60)
        print("CALCULATION HISTORY")
        print("=" * 60)
        for i, entry in enumerate(history, 1):
            print(f"{i:2}. {entry}")
        print("=" * 60 + "\n")

    def run(self) -> None:
        """Start the interactive calculator"""
        self.running = True
        print("\n" + "=" * 60)
        print("WELCOME TO THE PYTHON CALCULATOR")
        print("=" * 60)
        self.display_help()

        while self.running:
            try:
                # Display current value
                print(f"Display: {self.calculator.get_display()}", end="  ")

                # Get user input
                user_input = input("Enter operation: ").strip().lower()

                # Handle commands
                if user_input == 'q':
                    print("\nThank you for using the calculator!")
                    self.running = False
                    break
                elif user_input == '?':
                    self.display_help()
                elif user_input == 'h':
                    self.display_history()
                elif user_input == 'c':
                    self.calculator.clear()
                    print("Calculator cleared.")
                elif user_input == '.':
                    self.calculator.input_decimal()
                elif user_input in ['+', '-', '*', '/']:
                    self.calculator.set_operation(user_input)
                elif user_input == '=':
                    result = self.calculator.calculate()
                    print(f"Result: {result}")
                else:
                    # Try to parse as number
                    self.calculator.input_number(user_input)

            except (ValueError, ZeroDivisionError) as e:
                print(f"Error: {e}")
            except KeyboardInterrupt:
                print("\n\nCalculator interrupted by user.")
                self.running = False
            except Exception as e:
                print(f"Unexpected error: {e}")


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main entry point for the calculator"""
    import sys

    # Check if running tests
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        tests = CalculatorTests()
        all_passed = tests.run_all()
        sys.exit(0 if all_passed else 1)
    else:
        # Run interactive CLI
        cli = CalculatorCLI()
        cli.run()


if __name__ == "__main__":
    main()
