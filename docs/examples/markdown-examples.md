# MAFA Documentation Formatting Examples

<!--
Examples: Markdown Formatting Examples
Description: Reference guide for common markdown formatting patterns used in MAFA documentation
Usage: Reference this file when writing or formatting documentation
Last Updated: 2025-11-19
-->

---
title: "Markdown Formatting Examples"
description: "Reference guide for common markdown formatting patterns used in MAFA documentation"
category: "developer-guide"
type: "reference"
audience: "contributor"
version: "1.0.0"
last_updated: "2025-11-19"
authors:
  - name: "MAFA Documentation Team"
    email: "docs@mafa.example.com"
tags:
  - "documentation"
  - "formatting"
  - "examples"
review_status: "published"
review_date: "2025-11-19"
---

## 📋 Table of Contents

- [Headers](#headers)
- [Text Formatting](#text-formatting)
- [Lists](#lists)
- [Code Blocks](#code-blocks)
- [Links](#links)
- [Images](#images)
- [Tables](#tables)
- [Blockquotes](#blockquotes)
- [Horizontal Rules](#horizontal-rules)
- [Special Elements](#special-elements)
- [Meta Documentation](#meta-documentation)

## Headers

### Basic Header Structure

```markdown
# H1 - Main Title
## H2 - Section Header  
### H3 - Subsection
#### H4 - Sub-subsection
##### H5 - Minor Section
###### H6 - Detail Level
```

### Header with Custom ID

```markdown
## Custom Header Title {#custom-id}
```

Referenced as: [Custom Link](#custom-id)

### Emoji Headers

```markdown
## 🚀 Getting Started
## 🛠️ Developer Guide  
## 📋 Project Management
## 🔧 Troubleshooting
## 📊 Analytics
## 🔒 Security
```

## Text Formatting

### Basic Formatting

- **Bold Text** - Use `**bold**` or `__bold__`
- *Italic Text* - Use `*italic*` or `_italic_`
- ***Bold and Italic*** - Use `***bold italic***`
- ~~Strikethrough~~ - Use `~~strikethrough~~`
- `Inline Code` - Use backticks

### Combined Formatting

**Bold with `code` inside**  
*Italic with [link](#) inside*  
***Bold italic with `code` and [link](#) inside***

### Text with Special Characters

```
Escaped characters: \*\*not bold\*\*
HTML entities: &copy; &trade; &reg;
Mathematical: x<sup>2</sup> + y<sub>2</sub> = z<sub>2</sub>
```

### Text Formatting Examples

- **Important notice:** Use bold for important information
- *Emphasized tip:* Use italics for tips and suggestions
- `Code references:` Use backticks for commands, files, and code
- ~~Deprecated features:~~ Use strikethrough for deprecated items

## Lists

### Unordered Lists

```markdown
- Item 1
- Item 2
  - Nested item 2.1
  - Nested item 2.2
- Item 3
```

- Item 1
- Item 2
  - Nested item 2.1
  - Nested item 2.2
- Item 3

### Ordered Lists

```markdown
1. First item
2. Second item
   1. Nested first
   2. Nested second
3. Third item
```

1. First item
2. Second item
   1. Nested first
   2. Nested second
3. Third item

### Task Lists

```markdown
- [x] Completed task
- [ ] Incomplete task
- [ ] Another incomplete task
```

- [x] Completed task
- [ ] Incomplete task
- [ ] Another incomplete task

### Definition Lists

```markdown
MAFA
:   MüncheWohnungsAssistent - Munich Housing Assistant

API
:   Application Programming Interface

CLI
:   Command Line Interface
```

MAFA
:   MüncheWohnungsAssistent - Munich Housing Assistant

API
:   Application Programming Interface

CLI
:   Command Line Interface

## Code Blocks

### Basic Code Blocks

```markdown
```bash
# Shell command example
mafa-command --version
```
```

```bash
# Shell command example
mafa-command --version
```

### Syntax Highlighting

```markdown
```python
# Python example
import mafa

client = mafa.Client()
result = client.get_data()
print(result)
```
```

```python
# Python example
import mafa

client = mafa.Client()
result = client.get_data()
print(result)
```

### JSON Examples

```markdown
```json
{
  "name": "MAFA",
  "version": "1.0.0",
  "type": "housing-assistant"
}
```
```

```json
{
  "name": "MAFA",
  "version": "1.0.0",
  "type": "housing-assistant"
}
```

### YAML Examples

```markdown
```yaml
mafa:
  config:
    log_level: INFO
    timeout: 30
  database:
    host: localhost
    port: 5432
```
```

```yaml
mafa:
  config:
    log_level: INFO
    timeout: 30
  database:
    host: localhost
    port: 5432
```

### Inline Code in Lists

```markdown
1. Run `mafa-command start`
2. Check status with `mafa-command status`  
3. Stop with `mafa-command stop`
```

1. Run `mafa-command start`
2. Check status with `mafa-command status`  
3. Stop with `mafa-command stop`

## Links

### Basic Links

```markdown
[Text Link](https://example.com)

[Relative Link](./relative-path.md)

[Link with Title](https://example.com "Link Title")
```

[Text Link](https://example.com)  
[Relative Link](./relative-path.md)  
[Link with Title](https://example.com "Link Title")

### Reference Links

```markdown
This is a [reference link][1] and another [reference link][2].

[1]: https://example.com
[2]: ./relative-file.md "Reference Link Title"
```

This is a [reference link][1] and another [reference link][2].

[1]: https://example.com
[2]: ./relative-file.md "Reference Link Title"

### Auto Links

```markdown
<https://example.com>

<user@example.com>
```

<https://example.com>  
<user@example.com>

### Links with Special Formatting

- **[Important Link](./important.md)** - Use bold for important links
- *[Tip Link](./tip.md)* - Use italics for tip links  
- `Command Link`[1] - Use backticks for command references

## Images

### Basic Image

```markdown
![Alt text](./images/example.png)
```

![Alt text](https://via.placeholder.com/150x100)

### Image with Title

```markdown
![Alt text](./images/example.png "Image Title")
```

![Alt text](https://via.placeholder.com/150x100 "Image Title")

### Responsive Images

```markdown
<img src="./images/example.png" alt="Alt text" width="300" height="200">
```

<img src="https://via.placeholder.com/300x200" alt="Alt text" width="300" height="200">

## Tables

### Basic Table

```markdown
| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Row 1    | Data     | Data     |
| Row 2    | Data     | Data     |
| Row 3    | Data     | Data     |
```

| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Row 1    | Data     | Data     |
| Row 2    | Data     | Data     |
| Row 3    | Data     | Data     |

### Formatted Table

```markdown
| Feature | Status | Priority | Owner |
|---------|--------|----------|-------|
| API v2  | ✅ Done | High | Dev Team |
| CLI     | 🚧 WIP  | Medium | Team A |
| Docs    | ❌ TODO | Low | Team B |
```

| Feature | Status | Priority | Owner |
|---------|--------|----------|-------|
| API v2  | ✅ Done | High | Dev Team |
| CLI     | 🚧 WIP  | Medium | Team A |
| Docs    | ❌ TODO | Low | Team B |

### Code Examples in Tables

```markdown
| Language | Example | Status |
|----------|---------|--------|
| Python | `import mafa` | ✅ Supported |
| JavaScript | `const mafa = require('mafa')` | ✅ Supported |
| Go | `import "github.com/org/mafa"` | 🚧 Coming Soon |
```

| Language | Example | Status |
|----------|---------|--------|
| Python | `import mafa` | ✅ Supported |
| JavaScript | `const mafa = require('mafa')` | ✅ Supported |
| Go | `import "github.com/org/mafa"` | 🚧 Coming Soon |

## Blockquotes

### Basic Blockquote

```markdown
> This is a blockquote.
> 
> It can span multiple lines.
```

> This is a blockquote.
> 
> It can span multiple lines.

### Nested Blockquotes

```markdown
> This is the main quote.
> 
> > This is a nested quote.
> > 
> > Back to the main quote.
```

> This is the main quote.
> 
> > This is a nested quote.
> > 
> > Back to the main quote.

### Blockquote with Code

```markdown
> Here's an important command:
> 
> ```bash
> mafa-command --verify-installation
> ```
```

> Here's an important command:
> 
> ```bash
> mafa-command --verify-installation
> ```

## Horizontal Rules

```markdown
---

***

___
```

---

***

___

## Special Elements

### Alerts and Callouts

```markdown
> **⚠️ Warning:** This is an important warning message.
> 
> **Note:** This is a helpful note.
> 
> **Tip:** This is a useful tip.
> 
> **Important:** This is crucial information.
```

> **⚠️ Warning:** This is an important warning message.
> 
> **Note:** This is a helpful note.
> 
> **Tip:** This is a useful tip.
> 
> **Important:** This is crucial information.

### Information Boxes

```markdown
::: info
This is an information box that provides additional context.
:::

::: warning  
This is a warning box that alerts users to potential issues.
:::

::: success
This is a success box that confirms positive outcomes.
:::
```

::: info
This is an information box that provides additional context.
:::

::: warning  
This is a warning box that alerts users to potential issues.
:::

::: success
This is a success box that confirms positive outcomes.
:::

### Details/Summary (Collapsible Content)

```markdown
<details>
<summary>Click to expand technical details</summary>

```python
# Technical implementation example
def technical_function():
    return "Advanced implementation details"
```

</details>
```

<details>
<summary>Click to expand technical details</summary>

```python
# Technical implementation example
def technical_function():
    return "Advanced implementation details"
```

</details>

### Math Formulas

```markdown
Inline formula: E = mc<sup>2</sup>

Block formula:

```
area = π × r²
volume = 4/3 × π × r³
```
```

Inline formula: E = mc<sup>2</sup>

Block formula:

```
area = π × r²
volume = 4/3 × π × r³
```

## Meta Documentation

### Document Metadata

All MAFA documentation files should include proper metadata:

```markdown
---
title: "Document Title"
description: "Brief description of the document"
category: "{getting-started|user-guide|developer-guide|architecture|operations|project}"
type: "{guide|reference|tutorial|api}"
audience: "{user|developer|operator}"
version: "1.0.0"
last_updated: "2025-11-19"
authors:
  - name: "Author Name"
    email: "author@example.com"
tags:
  - "tag1"
  - "tag2"
review_status: "draft|review|published"
review_date: "2025-11-19"
---
```

### Comments in Markdown

```markdown
<!-- This is an HTML comment and won't be rendered -->

<!--
This is a multi-line comment
that won't appear in the final output
-->
```

<!-- This is an HTML comment and won't be rendered -->

### File References

When referencing files in the repository:

```markdown
- Configuration: [`config.json`](../../config.json)
- Source code: [`mafa/core.py`](../../mafa/core.py)
- Documentation: [`docs/README.md`](./README.md)
```

### Cross-References

```markdown
See the [Installation Guide](./installation.md) for setup instructions.

For more details, see:
- [Configuration Reference](./configuration.md)
- [Troubleshooting Guide](./troubleshooting.md)  
- [API Documentation](../developer-guide/api/)
```

## Best Practices

### Writing Style

- Use active voice when possible
- Write in present tense for instructions
- Use consistent terminology throughout
- Keep sentences concise and clear
- Use headers to break up long content

### Code Examples

- Always test code examples before including them
- Use realistic but simple examples
- Include comments explaining key steps
- Show both input and expected output
- Use syntax highlighting for readability

### Links and References

- Use relative paths for internal links
- Include descriptive link text
- Test all links to ensure they work
- Avoid "click here" - use descriptive text
- Include a link to the full documentation where appropriate

### Images

- Use descriptive alt text
- Keep images appropriately sized
- Use consistent image formats (PNG for screenshots, SVG for diagrams)
- Include captions when helpful
- Store images in organized directory structure

---

*This file is part of the MAFA documentation formatting examples. For the complete style guide, see [Documentation Guidelines](../developer-guide/documentation-guidelines.md).*

<!--
Formatting Tips:
1. Always use consistent indentation (2 spaces for nested lists)
2. Keep lines to a reasonable length (80-120 characters)
3. Use empty lines to separate sections and major elements
4. Include examples for all formatting patterns
5. Test all links and images to ensure they work
6. Use semantic HTML where appropriate (details, summary, etc.)
7. Include metadata in all documentation files
8. Use consistent terminology throughout
9. Provide context for all code examples
10. Keep examples simple but realistic
-->