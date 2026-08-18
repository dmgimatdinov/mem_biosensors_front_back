# Memristive Biosensors Portable Edition

## Description

This package gives you a portable desktop version of the Memristive Biosensors Passport Manager. It runs locally on Windows 10/11 without installing Python, Node.js, Docker, or Chrome.

## System requirements

- Windows 10 or 11 (64-bit)
- 4 GB RAM
- 1 GB free disk space

## Installation

1. Extract the ZIP archive into any folder on your computer.
2. Open the extracted folder.
3. Double-click the file named mem_biosensors.exe.

## First launch

The application starts a local server on http://127.0.0.1:8000.

Default login:
- Username: admin
- Password: admin

Please change the administrator password immediately after the first sign-in.

## Folder structure

- data/ - local SQLite database and JWT secret
- logs/ - application logs
- frontend/ - bundled static web assets
- README.txt - this guide
- start.bat - alternative launcher
- stop.bat - stop the running server
- UNINSTALL.bat - remove local data and launcher

## Data storage

All user data and the SQLite database are stored in the data/ folder. This folder is preserved between launches.

## Backup

Copy the data/ folder to create a backup.

## Uninstall

Run UNINSTALL.bat to remove the local data and launcher files.

## Troubleshooting

- If Windows Defender blocks the app, add the extraction folder to the antivirus exclusions.
- If port 8000 is busy, the launcher automatically tries the next free port.
- If the browser does not open, open http://127.0.0.1:8000 manually.

## Download latest release

Download the latest portable build from the GitHub Releases page for this repository. The artifact is named:

- MemBiosensors_Portable_v{version}_win-x64.zip

## Verify checksum

After downloading the archive, verify the SHA256 checksum using:

- sha256sum MemBiosensors_Portable_v{version}_win-x64.zip

Compare it with the checksum published in the release assets.

## Support

Contact the project maintainer for help with portable builds.
