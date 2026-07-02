# 📸 Utilitar Screenshoturi

A Windows utility written in Python for capturing screenshots during software testing.

Designed primarily for documenting a specific app's workflow, but can be configured to capture any application window.

---

# Features

## 🖥 Capture screenshots

- Capture the **left monitor**
- Capture the **right monitor**
- Capture a specific application window
- Global hotkey (**Win + Alt + Z**) for window capture
  - Useful for capturing menus or dropdowns that disappear when switching windows

---

## 📂 Automatic folder structure

Screenshots are automatically organized as:

```
Work Directory/
└── RC/
    └── SCI/
        ├── Step1/
        │   ├── step1.png
        │   ├── step1.2.png
        │   └── step1.3.png
        │
        ├── Step2/
        │   ├── step2.png
        │   └── step2.2.png
        │
        └── ...
```

or (if *Create Step Folder* is disabled)

```
Work Directory/
└── RC/
    └── SCI/
        ├── step1.png
        ├── step1.2.png
        ├── step2.png
        └── ...
```

---

# Automatic filename numbering

The application automatically handles numbering.

Example:

```
step1.png
step1.1.png
step1.2.png
step1.3.png
```

It even renames the first screenshot automatically when additional screenshots are taken.

---

# Image browser

The integrated image browser provides:

- thumbnail gallery
- image preview
- click to open image
- delete image (Recycle Bin)
- automatic refresh
- highlighted selected image thumbnail

---

# Screenshot log

Every captured image appears in a log.

Each entry contains:

- 📁 button to open Explorer
- selectable full path
- automatic scrolling
- refresh capability

---

# ZIP creation

Create a ZIP archive containing the complete SCI folder.

Generated filename:

```
SCI-0123-RC_NAME.zip
```

Perfect for sending documentation to colleagues.

---

# Window capture

Instead of capturing the entire monitor, the utility can capture only a specific application window.

Features:

- partial window title matching
- automatic maximize
- automatic foreground activation
- captures only the client area (no borders or title bar)


# Configuration

Settings are automatically saved in:

```
setari_utilitar_screenshoturi.json
```

Stored values include:

- working directory
- RC
- SCI
- current step
- auto increment option
- create step folder option
- filename delimiter
- recent window names
- image browser size and position

---

# Global Hotkey

```
Win + Alt + Z
```

Captures the configured application window even if another application is active.

This is especially useful when documenting software that uses temporary popup menus.

---

# Automatic refresh

The application automatically refreshes:

- screenshot log
- image browser
- thumbnail gallery

Missing files are detected automatically.

---

# Safety features

- Single application instance
- Invalid filename sanitization
- Automatic folder creation
- Error handling
- Informative dialogs
- Recycle Bin support (instead of permanent deletion)

---

# Requirements

Python 3.12+

Required packages:

```
pip install pillow
pip install mss
pip install pywin32
pip install send2trash
```

---

# Building

The project uses **Nuitka**.

Example build command:

```bash
python -m nuitka ^
--standalone ^
--remove-output ^
--include-data-files="camera_gear2.ico=camera_gear2.ico" ^
--enable-plugin=tk-inter ^
--windows-disable-console ^
--windows-icon-from-ico="camera_gear2.ico" ^
--product-version="0.2" ^
--product-name="Utilitar Screenshoturi" ^
--company-name="AndreiP" ^
--output-filename="Utilitar_screenshoturi.exe" ^
Utilitar_screenshoturi.py
```

---

# Dependencies

- tkinter
- Pillow
- mss
- pywin32
- send2trash

---

# Project structure

```
Utilitar_screenshoturi.py
camera_gear2.ico
setari_utilitar_screenshoturi.json
README.md
```

---

# Typical workflow

1. Enter **RC**
2. Enter **SCI**
3. Select current step
4. Capture screenshots
5. Review images
6. Delete unwanted screenshots
7. Refresh if necessary
8. Create ZIP archive
9. Send ZIP

---

# Possible future improvements:

- Drag & drop image reordering
- Automatic Image renaming if one is deleted from a suite of images
- Clipboard copy
- OCR
- Annotation tools ???
- Multiple capture profiles ???

---

# License

##This project is intended for internal software testing and documentation purposes.

# Descriere scurtă a capabilităților
- Capturează ecranul stâng, ecranul drept sau o fereastră dorită
- Salvează imaginile în foldere structurate: work_dir\RC\SCI\STEP_X\step_X_1.
- Suport pentru incrementare automată a numărului de pas după salvare.
- Permite setarea RC, SCI, step și directorului de lucru din interfața GUI.
- Salvează setările în fișierul setari_utilitar_screenshoturi.json.
- Are hotkey global Win+Alt+U pentru captură rapidă ca sa nu dispara droddown-urile de la app
- Afișează un log cu căi către imaginile salvate, cu butoane pentru a deschide locația în Explorer.
- Permite crearea unui fișier ZIP din conținutul folderului SCI, cu nume generat automat.
- Suportă o listă de nume de ferestre pentru captură, cu istoric în dropdown și validare după titlu parțial.
- Gestionează erorile și oferă mesaje informative utilizatorului.
- Asigură că doar o singură instanță a aplicației rulează simultan.
- Permite setarea unui delimitator personalizat între numărul pasului și indexul fotografiei în numele fișierelor (implicit ".") pentru compatibilitate cu diferite convenții de denumire.
- Fereastră separată dedicată vizualizării rapide a screenshoturilor.
- Posibilitate de ștergere a screenshoturilor (din bara de thumbnailuri).
- Previzualizare a thumburilor.
- Deschiderea imaginilor cu app setată ca default în Windows.


# Brief Description of Capabilities
- Captures the left screen, right screen, or an app's window.
- Saves images in a structured folder hierarchy: work_dir\RC\SCI\STEP_X\step_X_1.
- Supports automatic incrementing of the step number after each save.
- Allows configuring the RC, SCI, step number, and working directory through the GUI.
- Saves settings to the setari_utilitar_screenshoturi.json configuration file.
- Provides a global Win+Alt+U hotkey for quick screenshots, preventing SCDX dropdown menus from disappearing.
- Displays a log containing the paths of saved images, with buttons to open their locations in Windows  Explorer.
- Allows creating a ZIP archive from the contents of the SCI folder, with an automatically generated filename.
- Supports a list of window names for capture, including dropdown history and validation based on partial window titles.
- Handles errors gracefully and provides informative messages to the user.
- Ensures that only a single instance of the application can run at a time.
- Allows configuring a custom delimiter between the step number and the image index in filenames (default: ".") to support different naming conventions.
- Separate window dedicated to quick screenshot viewing.
- Ability to delete screenshots directly from the thumbnail bar.
- Thumbnail preview for all captured screenshots.
- Open screenshots using the default image viewer configured in Windows.