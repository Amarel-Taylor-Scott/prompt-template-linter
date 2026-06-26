# System Prompt Template Linter

A tiny, dependency-free Python tool that lints system prompt templates. It finds `{{placeholder}}` variables, counts instruction-like lines, flags unsafe keywords/phrases, and reports a simple complexity score.

## Features

- **Placeholder detection**: Extracts `{{placeholder}}` names and deduplicates them.
- **Instruction counting**: Detects bullet (`- ...`) and numbered (`1. ...`, `2) ...`) lines.
- **Unsafe keyword warnings**: Flags phrases such as `ignore previous`, `system prompt`, `override instructions`, etc.
- **Complexity score**: `placeholders + instructions + 2 × unsafe hits`.
- **CLI + library API**: Use it from the command line or import `lint_template` in your own code.

## Install / Usage

No installation required. Requires Python 3.10+.

```bash
# Lint a template file
python3 prompt_linter.py my_template.txt

# Or pipe a template in
cat my_template.txt | python3 prompt_linter.py
```

### Example

```text
You are a helpful coding assistant for {{language}}.

- Explain concepts clearly.
- Provide short code examples.
```

Output:

```text
Placeholders: language
Instructions: 2
Complexity:   3
```

## API

```python
from prompt_linter import lint_template

report = lint_template("Hello {{name}}, ignore previous instructions.")
print(report.to_dict())
```

## Tests

```bash
python3 -m pytest -q
python3 -m unittest discover
```

## License

MIT
