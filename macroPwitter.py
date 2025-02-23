import tkinter as tk
import random
import pyautogui
import threading
import time
from pynput import mouse

# ----------------------------
# Calibration (pour cliquer hors de Tkinter)
# ----------------------------
calib_points = {}
calib_click_count = 0
calibration_done = False  # Flag indiquant si le calibrage est terminé

def calibrer_zones_thread():
    global calib_click_count, calib_points, calibration_done
    calib_click_count = 0
    calib_points = {}
    calibration_done = False
    # Mettre à jour l'interface depuis le thread principal
    root.after(0, lambda: instruction_label.config(text="Calibrage démarré : cliquez sur QRT, citer, poster."))
    print("Calibrage démarré : cliquez sur les zones QRT, citer et poster dans l'ordre souhaité.")

    def on_click(x, y, button, pressed):
        global calib_click_count, calib_points
        if pressed:
            calib_click_count += 1
            if calib_click_count == 1:
                calib_points["QRT"] = (x, y)
                root.after(0, lambda: instruction_label.config(text="Clic QRT enregistré. Cliquez sur citer."))
                print(f"Zone QRT calibrée à : {(x, y)}")
            elif calib_click_count == 2:
                calib_points["citer"] = (x, y)
                root.after(0, lambda: instruction_label.config(text="Clic citer enregistré. Cliquez sur poster."))
                print(f"Zone citer calibrée à : {(x, y)}")
            elif calib_click_count == 3:
                calib_points["poster"] = (x, y)
                root.after(0, lambda: instruction_label.config(text="Calibration terminée."))
                print(f"Zone poster calibrée à : {(x, y)}")
                return False  # Arrête le listener après le 3ème clic

    with mouse.Listener(on_click=on_click) as listener:
        listener.join()

    calibration_done = True
    print("Calibration terminée.")
    print("Coordonnées enregistrées :", calib_points)

def calibrer_zones():
    t = threading.Thread(target=calibrer_zones_thread, daemon=True)
    t.start()


# ----------------------------
# Gestion des phrases et compteurs
# ----------------------------
# Dictionnaire des phrases avec leur compteur
phrases = {
    "Feur": 0,
    "Bjr ca va": 0,
    "Les pessi dominent twitter": 0
}
# Dictionnaire des variables pour activer/désactiver chaque phrase
phrase_vars = {}
# Pour conserver les checkbuttons (pour mise à jour de leur texte)
phrase_checkbuttons = {}

def refresh_phrase_buttons():
    # Vider le cadre et recréer les checkbuttons
    for widget in frame_phrases.winfo_children():
        widget.destroy()
    for phrase, count in phrases.items():
        if phrase not in phrase_vars:
            phrase_vars[phrase] = tk.BooleanVar(value=True)
        text = f"{phrase} (RT {count} fois)"
        cb = tk.Checkbutton(frame_phrases, text=text, variable=phrase_vars[phrase])
        cb.pack(anchor="w")
        phrase_checkbuttons[phrase] = cb

def add_phrase():
    new_phrase = entry_new_phrase.get().strip()
    if new_phrase and new_phrase not in phrases:
        phrases[new_phrase] = 0
        phrase_vars[new_phrase] = tk.BooleanVar(value=True)
        refresh_phrase_buttons()
    entry_new_phrase.delete(0, tk.END)

# ----------------------------
# Lancement d'une citation (mise à jour du presse-papiers)
# ----------------------------
global_count = 0
last_chosen = None

def lancer_citation():
    global global_count, phrases, last_chosen

    # Vérification de la limite globale si activée
    if var_global_limit.get():
        try:
            global_lim = int(entry_global.get())
        except ValueError:
            print("Veuillez entrer un nombre pour la limite globale.")
            return
        if global_count >= global_lim:
            print("Limite globale atteinte.")
            return

    # Constitution de la liste des phrases disponibles en fonction de la limite locale et de la sélection
    available_phrases = []
    if var_local_limit.get():
        try:
            local_lim = int(entry_local.get())
        except ValueError:
            print("Veuillez entrer un nombre pour la limite locale.")
            return
        for phrase, count in phrases.items():
            if phrase_vars.get(phrase, tk.BooleanVar(value=False)).get() and count < local_lim:
                available_phrases.append(phrase)
    else:
        for phrase in phrases.keys():
            if phrase_vars.get(phrase, tk.BooleanVar(value=False)).get():
                available_phrases.append(phrase)

    if not available_phrases:
        print("Toutes les limites locales sont atteintes ou aucune phrase n'est sélectionnée.")
        return

    # Sélection de la phrase : mode Random ou toujours la même
    if var_random.get():
        chosen_phrase = random.choice(available_phrases)
        last_chosen = None
    else:
        if last_chosen is None:
            last_chosen = available_phrases[0]
        elif last_chosen not in available_phrases:
            print("La citation sélectionnée a atteint la limite locale ou a été désactivée.")
            return
        chosen_phrase = last_chosen

    # Construction du message
    if var_count.get():
        count = phrases[chosen_phrase]
        message = f"{chosen_phrase} {count+1}"
    else:
        message = chosen_phrase

    # Copier dans le presse-papiers
    root.clipboard_clear()
    root.clipboard_append(message)
    root.update()
    print("Message copié :", message)

    # Mise à jour des compteurs
    phrases[chosen_phrase] += 1
    global_count += 1
    refresh_phrase_buttons()

# ----------------------------
# Cycle d'automatisation
# ----------------------------
cycle_running = False
stop_cycle = False

