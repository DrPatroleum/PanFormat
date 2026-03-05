import os
import sys
import string
import shutil
import threading
import tkinter as tk
from tkinter import ttk, messagebox

CHUNK = 4 * 1024 * 1024
APP_NAME = "Pan Format"

# Szacunkowa prędkość zapisu w MB/s (konserwatywna, dla pendrive'ów)
WRITE_SPEED_MBS = 20

cancel_flag = threading.Event()


def resource_path(relative_path):
    """Zwraca ścieżkę do zasobu — działa zarówno z .py jak i z .exe (PyInstaller)."""
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)


# ── Helpers ────────────────────────────────────────────────────────────────────

def get_drives():
    drives = []
    for d in string.ascii_uppercase:
        path = f"{d}:\\"
        if os.path.exists(path):
            try:
                total, used, free = shutil.disk_usage(path)
                size_gb = total / (1024 ** 3)
                drives.append(f"{d}: ({size_gb:.1f} GB)")
            except Exception:
                drives.append(f"{d}:")
    return drives


def get_drive_letter(combo_value):
    return combo_value[0] if combo_value else ""


def format_bytes(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def format_time(seconds):
    seconds = int(seconds)
    if seconds < 60:
        return f"~{seconds} sek."
    elif seconds < 3600:
        m, s = divmod(seconds, 60)
        return f"~{m} min {s:02d} sek."
    else:
        h, rem = divmod(seconds, 3600)
        m = rem // 60
        return f"~{h} godz. {m:02d} min"


def estimate_time(free_bytes, passes):
    total_mb = (free_bytes * passes) / (1024 * 1024)
    seconds = total_mb / WRITE_SPEED_MBS
    return format_time(seconds)


# ── Logika główna ──────────────────────────────────────────────────────────────

def on_drive_selected(event=None):
    drive_value = combo.get()
    if not drive_value:
        return
    drive_letter = get_drive_letter(drive_value)
    drive_path = f"{drive_letter}:\\"
    try:
        total, used, free = shutil.disk_usage(drive_path)
        label_disk_info.config(
            text=f"Pojemność: {format_bytes(total)}   "
                 f"Zajęte: {format_bytes(used)}   "
                 f"Wolne: {format_bytes(free)}"
        )
        for passes, lbl in time_labels.items():
            est = estimate_time(free, passes)
            lbl.config(text=est)
    except Exception:
        label_disk_info.config(text="Nie można odczytać informacji o dysku.")


def wipe():
    drive_value = combo.get()
    if not drive_value:
        messagebox.showerror("Błąd", "Wybierz dysk!")
        return

    drive_letter = get_drive_letter(drive_value)
    drive_path = f"{drive_letter}:\\"

    system_drive = os.environ.get("SystemDrive", "C:")[0].upper()
    if drive_letter.upper() == system_drive:
        messagebox.showerror(
            "Błąd",
            f"Dysk {drive_letter}: to dysk systemowy!\nNie można go nadpisać."
        )
        return

    passes = passes_var.get()
    if passes == 0:
        messagebox.showerror("Błąd", "Wybierz liczbę przebiegów!")
        return

    try:
        total, used, free = shutil.disk_usage(drive_path)
    except Exception as e:
        messagebox.showerror("Błąd", f"Nie można odczytać dysku:\n{e}")
        return

    est = estimate_time(free, passes)
    confirm = messagebox.askyesno(
        "Potwierdzenie operacji",
        f"UWAGA: Operacja jest nieodwracalna!\n\n"
        f"Dysk:                    {drive_letter}:\n"
        f"Pojemność:               {format_bytes(total)}\n"
        f"Do wyczyszczenia:        {format_bytes(free)}\n\n"
        f"Krok 1: Formatowanie (usunięcie plików)\n"
        f"Krok 2: Nadpisywanie losowymi danymi  x{passes}\n"
        f"Szacowany czas łączny:   {est}\n\n"
        "Czy chcesz kontynuować?"
    )
    if not confirm:
        return

    cancel_flag.clear()
    button_wipe.config(state="disabled")
    button_cancel.config(state="normal")
    combo.config(state="disabled")
    for rb in pass_radios:
        rb.config(state="disabled")

    thread = threading.Thread(
        target=wipe_thread, args=(drive_letter, free, passes), daemon=True
    )
    thread.start()


def wipe_thread(drive_letter, free_size, passes):
    drive_path = f"{drive_letter}:\\"

    # ── KROK 1: Formatowanie ──────────────────────────────────────────────────
    root.after(0, lambda: _set_step(1))
    root.after(0, lambda: label_pass.config(text="Formatowanie dysku — usuwanie plików..."))
    root.after(0, lambda: label_status.config(text="⏳ Formatowanie...", foreground="blue"))

    try:
        deleted = 0
        for root_dir, dirs, files in os.walk(drive_path, topdown=False):
            for fname in files:
                if cancel_flag.is_set():
                    break
                fpath = os.path.join(root_dir, fname)
                try:
                    os.remove(fpath)
                    deleted += 1
                    root.after(0, lambda d=deleted: label_pass.config(
                        text=f"Formatowanie — usunięto {d} plików..."
                    ))
                except Exception:
                    pass
            for dname in dirs:
                if cancel_flag.is_set():
                    break
                dpath = os.path.join(root_dir, dname)
                try:
                    shutil.rmtree(dpath, ignore_errors=True)
                except Exception:
                    pass
            if cancel_flag.is_set():
                break

        if cancel_flag.is_set():
            root.after(0, lambda: label_status.config(text="⚠ Anulowano", foreground="orange"))
            root.after(0, reset_ui)
            return

        root.after(0, lambda d=deleted: label_pass.config(
            text=f"Formatowanie zakończone — usunięto {d} plików"
        ))

        try:
            _, _, free_size = shutil.disk_usage(drive_path)
        except Exception:
            pass

    except Exception as e:
        root.after(0, lambda e=e: messagebox.showerror("Błąd formatowania", str(e)))
        root.after(0, lambda: label_status.config(text="✘ Błąd", foreground="red"))
        root.after(0, reset_ui)
        return

    # ── KROK 2: Nadpisywanie ─────────────────────────────────────────────────
    root.after(0, lambda: _set_step(2))
    root.after(0, lambda: label_status.config(text="⏳ Nadpisywanie...", foreground="blue"))

    path = f"{drive_letter}:\\wipe_temp.bin"
    total_bytes = free_size * passes
    total_written = 0

    try:
        for p in range(1, passes + 1):
            if cancel_flag.is_set():
                break

            root.after(0, lambda p=p: label_pass.config(
                text=f"Przebieg {p} / {passes} — zapis losowych danych"
            ))
            written = 0

            with open(path, "wb") as f:
                while written < free_size:
                    if cancel_flag.is_set():
                        break

                    block = min(CHUNK, free_size - written)
                    f.write(os.urandom(block))
                    written += block
                    total_written += block

                    pass_pct = written / free_size * 100
                    total_pct = total_written / total_bytes * 100
                    written_str = format_bytes(written)
                    size_str = format_bytes(free_size)
                    total_str = format_bytes(total_written)
                    total_size_str = format_bytes(total_bytes)

                    root.after(0, lambda pp=pass_pct, tp=total_pct,
                               ws=written_str, ss=size_str,
                               ts=total_str, tss=total_size_str: (
                        progress_pass.config(value=pp),
                        progress_total.config(value=tp),
                        label_progress.config(
                            text=f"Przebieg: {ws} / {ss}   |   Łącznie: {ts} / {tss}  ({tp:.1f}%)"
                        )
                    ))

            if os.path.exists(path):
                with open(path, "r+b") as f:
                    f.seek(0)
                    f.write(b'\x00' * min(CHUNK, free_size))
                    f.flush()
                    os.fsync(f.fileno())

        if cancel_flag.is_set():
            root.after(0, lambda: label_status.config(text="⚠ Anulowano", foreground="orange"))
        else:
            root.after(0, lambda: label_status.config(text="✔ Gotowe!", foreground="green"))
            root.after(0, lambda: label_pass.config(text="Wszystkie operacje zakończone pomyślnie."))
            root.after(0, lambda: progress_total.config(value=100))

    except PermissionError:
        root.after(0, lambda: messagebox.showerror(
            "Błąd uprawnień",
            "Brak uprawnień do zapisu na tym dysku.\nUruchom program jako Administrator."
        ))
        root.after(0, lambda: label_status.config(text="✘ Błąd uprawnień", foreground="red"))
    except OSError as e:
        root.after(0, lambda e=e: messagebox.showerror("Błąd", f"Błąd zapisu:\n{e}"))
        root.after(0, lambda: label_status.config(text="✘ Błąd", foreground="red"))
    finally:
        if os.path.exists(path):
            try:
                os.remove(path)
            except Exception:
                pass
        root.after(0, reset_ui)


def _set_step(step):
    for i, lbl in step_labels.items():
        if i == step:
            lbl.config(foreground="blue", font=("Segoe UI", 9, "bold"))
        elif i < step:
            lbl.config(foreground="green", font=("Segoe UI", 9))
        else:
            lbl.config(foreground="gray", font=("Segoe UI", 9))


def cancel_wipe():
    cancel_flag.set()
    label_status.config(text="Anulowanie...", foreground="orange")
    button_cancel.config(state="disabled")


def reset_ui():
    button_wipe.config(state="normal")
    button_cancel.config(state="disabled")
    combo.config(state="readonly")
    for rb in pass_radios:
        rb.config(state="normal")


# ── GUI ────────────────────────────────────────────────────────────────────────

root = tk.Tk()
root.title(APP_NAME)
root.resizable(False, False)

# Ikona w górnym pasku okna
try:
    icon_path = resource_path("icon.ico")
    root.iconbitmap(icon_path)
except Exception:
    pass

frame = ttk.Frame(root, padding=16)
frame.pack(fill="both", expand=True)

# Wybór dysku
ttk.Label(frame, text="1. Wybierz dysk:", font=("Segoe UI", 10, "bold")).pack(anchor="w")
combo = ttk.Combobox(frame, values=get_drives(), width=28, state="readonly")
combo.pack(pady=(2, 2), anchor="w")
combo.bind("<<ComboboxSelected>>", on_drive_selected)

label_disk_info = ttk.Label(frame, text="Wybierz dysk, aby zobaczyć szczegóły.",
                             foreground="gray", font=("Segoe UI", 8))
label_disk_info.pack(anchor="w", pady=(0, 10))

ttk.Separator(frame, orient="horizontal").pack(fill="x", pady=6)

# Wybór liczby przebiegów
ttk.Label(frame, text="2. Wybierz liczbę przebiegów nadpisywania:",
          font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 4))

