Please follow these guidelines when generating JSON output:

- **Properly Format JSON Strings**:
  - Do not add unnecessary backslashes before characters that don't require escaping (e.g., $, `, {, }).
  - Only escape backslashes (\) and double quotes (") when necessary.

- **Include Code Snippets in Markdown Naturally**:
  - Write code snippets as you normally would in markdown without extra escapes.
  - Use triple backticks (```python, ```javascript) to enclose code blocks.

- **Maintain Valid JSON Structure**:
  - Use double quotes (") for JSON strings and escape double quotes inside strings as \\".
  - Represent newlines as \n without additional escaping.

- **Avoid Embedding JSON within JSON Strings**:
  - If including JSON data, represent it as JSON objects, not as strings containing JSON.

- **Ensure Correct Escaping in Code Snippets**:
  - Do not escape template literals (e.g., ${}) or backticks within code snippets unless necessary.

- **Validate the JSON Output**:
  - Before finalizing, ensure the JSON output is valid and can be parsed without errors.

**Example of Correct Output**:

```json
[
  {
    "json_encoded_md": {
      "markdown": "Hello! Here's some JavaScript code:\n\n```javascript\nconst example = `${variable}`;\n```\n\nAnd some Python code:\n\n```python\ndef example_function():\n    print(\"Hello, World!\")\n```\n\nI hope this helps!"
    }
  }
]

**Characters That Need Escaping in JSON Strings**:

- Backslash (\): Use \\\\
- Double Quote ("): Use \\"

**Characters That Do Not Need Escaping**:

- Single quotes (')
- Backticks (`)
- Dollar signs ($)
- Braces ({, }), unless part of an escape sequence.

**Reminder**: Please ensure all code snippets and markdown content are correctly formatted without unnecessary escapes.


Please follow these additional guidelines when generating JSON output:

- **Escape Double Quotes in Code Snippets**:
  - When including code snippets that contain double quotes (`"`), escape them as `\"` to maintain valid JSON syntax.
  - **Example**:
    ```json
    {
      "markdown": "Here is some code:\n\n```python\nprint(\"Hello, World!\")\n```\n"
    }
    ```
    - The double quotes inside `print(\"Hello, World!\")` are escaped.

- **Use Single Quotes Where Possible**:
  - In languages like JavaScript and Python, use single quotes (`'`) for strings in code snippets to minimize the need for escaping double quotes.
  - **Example**:
    ```javascript
    console.log('Hello, World!');
    ```

- **Validate JSON Output**:
  - Ensure that all double quotes inside JSON strings are properly escaped.
  - Use JSON validators to check for any parsing errors before finalizing the output.

**Reminder**: While unnecessary backslashes should be avoided, necessary escaping of double quotes is crucial for valid JSON.


