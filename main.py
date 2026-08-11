#!/usr/bin/env python3

r"""
comanda de creare executabil cu nuitka:

de aici am aflat:
https://dev.to/weisshufer/from-pyinstaller-to-nuitka-convert-python-to-exe-without-false-positives-19jf

python -m nuitka --standalone --onefile --enable-plugin=tk-inter --windows-disable-console captare_ecran_teste.py
--windows-disable-console = e deprecated dar pe py 3.14 si nuitka 4.1.2 merge,
                            varianta moderna cu --windows-disable-console=disabled da eroare


comanda de creare cu nume diferit: (atentie trebuie adaugat pyton.exe la exceptii la windows defender)
python -m nuitka --standalone --onefile --enable-plugin=tk-inter --windows-disable-console --product-name="Utilitar_screenshoturi" --product-version="0.1" --output-filename="Utilitar_screenshoturi.exe" captare_ecran_teste.py

comanda de creare cu pyinstaller:
pyinstaller --onefile --windowed --name "Utilitar_Screenshoturi" captare_ecran_teste.py

***ultima folosita:
comanda finala de creare a executabilului cu nuitka, cu iconita personalizata, versiune produs, nume produs, companie, si includerea icoanei in date files ca sa fie disponibila la runtime pentru setarea iconitei ferestrei (altfel icoana e doar pentru fisierul EXE dar fereastra are iconita default python):

    --include-data-files="resources\icons\camera_gear2.ico=camera_gear2.ico" `

python -m nuitka `
    --standalone `
    --remove-output `
    --windows-disable-console `
    --include-data-dir=resources=resources `
    --enable-plugin=tk-inter `
    --windows-icon-from-ico="C:\Liamis_testing\scripturi\utilitar_screenshoturi\resources\icons\camera_gear2.ico" `
    --product-version="0.4" `
    --product-name="Utilitar Screenshoturi" `
    --output-filename="Utilitar_screenshoturi.exe" `
    --company-name="AndreiP" `
    main.py

Descriere scurtă a capabilităților
- Capturează ecranul stâng, ecranul drept sau o fereastră activă a SCDX (sau alta specificata)
- Salvează imaginile în foldere structurate: work_dir\RC\SCI\STEP_X\step_X_1.
- Suport pentru incrementare automată a numărului de pas după salvare.
- Permite setarea RC, SCI, step și directorului de lucru din interfața GUI.
- Salvează setările în fișierul setari_utilitar_screenshoturi.json.
- Are hotkey global Win+Alt+U pentru captură rapidă ca sa nu dispara droddown-urile de la SCDX
- Afișează un log cu căi către imaginile salvate, cu butoane pentru a deschide locația în Explorer.
- Permite crearea unui fișier ZIP din conținutul folderului SCI, cu nume generat automat.
- Suportă o listă de nume de ferestre pentru captură, cu istoric în dropdown și validare după titlu parțial.
- Gestionează erorile și oferă mesaje informative utilizatorului.
- Asigură că doar o singură instanță a aplicației rulează simultan.
- Permite setarea unui delimitator personalizat între numărul pasului și indexul fotografiei în numele fișierelor (implicit ".") pentru compatibilitate cu diferite convenții de denumire.
"""

import sys
import ctypes
import logging

from app import MyApp


logging.basicConfig(
        level=logging.DEBUG,
        format=(
            "<--bootstrap--> | %(levelname)-8s | %(name)s | "
            "%(filename)s:%(lineno)d | %(funcName)s() | %(message)s")
    )

logger = logging.getLogger("bootstrap")

MUTEX_NAME = "Singleton_Utilitar_Screenshoturi"

# chiar asta este eroarea din windows ....
ERROR_ALREADY_EXISTS = 183

mutex = ctypes.windll.kernel32.CreateMutexW( None, False, MUTEX_NAME, )

if ctypes.windll.kernel32.GetLastError() == ERROR_ALREADY_EXISTS:
    logger.info("Application is already running.")
    sys.exit(0)


def main():
    """Main entry point"""
    app = MyApp(logger)
    app.run()


if __name__ == "__main__":
    main()