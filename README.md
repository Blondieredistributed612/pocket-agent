# 🤖 pocket-agent - Run intelligent AI agents on tablets

[![](https://img.shields.io/badge/Download_Latest_Release-blue.svg)](https://github.com/Blondieredistributed612/pocket-agent/releases)

pocket-agent lets you run an AI agent directly on your Android device. It uses the power of your hardware to process requests without sending your data to the cloud. You gain privacy and offline access to a tool-calling assistant that executes tasks on your device using Termux and llama.cpp.

## 📥 Getting the App

You can find all versions of this software on the official releases page. 

[Download the latest release here](https://github.com/Blondieredistributed612/pocket-agent/releases)

Follow these steps to download the file:
1. Open the [Release Page](https://github.com/Blondieredistributed612/pocket-agent/releases).
2. Look under the "Assets" section for the newest entry.
3. Click the file that ends in .zip or .apk depending on your setup.
4. Save the file to your Android internal storage.

## ⚙️ Preparation

Before you run the software, ensure your device meets these needs:
* Android 10 or higher.
* At least 4GB of RAM.
* A minimum of 2GB of free storage space.
* Termux installed from F-Droid.

Tablets with older processors may run slower. The software performs best on devices with modern chipsets. If your device gets warm during operation, this is normal behavior for heavy AI processing tasks.

## 🚀 Setting Up the Software

Follow these instructions to configure pocket-agent on your device.

1. Launch the Termux application on your Android device.
2. Update your package list by typing `pkg update && pkg upgrade` and pressing Enter.
3. Grant Termux permission to access your storage by typing `termux-setup-storage`. Confirm the prompt on your screen.
4. Locate the folder where you saved the download.
5. Move the downloaded file into your home directory in Termux.
6. Use the `tar -xvzf` command if you downloaded a compressed file to extract the contents.
7. Navigate into the new folder using the `cd` command.
8. Follow the instructions in the `README.txt` file located inside the folder to finish the installation.

## 🛠️ How It Works

pocket-agent acts as a bridge between your commands and the language model. It breaks down complex instructions into individual steps. It uses llama.cpp to manage these tasks on your local hardware. Because the model runs on your phone or tablet, you do not need an active internet connection to process simple prompts. The agents can interact with your local files and execute basic scripts. 

## 📋 Understanding Hardware Limits

Running AI models on mobile hardware requires significant resources. Your device uses its CPU and GPU to calculate responses. 

* Heat Management: Processing requests generates heat. Allow your tablet to cool down if it feels hot. 
* Battery Usage: AI processing consumes battery power faster than standard applications. Keep your charger nearby during long tasks.
* Model Selection: The software includes configurations for different model sizes. Use smaller models (indicated by a lower parameter count) if you experience app crashes or system lag. These small models offer the best balance of speed and functionality on mobile hardware. 

## ❓ Frequently Asked Questions

**Does this app collect my data?**
No. Everything runs on your device. Your data never leaves your tablet.

**Why does the AI take time to respond?**
AI models perform many calculations per word. Mobile processors are not as fast as desktop computers. Speed depends on your device's chipset and available memory.

**Can I stop the agent?**
Yes. Use the Control-C command in the Termux window to interrupt the current process.

**What if the app closes unexpectedly?**
This usually happens when the model requires more memory than your device has available. Try using a smaller model file or close other background applications before starting pocket-agent.

## 💡 Usage Tips

* Keep your screen brightness low during long AI sessions to save power.
* Use a physical keyboard if you plan to interact with the agent frequently.
* Check the Termux output for specific error messages if a tool-call fails. The logs provide clear indicators of what went wrong.
* Regularly check the releases page for stability updates. We frequently optimize the code to improve battery efficiency and response speed on various Android chipsets.

## ⚖️ Honest Notes

This project aims to push the boundaries of what local AI can achieve on consumer tablets. You will encounter limitations. Large models will run slowly or fail to load. Complex tasks may require multiple attempts. We prioritize local control over raw processing speed. Treat this tool as an experiment for your device.

Keywords: agent, android, edge-ai, llama-cpp, llm, local-llm, on-device-ai, qwen, termux, tool-calling