# Player Comparison System

A powerful AI-powered sports player comparison system that analyzes player data and generates comprehensive comparison reports in both text and PDF formats.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
  - [CLI Mode](#cli-mode)
  - [API Mode](#api-mode)
- [API Endpoints](#api-endpoints)
- [Player Data Format](#player-data-format)
- [Technical Details](#technical-details)
- [Development](#development)
- [License](#license)

## Overview

This system provides an intelligent way to compare sports players across multiple attributes including physical skills, technical abilities, and experience. It uses a sophisticated scoring engine combined with AI-powered analysis to deliver comprehensive player evaluations.

The system supports four major sports:
- Football
- Basketball
- Handball
- Volleyball

## Features

### Core Features
- **Multi-Sport Support**: Compare players across Football, Basketball, Handball, and Volleyball
- **Comprehensive Evaluation**: Analyzes physical attributes, technical skills, and experience
- **Position-Specific Scoring**: Weighted analysis based on position requirements
- **AI-Powered Analysis**: Uses Groq's Llama 3 70B for deep, contextual player comparisons
- **PDF Report Generation**: Professional formatted comparison reports
- **Dual Interface**: CLI for direct use and REST API for integration

### Smart Player Selection
- **Exact Name Matching**: Finds players with exact name matches
- **Partial Name Matching**: Searches for names containing the search term
- **Multiple Selection Options**: Select by list number, exact name, or player ID
- **Disambiguation**: When multiple players share the same name, displays sport and position for each

### Export Options
- **PDF Reports**: Professional, formatted reports with tables and analysis
- **TXT Reports**: Simple text format for quick viewing

## Architecture

The system is built with a modular architecture:
Player Comparison System
├── Data Layer
│ ├── PlayerDatabase: Manages player storage and retrieval
│ └── PlayerDataParser: Parses player data from text files
├── Engine Layer
│ ├── PhysicalEngine: Calculates physical attribute scores
│ ├── TechnicalEngine: Calculates technical skill scores
│ ├── ExperienceEngine: Calculates experience scores
│ ├── PositionEngine: Calculates position-specific scores
│ └── OverallEngine: Combines all scores for final rating
├── AI Layer
│ └── GroqComparisonEngine: Generates AI-powered analysis
└── Presentation Layer
├── CLI: Command-line interface
└── REST API: FastAPI implementation

## Installation

### Prerequisites
- Python 3.8 or higher
- Groq API key (for AI analysis)

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd player-comparison-system
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

pip install -r requirements.txt
cp .env.example .env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama3-70b-8192
