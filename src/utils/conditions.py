class Conditions:

    def and_operation(operand1, operand2) -> bool:
        """
        Compute the conjunction (AND) of two boolean operands.

        This uses the bitwise AND operator (&) on boolean inputs, which is
        equivalent to logical AND for booleans.

        Args:
            operand1 (bool): First boolean operand.
            operand2 (bool): Second boolean operand.

        Returns:
            bool: True if both operands are True; otherwise False.
        """
        return operand1 & operand2


    def or_operation(operand1, operand2) -> bool:
        """
        Compute the conjunction (OR) of two boolean operands.

        This uses the bitwise OR operator (|) on boolean inputs, which is
        equivalent to logical OR for booleans.

        Args:
            operand1 (bool): First boolean operand.
            operand2 (bool): Second boolean operand.

        Returns:
            bool: True if at least one operand is True; otherwise False.
        """
        return operand1 | operand2


    def xor_operation(operand1, operand2) -> bool:
        """
        Compute the conjunction (XOR) of two boolean operands.

        This uses the bitwise XOR operator (^) on boolean inputs, which is
        equivalent to logical XOR for booleans.

        Args:
            operand1 (bool): First boolean operand.
            operand2 (bool): Second boolean operand.

        Returns:
            bool: True if both operands are different; otherwise False.
        """
        return operand1 ^ operand2


    def not_operation(operand) -> bool:
        """
        Compute the negation of a boolean operand.

        Args:
            operand (bool): Boolean operand.

        Returns:
            bool: True if the operands is False; otherwise False.
        """
        return not operand


    def and_conclusions_operation(operand1, operand2) -> bool:
        """


        Args:
            operand1
            operand2

        Returns:

        """
        return self.and_operation(operand1, operand2) # Mais à la fin genre
