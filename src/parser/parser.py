"""
NovaIR Parser - Parses tokens into an AST.

This module takes the token stream from the lexer and builds an Abstract Syntax Tree.
"""

from typing import List, Optional
from .lexer import Token, TokenType
from .ast import (
    System, State, Constraint, Objective, Action, Tick,
    Effect, Parameter, SourcePath, ValueWithUnit,
    Severity, CostLevel, ObjectiveType, TickMode
)


class ParseError(Exception):
    """Error during parsing."""
    def __init__(self, message: str, token: Token):
        self.message = message
        self.token = token
        super().__init__(f"Line {token.line}: {message} (got {token.type.name})")


class Parser:
    """Parses NovaIR tokens into an AST."""

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def parse(self) -> System:
        """Parse the token stream and return a System AST."""
        system = self._parse_system_decl()

        while not self._is_at_end():
            self._skip_newlines()
            if self._is_at_end():
                break

            if self._check(TokenType.STATE):
                system.states = self._parse_state_section()
            elif self._check(TokenType.CONSTRAINTS):
                system.constraints = self._parse_constraints_section()
            elif self._check(TokenType.OBJECTIVES):
                system.objectives = self._parse_objectives_section()
            elif self._check(TokenType.ACTIONS):
                system.actions = self._parse_actions_section()
            elif self._check(TokenType.TICK):
                system.tick = self._parse_tick_section()
            else:
                # Skip unknown tokens
                self._advance()

        return system

    # ============================================
    # Helper methods
    # ============================================

    def _peek(self) -> Token:
        """Return current token without advancing."""
        return self.tokens[self.pos]

    def _previous(self) -> Token:
        """Return the previous token."""
        return self.tokens[self.pos - 1]

    def _is_at_end(self) -> bool:
        """Check if we've reached the end of tokens."""
        return self._peek().type == TokenType.EOF

    def _check(self, type: TokenType) -> bool:
        """Check if current token is of given type."""
        if self._is_at_end():
            return False
        return self._peek().type == type

    def _advance(self) -> Token:
        """Consume and return current token."""
        if not self._is_at_end():
            self.pos += 1
        return self._previous()

    def _match(self, *types: TokenType) -> bool:
        """If current token matches any of the types, advance and return True."""
        for type in types:
            if self._check(type):
                self._advance()
                return True
        return False

    def _expect(self, type: TokenType, message: str) -> Token:
        """Expect and consume a token of the given type."""
        if self._check(type):
            return self._advance()
        raise ParseError(message, self._peek())

    def _skip_newlines(self):
        """Skip any newline tokens."""
        while self._match(TokenType.NEWLINE):
            pass

    def _skip_to_next_line(self):
        """Skip tokens until the next newline."""
        while not self._is_at_end() and not self._check(TokenType.NEWLINE):
            self._advance()
        self._skip_newlines()

    # ============================================
    # System declaration
    # ============================================

    def _parse_system_decl(self) -> System:
        """Parse: system Name @version("x.y")"""
        self._skip_newlines()
        self._expect(TokenType.SYSTEM, "Expected 'system' keyword")

        name_token = self._expect(TokenType.IDENTIFIER, "Expected system name")
        name = name_token.value
        version = None

        # Optional @version annotation
        if self._match(TokenType.VERSION):
            self._expect(TokenType.LPAREN, "Expected '(' after @version")
            version_token = self._expect(TokenType.STRING, "Expected version string")
            version = version_token.value
            self._expect(TokenType.RPAREN, "Expected ')' after version")

        self._skip_newlines()

        return System(name=name, version=version)

    # ============================================
    # State section
    # ============================================

    def _parse_state_section(self) -> List[State]:
        """Parse: state: followed by state bindings."""
        self._expect(TokenType.STATE, "Expected 'state'")
        self._expect(TokenType.COLON, "Expected ':' after 'state'")
        self._skip_newlines()

        states = []

        # Expect indent
        if self._match(TokenType.INDENT):
            while not self._check(TokenType.DEDENT) and not self._is_at_end():
                if self._is_identifier_like():
                    state = self._parse_state_binding()
                    states.append(state)
                self._skip_newlines()

            self._match(TokenType.DEDENT)

        return states

    def _is_identifier_like(self) -> bool:
        """Check if current token can be used as an identifier (including some keywords)."""
        # Allow some keywords to be used as identifiers in certain contexts
        identifier_like_types = {
            TokenType.IDENTIFIER,
            TokenType.TARGET,  # "target" can be a state name
            TokenType.MIN,
            TokenType.MAX,
            TokenType.MODE,
            TokenType.INTERVAL,
            TokenType.COST,
        }
        return self._peek().type in identifier_like_types

    def _consume_identifier_like(self, message: str) -> Token:
        """Consume a token that can be used as identifier."""
        if self._is_identifier_like():
            return self._advance()
        raise ParseError(message, self._peek())

    def _parse_state_binding(self) -> State:
        """Parse: name <- source.path"""
        name_token = self._consume_identifier_like("Expected state name")
        self._expect(TokenType.ARROW_LEFT, "Expected '<-'")
        source = self._parse_source_path()
        return State(name=name_token.value, source=source)

    def _parse_source_path(self) -> SourcePath:
        """Parse: identifier.identifier.identifier"""
        parts = []
        parts.append(self._expect(TokenType.IDENTIFIER, "Expected source path").value)

        while self._match(TokenType.DOT):
            parts.append(self._expect(TokenType.IDENTIFIER, "Expected identifier after '.'").value)

        return SourcePath(parts=parts)

    # ============================================
    # Constraints section
    # ============================================

    def _parse_constraints_section(self) -> List[Constraint]:
        """Parse: constraints: followed by constraint declarations."""
        self._expect(TokenType.CONSTRAINTS, "Expected 'constraints'")
        self._expect(TokenType.COLON, "Expected ':' after 'constraints'")
        self._skip_newlines()

        constraints = []

        if self._match(TokenType.INDENT):
            while not self._check(TokenType.DEDENT) and not self._is_at_end():
                if self._check(TokenType.IDENTIFIER):
                    constraint = self._parse_constraint()
                    constraints.append(constraint)
                self._skip_newlines()

            self._match(TokenType.DEDENT)

        return constraints

    def _parse_constraint(self) -> Constraint:
        """Parse: name : metric op value @severity"""
        name_token = self._expect(TokenType.IDENTIFIER, "Expected constraint name")
        self._expect(TokenType.COLON, "Expected ':'")

        metric_token = self._expect(TokenType.IDENTIFIER, "Expected metric name")
        operator = self._parse_comparison_operator()
        value = self._parse_value_with_unit()
        severity = self._parse_severity()

        return Constraint(
            name=name_token.value,
            metric=metric_token.value,
            operator=operator,
            value=value,
            severity=severity
        )

    def _parse_comparison_operator(self) -> str:
        """Parse a comparison operator."""
        ops = {
            TokenType.LTE: "<=",
            TokenType.GTE: ">=",
            TokenType.LT: "<",
            TokenType.GT: ">",
            TokenType.EQ: "==",
            TokenType.NEQ: "!=",
        }
        for token_type, op_str in ops.items():
            if self._match(token_type):
                return op_str
        raise ParseError("Expected comparison operator", self._peek())

    def _parse_severity(self) -> Severity:
        """Parse @critical or @warning."""
        if self._match(TokenType.CRITICAL):
            return Severity.CRITICAL
        elif self._match(TokenType.WARNING):
            return Severity.WARNING
        raise ParseError("Expected @critical or @warning", self._peek())

    # ============================================
    # Objectives section
    # ============================================

    def _parse_objectives_section(self) -> List[Objective]:
        """Parse: objectives: followed by objective declarations."""
        self._expect(TokenType.OBJECTIVES, "Expected 'objectives'")
        self._expect(TokenType.COLON, "Expected ':' after 'objectives'")
        self._skip_newlines()

        objectives = []

        if self._match(TokenType.INDENT):
            while not self._check(TokenType.DEDENT) and not self._is_at_end():
                if self._check(TokenType.IDENTIFIER):
                    objective = self._parse_objective()
                    objectives.append(objective)
                self._skip_newlines()

            self._match(TokenType.DEDENT)

        return objectives

    def _parse_objective(self) -> Objective:
        """Parse: name : metric -> type @priority(n)"""
        name_token = self._expect(TokenType.IDENTIFIER, "Expected objective name")
        self._expect(TokenType.COLON, "Expected ':'")

        metric_token = self._expect(TokenType.IDENTIFIER, "Expected metric name")
        self._expect(TokenType.ARROW_RIGHT, "Expected '->'")

        obj_type, target_value = self._parse_objective_type()
        priority = self._parse_priority()

        return Objective(
            name=name_token.value,
            metric=metric_token.value,
            type=obj_type,
            target_value=target_value,
            priority=priority
        )

    def _parse_objective_type(self) -> tuple:
        """Parse target(value), min, or max."""
        if self._match(TokenType.TARGET):
            self._expect(TokenType.LPAREN, "Expected '(' after 'target'")
            value = self._parse_value_with_unit()
            self._expect(TokenType.RPAREN, "Expected ')' after target value")
            return (ObjectiveType.TARGET, value)
        elif self._match(TokenType.MIN):
            return (ObjectiveType.MIN, None)
        elif self._match(TokenType.MAX):
            return (ObjectiveType.MAX, None)
        raise ParseError("Expected 'target', 'min', or 'max'", self._peek())

    def _parse_priority(self) -> int:
        """Parse @priority(n)."""
        self._expect(TokenType.PRIORITY, "Expected @priority")
        self._expect(TokenType.LPAREN, "Expected '(' after @priority")
        num_token = self._expect(TokenType.NUMBER, "Expected priority number")
        self._expect(TokenType.RPAREN, "Expected ')' after priority")
        return int(float(num_token.value))

    # ============================================
    # Actions section
    # ============================================

    def _parse_actions_section(self) -> List[Action]:
        """Parse: actions: followed by action declarations."""
        self._expect(TokenType.ACTIONS, "Expected 'actions'")
        self._expect(TokenType.COLON, "Expected ':' after 'actions'")
        self._skip_newlines()

        actions = []

        if self._match(TokenType.INDENT):
            while not self._check(TokenType.DEDENT) and not self._is_at_end():
                if self._check(TokenType.IDENTIFIER):
                    action = self._parse_action()
                    actions.append(action)
                self._skip_newlines()

            self._match(TokenType.DEDENT)

        return actions

    def _parse_action(self) -> Action:
        """Parse an action declaration."""
        name_token = self._expect(TokenType.IDENTIFIER, "Expected action name")
        self._expect(TokenType.COLON, "Expected ':'")
        self._skip_newlines()

        parameters = []
        effects = []
        cost = CostLevel.LOW

        if self._match(TokenType.INDENT):
            while not self._check(TokenType.DEDENT) and not self._is_at_end():
                if self._match(TokenType.PARAMETERS):
                    self._expect(TokenType.COLON, "Expected ':'")
                    parameters = self._parse_parameters_list()
                elif self._match(TokenType.EFFECTS):
                    self._expect(TokenType.COLON, "Expected ':'")
                    self._skip_newlines()
                    effects = self._parse_effects_list()
                elif self._match(TokenType.COST):
                    self._expect(TokenType.COLON, "Expected ':'")
                    cost = self._parse_cost_level()
                self._skip_newlines()

            self._match(TokenType.DEDENT)

        return Action(
            name=name_token.value,
            parameters=parameters,
            effects=effects,
            cost=cost
        )

    def _parse_parameters_list(self) -> List[Parameter]:
        """Parse: [name: min..max, ...]"""
        parameters = []
        self._expect(TokenType.LBRACKET, "Expected '['")

        while not self._check(TokenType.RBRACKET):
            name_token = self._expect(TokenType.IDENTIFIER, "Expected parameter name")
            self._expect(TokenType.COLON, "Expected ':'")
            min_token = self._expect(TokenType.NUMBER, "Expected min value")
            self._expect(TokenType.RANGE, "Expected '..'")
            max_token = self._expect(TokenType.NUMBER, "Expected max value")

            parameters.append(Parameter(
                name=name_token.value,
                min_value=int(float(min_token.value)),
                max_value=int(float(max_token.value))
            ))

            if not self._match(TokenType.COMMA):
                break

        self._expect(TokenType.RBRACKET, "Expected ']'")
        return parameters

    def _parse_effects_list(self) -> List[Effect]:
        """Parse the effects block."""
        effects = []

        if self._match(TokenType.INDENT):
            while not self._check(TokenType.DEDENT) and not self._is_at_end():
                if self._check(TokenType.IDENTIFIER):
                    effect = self._parse_effect()
                    effects.append(effect)
                self._skip_newlines()

            self._match(TokenType.DEDENT)

        return effects

    def _parse_effect(self) -> Effect:
        """Parse: metric: value [to value]"""
        metric_token = self._expect(TokenType.IDENTIFIER, "Expected metric name")
        self._expect(TokenType.COLON, "Expected ':'")

        min_effect = self._parse_value_with_unit()
        max_effect = None

        if self._match(TokenType.TO):
            max_effect = self._parse_value_with_unit()

        return Effect(
            metric=metric_token.value,
            min_effect=min_effect,
            max_effect=max_effect
        )

    def _parse_cost_level(self) -> CostLevel:
        """Parse low, medium, or high."""
        if self._match(TokenType.LOW):
            return CostLevel.LOW
        elif self._match(TokenType.MEDIUM):
            return CostLevel.MEDIUM
        elif self._match(TokenType.HIGH):
            return CostLevel.HIGH
        raise ParseError("Expected 'low', 'medium', or 'high'", self._peek())

    # ============================================
    # Tick section
    # ============================================

    def _parse_tick_section(self) -> Tick:
        """Parse: tick: followed by tick properties."""
        self._expect(TokenType.TICK, "Expected 'tick'")
        self._expect(TokenType.COLON, "Expected ':' after 'tick'")
        self._skip_newlines()

        tick = Tick()

        if self._match(TokenType.INDENT):
            while not self._check(TokenType.DEDENT) and not self._is_at_end():
                if self._match(TokenType.INTERVAL):
                    self._expect(TokenType.COLON, "Expected ':'")
                    num_token = self._expect(TokenType.NUMBER, "Expected number")
                    # Unit can be UNIT token or IDENTIFIER (ms, s, m, h)
                    unit = "ms"  # default
                    if self._match(TokenType.UNIT):
                        unit = self._previous().value.lower()
                    elif self._check(TokenType.IDENTIFIER):
                        # Accept ms, s, m, h as identifiers too
                        id_value = self._peek().value.lower()
                        if id_value in ("ms", "s", "m", "h"):
                            self._advance()
                            unit = id_value
                    # Convert to ms
                    value = float(num_token.value)
                    if unit == "s":
                        value *= 1000
                    elif unit == "m":
                        value *= 60000
                    elif unit == "h":
                        value *= 3600000
                    tick.interval_ms = int(value)
                elif self._match(TokenType.ACTION_THRESHOLD):
                    self._expect(TokenType.COLON, "Expected ':'")
                    num_token = self._expect(TokenType.NUMBER, "Expected number")
                    tick.action_threshold = float(num_token.value)
                elif self._match(TokenType.MODE):
                    self._expect(TokenType.COLON, "Expected ':'")
                    if self._match(TokenType.CONTINUOUS):
                        tick.mode = TickMode.CONTINUOUS
                    elif self._match(TokenType.REACTIVE):
                        tick.mode = TickMode.REACTIVE
                    else:
                        raise ParseError("Expected 'continuous' or 'reactive'", self._peek())
                self._skip_newlines()

            self._match(TokenType.DEDENT)

        return tick

    # ============================================
    # Value parsing
    # ============================================

    def _parse_value_with_unit(self) -> ValueWithUnit:
        """Parse a number with optional unit."""
        num_token = self._expect(TokenType.NUMBER, "Expected number")
        value = float(num_token.value)
        unit = None

        if self._match(TokenType.UNIT):
            unit = self._previous().value

        return ValueWithUnit(value=value, unit=unit)
