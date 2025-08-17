# text_to_shots

`text_to_shots` converts raw story text into structured film scenes and camera shots using OpenAI models. It can optionally read reference documents to guide the tone and style of the output.

## Features
- Detects the story language and translates non-English text to English
- Breaks a story into numbered scene headers with concise descriptions and dialogue
- Expands scenes into shot lists with per-shot prompts for image generation
- Supports optional reference documents to influence results

## Installation
The package can be installed from source:

```bash
pip install -e .
```

This installs the runtime dependencies listed in `setup.py`.

## Usage
Provide an OpenAI API key and pass a story string to `TextToShotsProcessor.process_story`:

```python
from text_to_shots import TextToShotsProcessor

processor = TextToShotsProcessor(api_key="sk-YOURKEY")  # or set OPENAI_API_KEY env var
story = """\
An angry neighbor seeks Hodja's advice.
His wife later does the same.
Hodja tells them both they are right.
"""
result = processor.process_story(story)

print(result.scenes)
print(result.shots)
```

Reference documents can be placed in an `outputs/` folder (or another path passed to the constructor) and discovered with:

```python
processor.get_available_references()
```

## Development
Install development extras and run the linters/tests:

```bash
pip install -e .[dev]
python -m py_compile $(git ls-files '*.py')
pytest
```

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
