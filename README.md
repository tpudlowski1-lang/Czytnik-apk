# Czytnik APK — instrukcja

## Struktura projektu
```
czytnik-apk/
├── main.py              ← główna aplikacja
├── buildozer.spec       ← konfiguracja kompilacji
├── README.md
└── .github/
    └── workflows/
        └── build.yml    ← automatyczna kompilacja APK
```

## Krok po kroku

### 1. Utwórz nowe repozytorium na GitHub
- Wejdź na github.com
- Kliknij **New repository**
- Nazwa: `czytnik-apk`
- Ustaw jako **Public**
- Kliknij **Create repository**

### 2. Wgraj pliki
- Kliknij **uploading an existing file**
- Wgraj wszystkie pliki z tego folderu
- WAŻNE: folder `.github/workflows/build.yml` musi zachować strukturę

### 3. Uruchom kompilację
- Wejdź w zakładkę **Actions**
- Kliknij **Build APK** → **Run workflow**
- Kompilacja trwa ~20-40 minut

### 4. Pobierz APK
- Po zakończeniu kliknij w wynik buildu
- Na dole strony znajdź **Artifacts**
- Pobierz `czytnik-apk.zip`
- Rozpakuj → znajdziesz plik `.apk`

### 5. Zainstaluj na telefonie
- Prześlij `.apk` na telefon (email, Google Drive, USB)
- Na telefonie: Ustawienia → Bezpieczeństwo → **Zezwól na instalację z nieznanych źródeł**
- Otwórz plik `.apk` i zainstaluj

## Funkcje aplikacji
- Wczytywanie PDF, EPUB, TXT
- 6 lektorów (Zofia, Marek PL + EN/DE/FR)
- Regulacja prędkości czytania
- Działa bez komputera PC
- TTS przez edge-tts (wymaga internetu)
