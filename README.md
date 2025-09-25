# ELA: English Language Assistant

## Overview

ELA is a bilingual multimedia application for English learners, primarily targeting Russian-speaking users from the former Soviet Union. The platform integrates linguistic analysis, translation, and vocabulary training, allowing users to select between paid online AI parsers and free offline models, as well as various translation services. The system transforms text or media into structured, interactive bilingual learning materials.

## Table of Contents

- [Research Problem](#research-problem)
- [Project Description](#project-description)
- [Key Features](#key-features)
- [Technologies](#technologies)
- [Objectives](#objectives)
- [Model Training Data](#model-training-data)
- [Technical Approach](#technical-approach)
- [Expected Deliverables](#expected-deliverables)
- [Timeline](#timeline)

## Research Problem

A bilingual multimedia learning app that adapts to individual English learning styles, combining linguistic analysis, translation, and vocabulary training with flexible parser and translation options.

## Project Description

ELA enables users to:

- Choose between a paid GPT-based cloud parser or a locally trained offline model (free to use).
- Select from multiple translation APIs (GPT, DeepL, HuggingFace, LaraAPI) or opt out of translation.
- Receive output in a unified JSON structure, ensuring compatibility across features.
- Process media/text into interactive syntax trees, example sentences, and personalized vocabulary lists.

## Key Features

- Audio/video transcription
- Optional translation via selected API
- Detailed linguistic parsing (grammatical tags, CEFR level, phonetic transcription)
- Interactive tree visualization of sentence structure
- Vocabulary extraction and export
- Project/media management interface

## Technologies

- **Core Processing & AI:** Python, PyTorch, HuggingFace Transformers, SpaCy, Whisper, ffmpeg
- **Frontend:** React, TailwindCSS, Kivy
- **Backend/API:** FastAPI, SQLite/PostgreSQL
- **Data Handling:** Pandas, JSONL, custom dataset preparation scripts
- **Integration:** GPT API, DeepL API, HuggingFace Inference API, LaraAPI

## Objectives

- Implement a full pipeline from media/text input to bilingual multimedia output with vocabulary and linguistic metadata
- Develop a custom AI parsing model matching GPT parser output
- Integrate both parsers into a single workflow
- Provide seamless integration of multiple translation providers
- Automate training data preparation from open/free sources
- Deliver a cross-platform user interface (desktop, web, mobile)

## Model Training Data

All datasets used are freely licensed for commercial use:

- Project Gutenberg – Public Domain – https://www.gutenberg.org
- Wikimedia Dumps – CC-BY-SA 4.0 – https://dumps.wikimedia.org
- OPUS OpenSubtitles 2018 – CC-BY 4.0 – https://opus.nlpl.eu
- Universal Dependencies (English EWT, GUM) – CC-BY-SA 4.0 – https://universaldependencies.org
- Tatoeba Project – CC-BY 2.0 – https://tatoeba.org
- CMU Pronouncing Dictionary – Public Domain – http://www.speech.cs.cmu.edu/cgi-bin/cmudict
- Wiktionary IPA data – CC-BY-SA 3.0/4.0 – https://dumps.wikimedia.org

> A dedicated Python script handles download, extraction, cleaning, and conversion of all datasets into a uniform JSONL format.

## Technical Approach

- **Core:** Python, PyTorch, HuggingFace Transformers, SpaCy, Whisper, ffmpeg
- **Frontend:** React (NodeBox.jsx, LinguisticNode.jsx, App.jsx), TailwindCSS, Kivy
- **Backend/API:** FastAPI, SQLite/PostgreSQL
- **Integration:** GPT API + custom model (selectable at runtime), multiple translation APIs

## Expected Deliverables

- Fully functional cross-platform application
- Trained offline parsing model compatible with GPT parser output
- Unified output for multiple translation APIs
- Automated dataset preparation pipeline
- Comparative benchmarks for GPT and local model
- Full documentation and demonstration materials

## Timeline

### Semester 1

- **Weeks 1–2:** Finalize dataset list and automation scripts
- **Weeks 3–6:** Implement transcription, segmentation, and translation modules
- **Weeks 7–10:** Train initial parsing model & integrate GPT parser
- **Weeks 11–14:** Connect both parsers to UI; begin testing

### Semester 2

- **Weeks 1–4:** Optimize parsing model for speed/accuracy
- **Weeks 5–8:** Extend vocabulary tools & project/media interface
- **Weeks 9–12:** Test complete system & compare parsers
- **Weeks 13–14:** Finalize documentation and submit
