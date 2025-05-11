# KaraTube

KaraTube is a YouTube search application that allows you to control the playback of YouTube videos from an other window.

## Table of Contents
- [Installation](#installation)
- [Usage](#usage)
- [Developer Instructions](#developer-instructions)
- [Building the Application](#building-the-application)
- [License](#license)

## Installation

Clone the repository:
```bash
git clone https://github.com/yourusername/KaraTube.git
cd KaraTube
```

Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Set up your YouTube API token (see [Developer Instructions](#developer-instructions))
2. Run the application:
```bash
python server.py
```
3. Go to `http://localhost:8080` in your web browser.

## Developer Instructions

### Setting Up YouTube API

1. Go to the [Google Developers Console](https://console.developers.google.com/)
2. Create a new project
3. Enable the YouTube Data API v3
4. Create credentials (API Key)
5. Create a `.env` file in the root directory of the project
6. Add your YouTube API token to the `.env` file:
```
YOUTUBE_API_KEY=your_api_key_here
```

### Development Setup

Make sure you have all dependencies installed:
```bash
pip install -r requirements.txt
```

Run the development server:
```bash
python server.py
```

Navigate to the URL shown in the console (http://localhost:8080).

## Building the Application

To create a standalone executable:

```bash
pyinstaller server.spec
```

The executable will be available in the `dist` folder.

## License

[MIT](LICENSE)