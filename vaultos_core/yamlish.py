"""A strict YAML subset, standard library only.

VaultOS files (tracker/*.yaml, requirements.yaml, project.yaml) use only:

    key: value                  plain, "double" or 'single' quoted scalars
    key: [a, "b, c"]            flow lists of scalars
    key: {}                     empty flow map
    key:                        nested block mapping or block list
      - id: T-1                 list of mappings
        title: ...
    # comments                  full-line or after a space

Anything else (block scalars `|` `>`, anchors, tags, non-empty flow maps,
tabs in indentation, multiple documents, a plain value containing ": ")
raises YamlError with the line number. It never guesses.

Scalars stay strings, except null / ~ / empty -> None and true / false -> bool.
"""

import re


class YamlError(ValueError):
    def __init__(self, line, message):
        super().__init__(f"line {line}: {message}")
        self.line = line
        self.message = message


class _Line:
    __slots__ = ("no", "indent", "text")

    def __init__(self, no, indent, text):
        self.no, self.indent, self.text = no, indent, text


def _strip_comment(s):
    quote, i = None, 0
    while i < len(s):
        ch = s[i]
        if quote:
            if ch == "\\" and quote == '"':
                i += 2
                continue
            if ch == quote:
                if quote == "'" and s[i + 1:i + 2] == "'":
                    i += 2
                    continue
                quote = None
        elif ch in "\"'" and (i == 0 or s[i - 1] in " [,:"):
            quote = ch
        elif ch == "#" and (i == 0 or s[i - 1] in " \t"):
            return s[:i].rstrip()
        i += 1
    return s.rstrip()


def _lines(text):
    out = []
    for no, raw in enumerate(text.splitlines(), 1):
        body = raw.lstrip(" ")
        if not body.strip() or body.lstrip().startswith("#"):
            continue
        if raw[:len(raw) - len(raw.lstrip(" \t"))].count("\t"):
            raise YamlError(no, "tab in indentation / 들여쓰기에 탭")
        if body.startswith(("---", "...")) and len(raw) == len(body):
            raise YamlError(no, "multiple documents are not supported / 여러 문서는 지원하지 않음")
        out.append(_Line(no, len(raw) - len(body), _strip_comment(body)))
    return out


def _unquote_double(s, no):
    out, i = [], 1
    while i < len(s) - 1:
        ch = s[i]
        if ch == "\\":
            nxt = s[i + 1]
            out.append({"n": "\n", "t": "\t", '"': '"', "\\": "\\"}.get(nxt, nxt))
            i += 2
            continue
        if ch == '"':
            raise YamlError(no, "unescaped quote inside string / 문자열 안의 따옴표")
        out.append(ch)
        i += 1
    return "".join(out)


def _split_flow(s, no):
    items, buf, quote = [], [], None
    i = 0
    while i < len(s):
        ch = s[i]
        if quote:
            buf.append(ch)
            if ch == "\\" and quote == '"':
                buf.append(s[i + 1])
                i += 2
                continue
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
            buf.append(ch)
        elif ch == ",":
            items.append("".join(buf).strip())
            buf = []
        elif ch in "[]{}":
            raise YamlError(no, "nested flow collections are not supported / 중첩된 [ ] { }는 지원하지 않음")
        else:
            buf.append(ch)
        i += 1
    if quote:
        raise YamlError(no, "unterminated string / 닫히지 않은 따옴표")
    last = "".join(buf).strip()
    if last or items:
        items.append(last)
    if any(x == "" for x in items):
        raise YamlError(no, "empty item in list / 목록에 빈 항목")
    return items


def scalar(s, no=0):
    s = s.strip()
    if s == "" or s in ("null", "~", "Null", "NULL"):
        return None
    if s in ("true", "True"):
        return True
    if s in ("false", "False"):
        return False
    if s[0] == '"':
        if len(s) < 2 or s[-1] != '"':
            raise YamlError(no, "unterminated string / 닫히지 않은 따옴표")
        return _unquote_double(s, no)
    if s[0] == "'":
        if len(s) < 2 or s[-1] != "'":
            raise YamlError(no, "unterminated string / 닫히지 않은 따옴표")
        return s[1:-1].replace("''", "'")
    if s[0] == "[":
        if s[-1] != "]":
            raise YamlError(no, "unterminated list / 닫히지 않은 [ ]")
        return [scalar(x, no) for x in _split_flow(s[1:-1], no)]
    if s[0] == "{":
        if s.replace(" ", "") == "{}":
            return {}
        raise YamlError(no, "flow mappings are not supported / { a: b } 형식은 지원하지 않음")
    if s[0] in "|>":
        raise YamlError(no, "block scalars (| >) are not supported / 여러 줄 값(| >)은 지원하지 않음")
    if s[0] in "&*!":
        raise YamlError(no, "anchors, aliases and tags are not supported / 앵커·별칭·태그는 지원하지 않음")
    if ": " in s or s.endswith(":"):
        raise YamlError(no, "quote a value that contains ': ' / ': '가 든 값은 따옴표로 감싼다")
    return s


