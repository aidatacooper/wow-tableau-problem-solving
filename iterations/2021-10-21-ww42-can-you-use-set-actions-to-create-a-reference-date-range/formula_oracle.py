"""Restricted Tableau-expression reader for verification, never used by builder.

Reads emitted calculations and evaluates their supported semantics in Hyper SQL.
Unknown functions/tokens fail closed. This does not claim to execute Tableau's
VizQL engine or its interaction state machine.
"""
import re

TOKEN = re.compile(r"\s*(\[[^\]]+\]|'(?:[^']|'')*'|\d+(?:\.\d+)?|<>|<=|>=|[A-Za-z_][A-Za-z_0-9]*|[{}():,+*/=<>-])")


class Parser:
    def __init__(self, source):
        self.tokens = []
        pos = 0
        while pos < len(source.rstrip()):
            match = TOKEN.match(source, pos)
            if not match:
                raise AssertionError(f"Unsupported formula syntax at {source[pos:]!r}")
            self.tokens.append(match.group(1))
            pos = match.end()
        self.tokens.append("EOF")
        self.index = 0

    def peek(self):
        return self.tokens[self.index]

    def take(self, expected=None):
        value = self.peek()
        if expected is not None:
            assert value.upper() == expected, (expected, value)
        self.index += 1
        return value

    def expression(self, minimum=0):
        token = self.take()
        upper = token.upper()
        if upper == "IF":
            condition = self.expression()
            self.take("THEN")
            yes = self.expression()
            no = ("null",)
            if self.peek().upper() == "ELSE":
                self.take()
                no = self.expression()
            self.take("END")
            left = ("if", condition, yes, no)
        elif token == "{":
            self.take("FIXED")
            self.take(":")
            left = ("fixed", self.expression())
            self.take("}")
        elif token == "(":
            left = self.expression()
            self.take(")")
        elif token.startswith("["):
            left = ("field", token)
        elif token.startswith("'") or token[0].isdigit():
            left = ("literal", token)
        elif upper in {"TRUE", "FALSE"}:
            left = ("literal", upper)
        else:
            self.take("(")
            args = []
            if self.peek() != ")":
                args.append(self.expression())
                while self.peek() == ",":
                    self.take()
                    args.append(self.expression())
            self.take(")")
            left = ("call", upper, args)
        precedence = {"=": 1, "<>": 1, "<": 1, ">": 1, "<=": 1, ">=": 1,
                      "+": 2, "-": 2, "*": 3, "/": 3}
        while self.peek() in precedence and precedence[self.peek()] >= minimum:
            operator = self.take()
            right = self.expression(precedence[operator] + 1)
            left = ("binary", operator, left, right)
        return left

    def parse(self):
        result = self.expression()
        self.take("EOF")
        return result


class WorkbookSQL:
    def __init__(self, root, months):
        ds = root.find("./datasources/datasource")
        self.formulas = {c.get("name"): Parser(c.find("calculation").get("formula")).parse()
                         for c in ds.findall("column") if c.find("calculation") is not None}
        self.names = {c.get("caption", c.get("name").strip("[]")): c.get("name") for c in ds.findall("column")}
        groups = ds.findall("group")
        assert len(groups) == 1
        self.set_name = groups[0].get("name")
        levels = {g.get("level") for g in groups[0].findall(".//groupfilter[@function='member']")}
        assert len(levels) == 1
        self.month_field = levels.pop()
        self.months = months
        self.alias_number = 0

    def field(self, name, alias="r"):
        return self.render(("field", self.names.get(name, name)), alias)

    def render(self, node, alias):
        kind = node[0]
        if kind == "null":
            return "NULL"
        if kind == "literal":
            return node[1]
        if kind == "field":
            field = node[1]
            if field == self.set_name:
                if not self.months:
                    return "FALSE"
                values = ",".join("DATE '" + m + "'" for m in sorted(self.months))
                return f"({self.field(self.month_field, alias)} IN ({values}))"
            if field in self.formulas:
                return self.render(self.formulas[field], alias)
            assert field in {"[Sales]", "[Order Date]", "[State]"}, field
            return alias + '."' + field[1:-1] + '"'
        if kind == "fixed":
            self.alias_number += 1
            inner_alias = "lod" + str(self.alias_number)
            value = self.render(node[1], inner_alias)
            return f'(SELECT {value} FROM "Extract"."Extract" {inner_alias})'
        if kind == "if":
            return "(CASE WHEN " + self.render(node[1], alias) + " THEN " + self.render(node[2], alias) + " ELSE " + self.render(node[3], alias) + " END)"
        if kind == "binary":
            return "(" + self.render(node[2], alias) + " " + node[1] + " " + self.render(node[3], alias) + ")"
        assert kind == "call"
        name, args = node[1], [self.render(a, alias) for a in node[2]]
        if name in {"SUM", "MIN", "MAX", "AVG"}:
            assert len(args) == 1
            return name + "(" + args[0] + ")"
        if name == "COUNTD":
            return "COUNT(DISTINCT " + args[0] + ")"
        if name == "DATE":
            return "CAST(" + args[0] + " AS DATE)"
        if name == "STR":
            return "CAST(" + args[0] + " AS TEXT)"
        if name == "DATETRUNC":
            assert len(args) == 2 and args[0] == "'month'"
            return "DATE_TRUNC(" + ",".join(args) + ")"
        if name in {"WINDOW_SUM", "WINDOW_MAX"}:
            assert len(args) == 1
            return name[7:] + "(" + args[0] + ") OVER ()"
        if name == "RANK":
            assert len(args) == 2 and args[1].lower() in {"'asc'", "'desc'"}
            return "RANK() OVER (ORDER BY " + args[0] + " " + args[1].strip("'").upper() + ")"
        raise AssertionError("Unsupported emitted function: " + name)