passes_var = tk.IntVar(value=3)
pass_radios = []
time_labels = {}

PASS_OPTIONS = [
    (1,  "Szybkie  (1×) ",  "podstawowe, dla zwykłych danych"),
    (3,  "Standardowe (3×) ", "zalecane — dobry kompromis"),
    (5,  "Bezpieczne (5×) ", "dla wrażliwych danych"),
    (7,  "DoD 5220.22-M (7×) ", "standard wojskowy USA"),
]

passes_frame = ttk.Frame(frame)
passes_frame.pack(fill="x", pady=(0, 4))

for passes, label_text, desc in PASS_OPTIONS:
    row = ttk.Frame(passes_frame)
    row.pack(fill="x", pady=2)

    rb = ttk.Radiobutton(row, text=label_text, variable=passes_var, value=passes)
    rb.pack(side="left")
    pass_radios.append(rb)

    ttk.Label(row, text=desc, foreground="gray", font=("Segoe UI", 8)).pack(side="left")

    time_lbl = ttk.Label(row, text="— wybierz dysk —", foreground="#999",
                         font=("Segoe UI", 8, "italic"), width=18, anchor="e")
    time_lbl.pack(side="right")
    time_labels[passes] = time_lbl

ttk.Label(passes_frame,
          text="Szacunki czasu zakładają ~20 MB/s (typowy pendrive). "
               "Dyski SSD będą znacznie szybsze.",
          foreground="gray", font=("Segoe UI", 7, "italic")).pack(anchor="e")