def run_cycle():
    global cycle_running, stop_cycle, global_count, phrases
    cycle_running = True
    stop_cycle = False
    update_status_bar()  # Passe en vert dès le démarrage
    while not stop_cycle:
        lancer_citation()

        # Vérification des limites globales
        if var_global_limit.get():
            try:
                global_lim = int(entry_global.get())
            except ValueError:
                global_lim = None
            if global_lim is not None and global_count >= global_lim:
                print("Limite globale atteinte.")
                break

        # Vérification des limites locales : si aucune phrase n'est disponible, on arrête
        available_phrases = []
        if var_local_limit.get():
            try:
                local_lim = int(entry_local.get())
            except ValueError:
                local_lim = None
            for phrase, count in phrases.items():
                if phrase_vars.get(phrase, tk.BooleanVar(value=False)).get() and (local_lim is None or count < local_lim):
                    available_phrases.append(phrase)
        else:
            for phrase in phrases.keys():
                if phrase_vars.get(phrase, tk.BooleanVar(value=False)).get():
                    available_phrases.append(phrase)
        if not available_phrases:
            print("Toutes les limites locales sont atteintes ou aucune phrase n'est sélectionnée.")
            break

        # Simulation des clics et du Ctrl+V
        if "QRT" in calib_points:
            pyautogui.click(calib_points["QRT"][0], calib_points["QRT"][1])
        else:
            print("Coordonnées QRT non calibrées.")
            break
        time.sleep(0.4)

        if "citer" in calib_points:
            pyautogui.click(calib_points["citer"][0], calib_points["citer"][1])
        else:
            print("Coordonnées citer non calibrées.")
            break
        time.sleep(0.4)

        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.4)

        if "poster" in calib_points:
            pyautogui.click(calib_points["poster"][0], calib_points["poster"][1])
        else:
            print("Coordonnées poster non calibrées.")
            break

        # Délai aléatoire entre chaque cycle (entre 0.8 et 1.2 s)
        time.sleep(random.uniform(1.8, 2.2))
        update_status_bar()

    cycle_running = False
    update_status_bar()
    print("Cycle arrêté.")

def toggle_cycle(event):
    global cycle_running, stop_cycle
    if not calibration_done:
        print("Veuillez calibrer les zones avant de démarrer le cycle.")
        return
    if not cycle_running:
        print("Démarrage du cycle.")
        stop_cycle = False
        t = threading.Thread(target=run_cycle)
        t.daemon = True
        t.start()
    else:
        print("Arrêt du cycle.")
        stop_cycle = True

# ----------------------------
# Barre de statut
# ----------------------------
def update_status_bar():
    if cycle_running:
        root.after(0, lambda: status_label.config(bg="green", text=f"Collés: {global_count}"))
    else:
        root.after(0, lambda: status_label.config(bg="red", text="ESPACE pour commencer"))

# ----------------------------
# Interface Tkinter
# ----------------------------
root = tk.Tk()
root.title("Own sans difficulté")
root.geometry("500x700")

# --- Ajout d'une image en haut à droite ---
try:
    # Chargez l'image (assurez-vous que "logo.png" existe dans le répertoire)
    img = tk.PhotoImage(file="fallaitetudier.png")
    image_label = tk.Label(root, image=img)
    # Placez l'image en haut à droite (ancrée "ne" pour North East)
    image_label.place(relx=1.0, y=0, anchor="ne")
except Exception as e:
    print("Erreur lors du chargement de l'image :", e)

# Options
var_random = tk.BooleanVar(value=True)
var_count = tk.BooleanVar(value=True)
var_global_limit = tk.BooleanVar(value=False)
var_local_limit = tk.BooleanVar(value=False)

check_random = tk.Checkbutton(root, text="Random", variable=var_random)
check_random.pack(anchor="w", padx=10, pady=2)
check_count = tk.Checkbutton(root, text="Compter", variable=var_count)
check_count.pack(anchor="w", padx=10, pady=2)

check_global = tk.Checkbutton(root, text="Limite Globale", variable=var_global_limit)
check_global.pack(anchor="w", padx=10, pady=2)
entry_global = tk.Entry(root, width=10)
entry_global.pack(anchor="w", padx=20)
entry_global.insert(0, "10")

check_local = tk.Checkbutton(root, text="Limite Locale", variable=var_local_limit)
check_local.pack(anchor="w", padx=10, pady=2)
entry_local = tk.Entry(root, width=10)
entry_local.pack(anchor="w", padx=20)
entry_local.insert(0, "3")

# Bouton manuel pour lancer une citation
button_citation = tk.Button(root, text="Own moi", command=lancer_citation)
button_citation.pack(pady=10)

# Zone d'ajout et d'affichage des phrases
frame_phrases = tk.LabelFrame(root, text="Copié-collés disponibles")
frame_phrases.pack(fill="both", padx=10, pady=10, expand=True)

# Zone d'ajout d'une nouvelle phrase
frame_new = tk.Frame(root)
frame_new.pack(fill="x", padx=10, pady=5)
entry_new_phrase = tk.Entry(frame_new)
entry_new_phrase.pack(side="left", fill="x", expand=True, padx=(0, 5))
button_add = tk.Button(frame_new, text="Ajouter", command=add_phrase)
button_add.pack(side="left")
refresh_phrase_buttons()

# Bouton de calibration et label d'instructions
calib_button = tk.Button(root, text="Calibrer", command=calibrer_zones)
calib_button.pack(pady=5)
instruction_label = tk.Label(root, text="Appuyez sur 'Calibrer' pour calibrer les zones.", fg="blue")
instruction_label.pack(pady=5)

# Barre de statut
status_label = tk.Label(root, text="ESPACE pour commencer", bg="red", fg="white", font=("Helvetica", 16))
status_label.pack(fill="x", pady=10)

# Lier la barre espace pour démarrer/arrêter le cycle (active uniquement après calibrage)
root.bind("<space>", toggle_cycle)

root.mainloop()
