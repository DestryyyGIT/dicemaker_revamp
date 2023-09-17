# dicemaker_revamp

## Welcome to Cube Maker Unofficial v1.6!

Hey everyone! I'd like to share with you my progress on updating Cube Maker to be more user friendly, have more features, and generally provide a better time for generating dice. This **Python** script currently only works with **BlueStacks** and contains the following new features:
- Slightly refactored codebase with improvements to thread handling
- UI Improvements
- Dice Count Tracker
- Earned Dice Tracker
- Control over the buffer period (for those with potato PC's or NASA rigs)
- Live milestone bar tracker
- 'Close Tabs' Feature for Lightning Browser 

The script also already assumes it's in the C:\platform-tools:\ directory alongside your ADB files. 
*Please see here ([▶ dice.exe setup (figma.com)](https://www.figma.com/proto/2d3icPqyv5V8ow4EWgOmvl/Untitled?type=design&node-id=124-84&t=oXRlJ0X4ydqPNtpJ-0&scaling=min-zoom&page-id=0%3A1) for help on getting the ADB folder set up in the right spot alongside your system's environment variables if you haven't already.* 

Let me know if you guys encounter any bugs, it's definitely still far from perfect. I will not be incorporating compatibility with other emulators, but I welcome somebody else to take on the challenge!

How To Run:
- Download EXE (This will likely trigger anti-virus. This application does not need admin rights to run; however, it does conduct port scanning (through adb), it does create/terminate subprocesses and threads, and due to the nature of wrapping it using PyInstaller, files may be created in a temp folder that the Python dependencies need. The source code is uploaded here and transparent. 
Relevant VT Link: [VirusTotal - dicemaker1.2.exe](https://www.virustotal.com/gui/file/9ac17825685a508a7bc4f9da343c4895e8be5e865fe69a61e693c7b2a0f38b1c/detection). 

And for additional context, the original dice.exe also gets flagged as malware. [VirusTotal - Dice.exe](https://www.virustotal.com/gui/file/e3cb7800f4fc723cff0a1136be7d352b71882d48a7fb741d06141a317cbfbe8b/behavior)
- With Python IDLE, just edit the file in IDLE and click F5.
- With CMD, navigate to the platform-tools directory and type *'python dicemaker1.2.py'*

**Be mindful that dice generators will not work on your account if you have accessed Monopoly Go after version 1.11.0.**

![Image](https://i.imgur.com/6hRqf9x.png)

v1.6 Changelog:
- Added 'Close Tabs' Feature for Lightning Browser

v1.4 Changelog:
- Initial Release

Known Bugs:
- ~~Earned dice count may not update properly after hitting the reset button~~ Fixed!
- Earned Dice/Total Dice does not consider multiple links being entered
