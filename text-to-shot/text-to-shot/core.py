"""
Core functionality for converting text to scenes and shots.
"""
import os
import glob
import textwrap
from typing import List, Optional, Tuple
from dotenv import load_dotenv
from openai import OpenAI

from .models import StoryAnalysisResult


class TextToShotsProcessor:
    """
    Main processor class for converting text stories to scenes and shots.
    """

    def __init__(self, api_key: str = None, references_folder: str = "outputs"):
        """
        Initialize the processor.

        Args:
            api_key: OpenAI API key. If None, will try to load from environment
            references_folder: Path to folder containing reference documents
        """
        # Load environment variables
        load_dotenv()

        # Set up API key
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not provided and not found in environment variables")

        self.client = OpenAI(api_key=self.api_key)
        self.references_folder = references_folder

        # Model configurations
        self.default_model = "gpt-4o-mini"
        self.fast_model = "gpt-4o-mini"
        self.language_detect_model = "gpt-4o-mini"

        # Example prompts for reference
        self._setup_examples()

    def _setup_examples(self):
        """Setup example prompts for better AI responses."""
        self.example_raw = textwrap.dedent("""
        "Wife, You Are Right Too" Anecdote
        Film Treatment
        One day, a neighbor comes to Hodja's house, upset. He complains about his wife and asks Hodja to judge who is right. Hodja listens, nods, and says, "You are right."
        After the neighbor leaves, his wife comes in, equally upset. She presents her side. Hodja nods and says, "You are right too." Hodja's own wife, having overheard, says, "How can both be right?" Hodja pauses, thinks, and replies, "Wife, you are right too."
        """).strip()

        self.example_scenes = textwrap.dedent("""
        SCENE 1 / HODJA'S COURTYARD / DAY / EXTERIOR / HODJA – NEIGHBOR
        Hodja greets his agitated neighbor and listens to the complaint.
        NEIGHBOR (agitated)
        Hodja, you must help me with this matter!
        HODJA (calmly)
        Tell me what troubles you, my friend.
        SCENE 2 / HODJA'S COURTYARD / DAY / EXTERIOR / HODJA – COMPLAINANT
        Hodja tells the man, "You are right," and sends him away.
        HODJA (raising his hand)
        You are right, my friend.
        COMPLAINANT (relieved)
        Thank you, Hodja. I knew you would understand.
        """).strip()

        self.example_shots = textwrap.dedent("""
        # EXAMPLE SCENE (4 SHOTS - MORE COMPLEX)
        SCENE 1 / HODJA'S COURTYARD / DAY / EXTERIOR / HODJA – NEIGHBOR
        🎥 Objective: Establish the rural setting, neighbor's agitation, and Hodja's calm demeanor.
        1. Wide Shot – Neighbor knocking on the gate
        Prompt: "Morning light over a rustic courtyard, an agitated man pounding on a wooden gate…"
        2. Medium Shot - Hodja opening the gate
        Prompt: "Hodja opens the wooden gate, his expression is calm and welcoming."
        3. Two-Shot – Neighbor explaining his problem animatedly
        Prompt: "The neighbor gestures wildly while complaining, Hodja listens patiently, nodding."
        4. Close-Up – Hodja's calm face
        Prompt: "Hodja's serene expression as he listens, soft shadows under his turban."
        # EXAMPLE SCENE (2 SHOTS - SIMPLER)
        SCENE 2 / HODJA'S COURTYARD / DAY / EXTERIOR / HODJA – COMPLAINANT
        🎥 Objective: Show Hodja's judgment and the complainant's relief.
        1. Medium Shot – Hodja raising a reassuring hand
        Prompt: "Hodja seated on a low wooden bench, palm up, saying 'You are right'..."
        2. Wide Shot – Complainant departing happily
        Prompt: "Man walking away from the courtyard, posture relaxed, bright midday sun."
        """).strip()

    def process_story(self, raw_story: str, use_references: bool = True) -> StoryAnalysisResult:
        """
        Main method to process a story into scenes and shots.

        Args:
            raw_story: The raw story text to process
            use_references: Whether to use reference documents

        Returns:
            StoryAnalysisResult: Complete analysis result
        """
        if not raw_story.strip():
            raise ValueError("Story text cannot be empty")

        # Load references if requested
        combined_references = "No references provided."
        loaded_files = []
        if use_references:
            combined_references, loaded_files = self._load_references()

        # Detect language and translate if needed
        detected_language = self._detect_language(raw_story)
        story_text = raw_story
        translated_story = None

        if detected_language.lower() != "english":
            translated_story = self._translate_to_english(raw_story)
            story_text = translated_story

        # Generate scenes
        scenes_output = self._generate_scenes(story_text, combined_references)

        # Generate shots
        shots_output = self._generate_shots(scenes_output, combined_references)

        return StoryAnalysisResult(
            original_story=raw_story,
            detected_language=detected_language,
            translated_story=translated_story,
            scenes=scenes_output,
            shots=shots_output,
            references_used=loaded_files
        )

    def _chat(self, messages: List[dict], model: str, temperature: float = 0.4) -> str:
        """Internal method to communicate with OpenAI API."""
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise RuntimeError(f"OpenAI API error: {str(e)}")

    def _detect_language(self, text: str) -> str:
        """Detect the language of the input text."""
        prompt = [
            {"role": "system", "content": "You are a language detector. Answer only with 'turkish' or 'english'."},
            {"role": "user", "content": text}
        ]
        return self._chat(prompt, model=self.language_detect_model, temperature=0.0)

    def _translate_to_english(self, text: str) -> str:
        """Translate text from Turkish to English."""
        messages = [
            {
                "role": "system",
                "content": "You are a professional translator. Translate the following story from Turkish to fluent, natural English suitable for film scene analysis."
            },
            {"role": "user", "content": text}
        ]
        return self._chat(messages, model=self.fast_model, temperature=0.3)

    def _generate_scenes(self, story_text: str, references: str) -> str:
        """Generate scenes from the story text."""
        system = "You are a professional script analyst. Using the provided reference documents, break the raw story into as many scenes as necessary. Start a new scene only when the location, time of day, emotional tone, or main characters change. Do not merge distinct story beats into a single scene. Use this exact format for each scene header:\nSCENE <n> / <LOCATION> / <TIME> / <INTERIOR|EXTERIOR> / <CHARACTERS>\nThen list concise action descriptions and dialogue in English. No commentary or Turkish."
        example = f"### REFERENCE EXAMPLE ###\nRaw story (example):\n{self.example_raw}\n{self.example_scenes}\nEnd example."
        user = f"### REFERENCE DOCUMENTS ###\n{references}\n\n### RAW STORY TO ANALYZE ###\n{story_text}"

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": example},
            {"role": "user", "content": user}
        ]

        return self._chat(messages, model=self.default_model, temperature=0.25)

    def _generate_shots(self, scenes_text: str, references: str) -> str:
        """Generate shots from the scenes text."""
        system = "You are an experienced storyboard artist. Using only the provided scene list, create a dynamic number of shots per scene. The number of shots must be based on the scene's content and complexity—do not use a fixed count. A simple action might only need 1-2 shots, while a complex dialogue or action sequence could require 8 or more. Include an Objective line and reset numbering for each scene. Use this format:\n<number>. <Shot Title> – <brief action>\nPrompt: \"<vivid English prompt>\""
        example = f"### REFERENCE EXAMPLE ###\n{self.example_shots}\nEnd example."
        user = f"### REFERENCE DOCUMENTS ###\n{references}\n\n### SCENES TO VISUALIZE ###\n{scenes_text}\n\nGenerate shots for the scenes above:"

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": example},
            {"role": "user", "content": user}
        ]

        return self._chat(messages, model=self.default_model, temperature=0.55)

    def _load_references(self) -> Tuple[str, List[str]]:
        """Load and combine reference documents."""
        if not os.path.exists(self.references_folder):
            return "No references provided.", []

        doc_paths = glob.glob(os.path.join(self.references_folder, "*.txt"))
        reference_texts = []
        loaded_files = []

        for path in doc_paths:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        reference_texts.append(f"--- Ref: {os.path.basename(path)} ---\n{content[:500]}...")
                        loaded_files.append(os.path.basename(path))
            except Exception:
                continue

        combined_references = "\n\n".join(reference_texts) if reference_texts else "No references provided."
        return combined_references, loaded_files

    def get_available_references(self) -> List[str]:
        """Get list of available reference files."""
        if not os.path.exists(self.references_folder):
            return []

        doc_paths = glob.glob(os.path.join(self.references_folder, "*.txt"))
        return [os.path.basename(path) for path in doc_paths]