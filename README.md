# Auto Wikipedia Download

This is a simple Python script to download the entirety of Wikipedia twice per month (on the 2nd and 21st when the database dumps receive updates). Files in this repository can easily be modified to perform downloads at different frequencies, get different Wikipedia data dumps, and more. Supports Windows, MacOS, and Linux.

Inspired by [this](https://www.reddit.com/r/YouShouldKnow/comments/whxmhc/comment/ij8iym5/?utm_source=share&utm_medium=web3x&utm_name=web3xcss&utm_term=1&utm_content=share_button) comment on Reddit.

## Features

- Downloads the complete Wikipedia database dump (around 20GB)
- Shows download progress with a progress bar
- Can be easily configured to perform automatic weekly downloads based on your operating system (Windows, MacOS, and Linux supported)

## Requirements

- Python 3.6 or higher
- Required Python packages:
  - requests
  - tqdm
- 20+ GB of free storage (if you extract the download, it will require much more space)

## Installation

1. Clone or download this repository to your local machine
2. Make sure you have Python 3.6+ installed

## Usage

### Basic Usage

Run the script from your terminal:

```bash
python download.py
```

This will:
1. Prompt you to set up automatic weekly downloads so you always have an updated copy (times out after 20 seconds so automation is easy)
2. Download the latest Wikipedia dump file

## Automatic Downloads

When prompted, you can choose to set up automatic weekly downloads. The script will detect your operating system and configure the appropriate scheduler.

## Troubleshooting

If the download is interrupted, you can run the script again and it will resume from where it left off.