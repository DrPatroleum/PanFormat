# 🗑️ Pan Format

**Pan Format** to darmowe narzędzie dla systemu Windows do bezpiecznego i nieodwracalnego czyszczenia nośników danych (pendrive'ów, dysków zewnętrznych, kart SD).

Program najpierw **formatuje zawartość dysku** (usuwa wszystkie pliki), a następnie **wielokrotnie nadpisuje wolne miejsce losowymi danymi**, uniemożliwiając odzyskanie jakichkolwiek informacji przez osoby trzecie.

---

## 📸 Funkcje

- ✅ Dwuetapowe czyszczenie: formatowanie → nadpisywanie
- ✅ Wybór liczby przebiegów: **1×, 3×, 5×, 7× (DoD 5220.22-M)**
- ✅ Szacowany czas operacji wyświetlany **przed** uruchomieniem
- ✅ Dwa paski postępu: bieżący przebieg + postęp całkowity
- ✅ Możliwość anulowania w dowolnym momencie
- ✅ Zabezpieczenie przed przypadkowym nadpisaniem dysku systemowego (C:)
- ✅ Obsługa błędów: brak uprawnień, błędy I/O
- ✅ Interfejs w języku polskim

---

## 💻 Wymagania

- System Windows 7 / 10 / 11
- Python 3.8+ *(tylko jeśli uruchamiasz z kodu źródłowego)*

---

## 🚀 Instalacja i uruchomienie

### Opcja A — gotowy plik `.exe` *(zalecane)*

1. Pobierz najnowszą wersję z sekcji [**Releases**](../../releases)
2. Uruchom `Pan Format.exe` — brak instalacji, działa od razu

> ⚠️ Windows może wyświetlić ostrzeżenie SmartScreen przy pierwszym uruchomieniu (plik nie jest podpisany cyfrowo). Kliknij „Więcej informacji" → „Uruchom mimo to".

### Opcja B — uruchomienie z kodu źródłowego

```bash
# Sklonuj repozytorium
git clone https://github.com/TWOJ_LOGIN/pan-format.git
cd pan-format

# Uruchom program
python pan_format.py
```

Wymagane tylko standardowe biblioteki Pythona (`tkinter`, `os`, `shutil`, `threading`) — brak zewnętrznych zależności.

---

## 🔨 Budowanie pliku `.exe`

Aby samodzielnie zbudować plik wykonywalny:

1. Upewnij się, że masz zainstalowanego Pythona i pip
2. Umieść pliki `pan_format.py`, `icon.ico` oraz `build.bat` w jednym folderze
3. Uruchom `build.bat` — skrypt automatycznie zainstaluje PyInstaller i zbuduje `Pan Format.exe`

Gotowy plik znajdziesz w folderze `dist\`.

---

## 📖 Jak używać

1. **Wybierz dysk** z listy rozwijanej (widoczna pojemność w GB)
2. **Wybierz liczbę przebiegów** — obok każdej opcji widnieje szacowany czas dla wybranego dysku:

| Tryb | Przebiegi | Zastosowanie |
|------|-----------|--------------|
| Szybkie | 1× | Zwykłe dane, szybkie czyszczenie |
| Standardowe | 3× | Zalecane — dobry kompromis |
| Bezpieczne | 5× | Wrażliwe dane osobowe |
| DoD 5220.22-M | 7× | Standard wojskowy USA |

3. Kliknij **„Rozpocznij czyszczenie"** i potwierdź operację
4. Program wykona dwa kroki:
   - **① Formatowanie** — usuwa wszystkie pliki z dysku
   - **② Nadpisywanie** — wypełnia wolne miejsce losowymi danymi (wielokrotnie)

> ⏱️ Szacunki czasu zakładają prędkość zapisu ~20 MB/s (typowy pendrive USB 2.0). Szybsze nośniki (USB 3.x, SSD) będą działać znacznie krócej.

---

## ⚠️ Ostrzeżenia

- **Operacja jest nieodwracalna.** Po zakończeniu odzyskanie danych jest praktycznie niemożliwe.
- Program **nie pozwala** wybrać dysku systemowego (zazwyczaj C:) jako zabezpieczenie przed przypadkowym usunięciem systemu.
- Zalecane uruchomienie **jako Administrator** (prawy przycisk → „Uruchom jako administrator"), szczególnie przy czyszczeniu dysków z zabezpieczonymi plikami.

---

## 📄 Licencja

Projekt udostępniony na licencji [MIT](LICENSE).

---

## 🤝 Współpraca

Pull requesty i zgłoszenia błędów są mile widziane! Jeśli napotkasz problem, otwórz [issue](../../issues).
