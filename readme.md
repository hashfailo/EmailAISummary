# Email Digest Bot

An automated email digest system that summarizes unread emails using AI.

## Features

- Processes unread Gmail messages
- Creates AI-powered summaries using Hugging Face API
- Handles both plain text and HTML emails
- Sends formatted digest emails

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file with:
   ```
   EMAIL_USERNAME=your.email@gmail.com
   EMAIL_PASSWORD=your-app-specific-password
   HG_TOKEN=your-huggingface-token
   ```

## Usage

```bash
python emailDigestBot.py
```

## Requirements

- Python 3.x
- Gmail account with IMAP enabled
- Hugging Face API token

## License

MIT
