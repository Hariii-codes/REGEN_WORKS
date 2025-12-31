# Batch Translation System

This system translates ALL user-facing strings in ONE batch API call per language, avoiding multiple API requests.

## How It Works

1. **Extract all strings** - All hardcoded user-facing text is in `locales/en.json`
2. **Batch translate** - Run `batch_translate_all.py` to translate ALL strings in ONE API call per language
3. **Generate language files** - Translated strings are saved to `locales/{language}.json`
4. **Use i18n** - Code uses `get_localized_string()` to display translated text

## Usage

### Step 1: Add New Strings to `locales/en.json`

When you add new hardcoded strings, add them to `locales/en.json`:

```json
{
  "your.new.key": "Your English text here"
}
```

### Step 2: Run Batch Translation

```bash
python batch_translate_all.py
```

This will:
- Load ALL strings from `locales/en.json`
- Translate them to each target language in ONE batch request per language
- Save translated files to `locales/{language}.json`

### Step 3: Use i18n in Code

Replace hardcoded strings with i18n lookups:

```python
from localization_helper import get_localized_string, get_current_language

lang = get_current_language()
text = get_localized_string('your.new.key', lang, 'Default English text')
```

## Target Languages

- `hi` - Hindi
- `kn` - Kannada
- `ta` - Tamil
- `mr` - Marathi
- `bn` - Bengali

## Important Notes

- **ONE API call per language** - All strings are translated together in a single batch
- **No runtime translation** - All translation happens during setup, not during user requests
- **Preserves structure** - JSON keys and placeholders like `{variable}` are preserved
- **HTML safe** - HTML tags in strings are preserved during translation

## Files Modified

- `locales/en.json` - Contains all English strings
- `carbon_calculator.py` - Uses i18n for carbon text
- `gemini_formatter.py` - Uses i18n for summary templates
- `batch_translate_all.py` - Batch translation script