_KEY = re.compile(r'^("(?:[^"\\]|\\.)*"|\'(?:[^\']|\'\')*\'|[^\s"\'#\-\[\]{}][^:]*?)\s*:(?:\s+(.*))?$')


def _mapping(lines, i, indent):
    out = {}
    while i < len(lines) and lines[i].indent == indent:
        ln = lines[i]
        if ln.text.startswith("- ") or ln.text == "-":
            raise YamlError(ln.no, "list item where a key was expected / 키가 와야 할 자리에 목록")
        m = _KEY.match(ln.text)
        if not m:
            raise YamlError(ln.no, "expected 'key: value' / 'key: value' 형식이 아님")
        key = scalar(m.group(1), ln.no) if m.group(1)[0] in "\"'" else m.group(1).strip()
        if key in out:
            raise YamlError(ln.no, f"duplicate key '{key}' / 키 중복")
        rest = m.group(2)
        i += 1
        if rest is not None and rest.strip():
            out[key] = scalar(rest, ln.no)
        elif i < len(lines) and lines[i].indent > indent:
            out[key], i = _block(lines, i, lines[i].indent)
        elif i < len(lines) and lines[i].indent == indent and (lines[i].text.startswith("- ") or lines[i].text == "-"):
            out[key], i = _list(lines, i, indent)
        else:
            out[key] = None
    if i < len(lines) and lines[i].indent > indent:
        raise YamlError(lines[i].no, "unexpected indentation / 들여쓰기가 맞지 않음")
    return out, i


def _list(lines, i, indent):
    out = []
    while i < len(lines) and lines[i].indent == indent and (lines[i].text.startswith("- ") or lines[i].text == "-"):
        ln = lines[i]
        rest = ln.text[1:].lstrip(" ")
        if not rest:
            i += 1
            if i < len(lines) and lines[i].indent > indent:
                item, i = _block(lines, i, lines[i].indent)
            else:
                item = None
        elif _KEY.match(rest) and not rest.startswith(("[", '"', "'")):
            col = indent + (len(ln.text) - len(rest))
            lines[i] = _Line(ln.no, col, rest)
            item, i = _mapping(lines, i, col)
        else:
            item = scalar(rest, ln.no)
            i += 1
        out.append(item)
    if i < len(lines) and lines[i].indent > indent:
        raise YamlError(lines[i].no, "unexpected indentation / 들여쓰기가 맞지 않음")
    return out, i


def _block(lines, i, indent):
    if lines[i].text.startswith("- ") or lines[i].text == "-":
        return _list(lines, i, indent)
    return _mapping(lines, i, indent)


def loads(text):
    """Parse text. Empty text -> {}."""
    lines = _lines(text)
    if not lines:
        return {}
    if lines[0].indent != 0:
        raise YamlError(lines[0].no, "the first key must not be indented / 첫 키는 들여쓰지 않는다")
    value, i = _block(lines, 0, 0)
    if i != len(lines):
        raise YamlError(lines[i].no, "unexpected content / 해석할 수 없는 줄")
    return value


def load(path):
    with open(path, encoding="utf-8") as fh:
        return loads(fh.read())


def quote(value):
    """A double-quoted scalar that loads() reads back unchanged."""
    s = str(value).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\t", "\\t")
    return f'"{s}"'


def flow(values):
    return "[" + ", ".join(quote(v) if _needs_quote(v) else str(v) for v in values) + "]"


_SAFE = re.compile(r"^[A-Za-z0-9_./@+][A-Za-z0-9_./@+()-]*$")


def _needs_quote(v):
    s = str(v)
    return not _SAFE.match(s) or scalar(s) != s
