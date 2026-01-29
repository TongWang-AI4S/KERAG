# Multi-Language Support [@multi-language]

KERAG supports multi-language knowledge bases, allowing you to provide different language versions for the same content and automatically select the most appropriate version based on user language preferences.

## File Naming Conventions [@file-naming]

Multi-language files are identified by suffixes:

- **Default Language Files**: `filename.md` or `index.md`
- **Chinese Version**: `filename.zh.md` or `index.zh.md`
- **English Version**: `filename.en.md` or `index.en.md`
- **Other Languages**: Use ISO 639-1 two-letter language codes (e.g., `.ja` for Japanese, `.de` for German)

**Directory Structure Example**:
```text
linear-algebra/
├── index.md           # Default version
├── index.zh.md        # Chinese entry
├── index.en.md        # English entry
├── matrix.md          # Default version
├── matrix.zh.md       # Chinese matrix section
└── matrix.en.md       # English matrix section
```

## Language Resolution Priority [@language-priority]

When the system needs to find the physical file corresponding to a `file_id`, it tries in the following priority order:

Assuming current language is set to `en`, looking up `linear-algebra/matrix`:

1. `linear-algebra/matrix.en.md` (Priority match current language)
2. `linear-algebra/matrix.md` (Fallback to default version)

For directory-type references (e.g., `linear-algebra`):

1. `linear-algebra/index.en.md` (Priority match current language)
2. `linear-algebra/index.md` (Fallback to default version)

## File ID Language Independence [@file-id-language]

**Important**: Regardless of which language version is used, the file ID remains the same.

- File IDs for both `matrix.zh.md` and `matrix.en.md` are `linear-algebra::matrix`
- No need to specify language when referencing: `(@linear-algebra/matrix::content)` automatically resolves to the current language version

This design ensures cross-language reference simplicity and consistency.

## Configuring Language Preference [@language-config]

The system determines the current language through:

- **Environment Variable**: Set `KERAG_LANG` environment variable (e.g., `zh`, `en`)
- **Program Interface**: Pass `lang` parameter when calling in code

```bash
# Set environment variable before running commands
export KERAG_LANG=en
```

## Best Practices [@best-practices-i18n]

### Structural Consistency
Different language versions should maintain the same section structure and label naming to ensure cross-language references resolve correctly:

```markdown
<!-- matrix.zh.md -->
# 矩阵 [@matrix]
矩阵是一个按照长方阵列排列的复数或实数集合。

<!-- matrix.en.md -->
# Matrix [@matrix]
A matrix is a rectangular array of complex or real numbers.
```

### Default Language Fallback
It is recommended to always provide a default language version (files without language suffixes), so the system can gracefully fall back to the default version when a specific language version is missing, rather than erroring.
