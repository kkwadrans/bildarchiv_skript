#from faulthandler import disable
from faulthandler import disable
import tkinter as tk
from tkinter import DISABLED, Toplevel, messagebox, BooleanVar, filedialog as tkfd
import picture_test

source_folder = ""
is_running = False


def close_programm():
    msgbox = messagebox.askquestion("Programm beenden", "Programm wirklich beenden?")
    if msgbox == "yes":
        root.destroy()

def open_log_settings_window():
    log_settings_window = Toplevel(root)
    log_settings_window.title("Log-Datein")
    log_settings_window.grab_set()
    log_settings_window.wm_attributes("-topmost", 1)

    lsw_label_error_path = tk.Label(log_settings_window, text="Datei-Pfad der Fehler-Logdatei:\n"+picture_test.error_log)
    lsw_label_error_path.grid(row=0, column=0, pady=10, padx=10)

    lsw_label_duplicates_path = tk.Label(log_settings_window, text="Datei-Pfad der Duplikaten-Logdatei:\n"+picture_test.duplicates_log)
    lsw_label_duplicates_path.grid(row=1, column=0, pady=10, padx=10)

    #log_settings_window_test_btn = tk.Button(log_settings_window, text="Test", command=select_source_folder)
    #log_settings_window_test_btn.grid(row=2, column=0)

def append_text_in_textbox(additional_text: str, with_timestamp = False):
    additional_text = f"{additional_text}\n"
    if with_timestamp:
        additional_text = f"{picture_test.make_timestamp('time')} : {additional_text}"
    text_box_info.insert(tk.END, additional_text)

def select_source_folder():
    global source_folder
    source_folder = tkfd.askdirectory()
    label_source_path.config(text = source_folder)
    picture_test.file_counter = 0
    picture_test.check_file_count(source_folder, True)
    label_input_files_number.config(text=f"{picture_test.file_counter}")

def write_result_in_textbox():
    text_box_info.config(state="normal")
    text_box_info.delete(1.0, tk.END)
    append_text_in_textbox("----- START! -----",True)
    list_result = picture_test.start_test(source_folder)
    text_box_info.tag_config("OK",background="#CCFFCC")
    text_box_info.tag_config("KAPUTT",background="#FFCCCC")
    for list_entry in list_result:
        if "ist OK!" in list_entry:
            text_box_info.insert(tk.END, f"{list_entry}\n", "OK")
        elif "ist kaputt" in list_entry:
            text_box_info.insert(tk.END, f"{list_entry}\n", "KAPUTT")
        elif "ist 0 bit groß" in list_entry:
            text_box_info.insert(tk.END, f"{list_entry}\n", "KAPUTT")
        elif "ist trunkiert" in list_entry:
            text_box_info.insert(tk.END, f"{list_entry}\n", "KAPUTT")
        else:
            append_text_in_textbox(f"{list_entry}")
    append_text_in_textbox("----- STOP! -----",True)
    text_box_info.config(state="disabled")

def show_file_count_result_on_gui():
    label_result_files_ok_number.config(text=f"{picture_test.files_ok}")
    file_errors = picture_test.corrupted_files + picture_test.hash_errors
    label_result_corrupted_files_number.config(text=f"{file_errors}")
    label_result_duplicates_number.config(text=f"{picture_test.duplicated_files}")

def press_start():
    global is_running
    if is_running == False:
        is_running = True
        if source_folder == "":
            msgbox = messagebox.showinfo("Kein Ordnerpfad", "Es wurde kein Ordner ausgewählt!")
            is_running = False
        elif check_file_error.get() == False and check_duplicates.get() == False:
            msgbox = messagebox.showinfo("Keine Datenprüfung", "Es wurde keine Prüfoption ausgewählt!")
            is_running = False
        else:
            picture_test.check_for_errors_is_selected = check_file_error.get()
            picture_test.check_for_duplicates_is_selected = check_duplicates.get()
            button_control_start.config(text="STOP")
            picture_test.reset_stats()
                            #TODO Prüf-Funktionen in eigenen Prozess auslagern
            write_result_in_textbox()
            show_file_count_result_on_gui()
            button_control_start.config(text="START")
            is_running = False
    else:
        pass

root = tk.Tk()
root.title("Datei prüfen")

root.protocol("WM_DELETE_WINDOW", close_programm)

check_file_error = BooleanVar()
check_duplicates = BooleanVar()

label_source_path = tk.Label(root, text="- kein Quell-Ordner gewählt -")
label_source_path.grid(row=0, column=0, columnspan=3)


