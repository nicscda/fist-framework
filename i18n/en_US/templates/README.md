# Templates

## Schema Configuration (Optional)

To enable auto-completion and validation in your editor (e.g., VS Code), add the [schema file path](/.schema.json) after `$schema=`:

```yaml
# Use local path (recommended)
# yaml-language-server: $schema=../../.schema.json

# Or use remote URL
# yaml-language-server: $schema=https://raw.githubusercontent.com/nicscda/fist-framework/refs/tags/latest/.schema.json
```

This enables real-time validation and helpful tooltips while editing.