ttk.Separator(frame, orient="horizontal").pack(fill="x", pady=6)

# Kroki
ttk.Label(frame, text="Kolejność operacji:", font=("Segoe UI", 9, "bold")).pack(anchor="w")
steps_frame = ttk.Frame(frame)
steps_frame.pack(fill="x", pady=(2, 8))

step_labels = {}
for i, text in {
    1: "① Formatowanie — usunięcie wszystkich plików z dysku",
    2: "② Nadpisywanie — wielokrotny zapis losowych danych",
}.items():
    lbl = ttk.Label(steps_frame, text=text, foreground="gray", font=("Segoe UI", 9))
    lbl.pack(anchor="w")
    step_labels[i] = lbl

ttk.Separator(frame, orient="horizontal").pack(fill="x", pady=6)

# Przyciski
btn_frame = ttk.Frame(frame)
btn_frame.pack(fill="x", pady=(0, 10))

button_wipe = ttk.Button(btn_frame, text="▶  Rozpocznij czyszczenie", command=wipe)
button_wipe.pack(side="left", padx=(0, 8))

button_cancel = ttk.Button(btn_frame, text="✖  Anuluj", command=cancel_wipe, state="disabled")
button_cancel.pack(side="left")

ttk.Separator(frame, orient="horizontal").pack(fill="x", pady=6)

# Postęp
label_pass = ttk.Label(frame, text="Oczekiwanie na start...", font=("Segoe UI", 9))
label_pass.pack(anchor="w")

ttk.Label(frame, text="Postęp bieżącego przebiegu:",
          font=("Segoe UI", 8), foreground="gray").pack(anchor="w", pady=(4, 0))
progress_pass = ttk.Progressbar(frame, length=420, mode="determinate")
progress_pass.pack(fill="x", pady=(2, 6))

ttk.Label(frame, text="Postęp całkowity:",
          font=("Segoe UI", 8), foreground="gray").pack(anchor="w")
progress_total = ttk.Progressbar(frame, length=420, mode="determinate")
progress_total.pack(fill="x", pady=(2, 4))

label_progress = ttk.Label(frame, text="", font=("Segoe UI", 8))
label_progress.pack(anchor="w")

ttk.Separator(frame, orient="horizontal").pack(fill="x", pady=8)

label_status = ttk.Label(frame, text="Gotowy do pracy.", font=("Segoe UI", 10, "bold"))
label_status.pack(anchor="w")

root.mainloop()