# +++ MENUBAR +++
menubar = tk.Menu(root)

menu_bar = tk.Menu(menubar)
menu_bar.add_command(label="Speicherort Log-Dateien", command=open_log_settings_window)
menu_bar.add_command(label="Beenden", command=close_programm)

menubar.add_cascade(label="Menü", menu=menu_bar)

root.config(menu=menubar)


# +++ CONTROL +++
frame_control = tk.LabelFrame(root)
frame_control.grid(row=1, column=0, sticky=tk.N)

label_control = tk.Label(frame_control, text="Einstellungen", bg="#bbbbbb", height=3, width=30)
label_control.grid(row=0, column=0, columnspan=2)

button_select_source_folder = tk.Button(frame_control, text="Quellordner wählen", command=select_source_folder)
button_select_source_folder.grid(row=1, column=0, columnspan=2, pady=8)

# - left frame -
frame_control_left = tk.Frame(frame_control)
frame_control_left.grid(row=2, column=0)

label_control_select_find_duplicates = tk.Label(frame_control_left, text="Duplikate finden: ")
label_control_select_find_duplicates.grid()

label_control_select_file_test = tk.Label(frame_control_left, text="Datei überprüfen: ")
label_control_select_file_test.grid()

# - right frame -
frame_control_right = tk.Frame(frame_control)
frame_control_right.grid(row=2, column=1)

checkbutton_control_select_find_duplicates = tk.Checkbutton(frame_control_right, variable=check_duplicates)
checkbutton_control_select_find_duplicates.grid()

checkbutton_control_select_file_test = tk.Checkbutton(frame_control_right, variable=check_file_error)
checkbutton_control_select_file_test.grid()


# +++ BUTTONS +++
button_control_start = tk.Button(root, text="START", command=press_start, font=("arial", 14), height=2, width=14)
button_control_start.grid(row=2, column=0, pady=8, sticky=tk.S)


# +++ INPUT +++
frame_input = tk.LabelFrame(root)
frame_input.grid(row=1, column=2, sticky=tk.N + tk.S)

label_input = tk.Label(frame_input, text="Quell-Datein", bg="#bbbbbb", height=3, width=30)
label_input.grid(row=0, column=0, columnspan=2)

label_input_files = tk.Label(frame_input, text="Datein im Quell-Ordner: ")
label_input_files.grid(row=1, column=0)

label_input_files_number = tk.Label(frame_input, text="0")
label_input_files_number.grid(row=1, column=1)


# +++ RESULT +++
frame_result = tk.LabelFrame(root)
frame_result.grid(row=2, column=2, sticky=tk.N + tk.S)

label_result = tk.Label(frame_result, text="Ergebnis", bg="#bbbbbb", height=3, width=30)
label_result.grid(row=0, column=0, columnspan=2)

# - left frame -
frame_result_left = tk.Frame(frame_result)
frame_result_left.grid(row=1, column=0)

label_result_files_ok = tk.Label(frame_result_left, text="Dateien in Ordnung: ")
label_result_files_ok.grid()

#label_result_hash_test = tk.Label(frame_result_left, text="Hash-Test gescheitert: ")
#label_result_hash_test.grid()

label_result_corrupted_files = tk.Label(frame_result_left, text="Dateien nicht lesbar: ")
label_result_corrupted_files.grid()

label_result_duplicates = tk.Label(frame_result_left, text="Duplikate gefunden: ")
label_result_duplicates.grid()

# - right frame -
frame_result_right = tk.Frame(frame_result)
frame_result_right.grid(row=1, column=1)

label_result_files_ok_number = tk.Label(frame_result_right, text="0")
label_result_files_ok_number.grid()

#label_result_hash_test_number = tk.Label(frame_result_right, text="0")
#label_result_hash_test_number.grid()

label_result_corrupted_files_number = tk.Label(frame_result_right, text="0")
label_result_corrupted_files_number.grid()

label_result_duplicates_number = tk.Label(frame_result_right, text="0")
label_result_duplicates_number.grid()


# +++ INFO +++
frame_info = tk.LabelFrame(root)
frame_info.grid(row=1, column=1, rowspan=2, sticky=tk.N)

scroll_info = tk.Scrollbar(frame_info, orient="vertical")

text_box_info = tk.Text(frame_info, yscrollcommand=scroll_info.set, height=40, width=140, state="disabled")
text_box_info.grid(row=0, column=0)

scroll_info.config(command=text_box_info.yview)
scroll_info.grid(row=0, column=1, sticky=tk.N + tk.S)

root.mainloop()
