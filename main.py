import tkinter as tk
import picture_test
import os
from tkinter import CENTER, DISABLED, N, Toplevel, messagebox, BooleanVar, filedialog as tkfd
from queue import Queue
from threading import Thread

# Bild prüfung
# https://pypi.org/project/ImageLite/0.1/#description

# Multithreading
# https://noisefloor-net.blogspot.com/2017/12/tkinter-und-threads.html

#print(frame_result.winfo_reqwidth())   # frame-breite auslesen
#print(len(lsw_label_error_path.cget("text")))  # label-text auslesen

MAX_LOG_PATH_WIDTH = 28

class DafenGui(tk.Frame):
    def __init__(self, text_box_queue, master = None):
        super().__init__(master)
        self.master.protocol("WM_DELETE_WINDOW", self.close_programm)
        if os.name == "nt":
            self.os_path_splitter = "\\"
        else:
            self.os_path_splitter = "/" 
        self.source_folder = ""
        self.is_running = False
        self.check_file_error = BooleanVar()
        self.check_duplicates = BooleanVar()
        self.new_error_log_path = ""
        self.new_duplicates_log_path = ""
        self.infobox_queue = text_box_queue
        self.get_splited_log_paths()
        self.create_widgets()

    def close_programm(self):
        msgbox = messagebox.askquestion("Programm beenden", "Dafen22 wirklich beenden?")
        if msgbox == "yes":
            picture_test.continue_work = False
            self.master.destroy()

    def get_queue_content(self):
        if self.t1.is_alive() or not picture_test.infobox_queue.empty():
            if picture_test.infobox_queue.qsize() > 100:
                queue_read_speed = 5
            elif picture_test.infobox_queue.qsize() > 50:
                queue_read_speed = 10
            elif picture_test.infobox_queue.qsize() > 10:
                queue_read_speed = 15
            elif picture_test.infobox_queue.qsize() > 5:
                queue_read_speed = 30
            elif picture_test.infobox_queue.qsize() > 2:
                queue_read_speed = 50
            else:
                queue_read_speed = 100
            self.master.after(queue_read_speed, self.get_queue_content)
            #print(picture_test.infobox_queue.qsize())
            while not picture_test.infobox_queue.empty():
                self.text_box_info.tag_config("OK",background="#88FFAA")
                self.text_box_info.tag_config("NOIMAGE",background="#FFFFAA")
                self.text_box_info.tag_config("BROKEN",background="#FFAAAA")
                self.text_box_info.tag_config("DUPLICATE",background="#DDDDFF")
                queue_entry = picture_test.infobox_queue.get()
                if "ist OK!" in queue_entry:
                    self.text_box_info.insert(tk.END, f"{queue_entry}\n", "OK")
                elif "ist keine Bild-Datei" in queue_entry:
                    self.text_box_info.insert(tk.END, f"{queue_entry}\n", "NOIMAGE")
                elif "ist kaputt" in queue_entry:
                    self.text_box_info.insert(tk.END, f"{queue_entry}\n", "BROKEN")
                elif "ist 0 bit groß" in queue_entry:
                    self.text_box_info.insert(tk.END, f"{queue_entry}\n", "BROKEN")
                elif "ist trunkiert" in queue_entry:
                    self.text_box_info.insert(tk.END, f"{queue_entry}\n", "BROKEN")
                elif "------------------------" in queue_entry:
                    self.text_box_info.insert(tk.END, f"{queue_entry}\n", "DUPLICATE")
                else:
                    self.append_text_in_textbox(f"{queue_entry}")

                self.label_result_files_ok_number.config(text=picture_test.files_ok)
                self.label_result_no_image_file_number.config(text=picture_test.no_image_files)
                self.label_result_corrupted_files_number.config(text=(picture_test.corrupted_files + picture_test.hash_errors))

                #self.label_result_files_ok_number.config(text=picture_test.files_ok_queue.get())
                #self.label_result_no_image_file_number.config(text=picture_test.no_image_files_queue.get())
                #self.label_result_corrupted_files_number.config(text=picture_test.corrupted_files_queue.get())
                #self.append_text_in_textbox(picture_test.infobox_queue.get(), False)
        else:
            self.label_result_duplicates_number.config(text=f"{picture_test.duplicated_files}")
            self.append_text_in_textbox("----- FERTIG! -----",True)
            self.text_box_info.config(state="disabled")
            self.is_running = False

    def split_log_file_path_label(self, log_path):
        self.log_splitlist = log_path.split(self.os_path_splitter)
        self.log_splitlist.pop(0)
        self.new_log_path:str = ""
        self.new_log_path_current_row_length = 0

        for i in self.log_splitlist:
            if (self.new_log_path_current_row_length + len(i)) <= MAX_LOG_PATH_WIDTH:
                self.new_log_path_current_row_length += len(i)
                self.new_log_path += self.os_path_splitter
                self.new_log_path += i
            else:
                self.new_log_path_current_row_length = len(i)
                self.new_log_path += self.os_path_splitter + "\n"
                self.new_log_path += i
        return self.new_log_path

    def get_splited_log_paths(self):
        self.new_error_log_path = self.split_log_file_path_label(os.getcwd() + self.os_path_splitter + picture_test.error_log)
        self.new_duplicates_log_path = self.split_log_file_path_label(os.getcwd() + self.os_path_splitter + picture_test.duplicates_log)

    def double_click_log(self, event, log_file):
        self.log_show_window = Toplevel(self)
        self.log_show_window.title(log_file)
        self.log_show_window.rowconfigure(0, weight=1)
        self.log_show_window.columnconfigure(0, weight=1)
        
        self.scroll_log = tk.Scrollbar(self.log_show_window, orient="vertical")
        self.textbox_log = tk.Text(self.log_show_window, yscrollcommand=self.scroll_log.set, height=40, width=140, state="normal")
        self.textbox_log.grid(sticky=tk.N + tk.E + tk.S + tk.W)
        self.scroll_log.config(command=self.textbox_log.yview)
        self.scroll_log.grid(row=0, column=1, sticky=tk.N + tk.S)
        self.log_file_text = open(log_file, "r")
        self.textbox_log.insert(tk.END, self.log_file_text.read())
        self.textbox_log.config(state="disabled")
        self.textbox_log.rowconfigure(0, weight=1)
        self.textbox_log.columnconfigure(0, weight=1)

    def append_text_in_textbox(self, additional_text: str, with_timestamp = False):
        self.additional_text = f"{additional_text}\n"
        if with_timestamp:
            self.additional_text = f"{picture_test.make_timestamp('time')} : {self.additional_text}"
        self.text_box_info.insert(tk.END, self.additional_text)

    def select_source_folder(self):
        self.selected_folder = str(tkfd.askdirectory())
        if self.selected_folder != "":
            self.source_folder = self.selected_folder
            self.label_source_path.config(text = self.source_folder)
            picture_test.file_counter = 0
            picture_test.check_file_count(self.source_folder, True)
            self.label_input_files_number.config(text=f"{picture_test.file_counter}")

    def write_result_in_textbox(self):
        self.text_box_info.config(state="normal")
        self.text_box_info.delete(1.0, tk.END)
        self.append_text_in_textbox("----- START! -----",True)

        self.t1 = Thread(target=picture_test.start_test, args=(self.source_folder,))
        self.t1.start()
        self.get_queue_content()

        #self.list_result = picture_test.start_test(self.source_folder)
        #self.text_box_info.tag_config("OK",background="#CCFFCC")
        #self.text_box_info.tag_config("KAPUTT",background="#FFCCCC")
        #self.text_box_info.tag_config("DUPLICATE",background="#DDDDFF")
        #for list_entry in self.list_result:
        #    if "ist OK!" in list_entry:
        #        self.text_box_info.insert(tk.END, f"{list_entry}\n", "OK")
        #    elif "ist kaputt" in list_entry:
        #        self.text_box_info.insert(tk.END, f"{list_entry}\n", "KAPUTT")
        #    elif "ist 0 bit groß" in list_entry:
        #        self.text_box_info.insert(tk.END, f"{list_entry}\n", "KAPUTT")
        #    elif "ist trunkiert" in list_entry:
        #        self.text_box_info.insert(tk.END, f"{list_entry}\n", "KAPUTT")
        #    elif "------------------------" in list_entry:
        #        self.text_box_info.insert(tk.END, f"{list_entry}\n", "DUPLICATE")
        #    else:
        #        self.append_text_in_textbox(f"{list_entry}")
        #self.append_text_in_textbox("----- FERTIG! -----",True)
        #self.text_box_info.config(state="disabled")
        #self.is_running = False

    def show_duplicates_count(self):
        #self.label_result_files_ok_number.config(text=f"{picture_test.files_ok}")
        #self.label_result_no_image_file_number.config(text=f"{picture_test.no_image_files}")
        #self.file_errors = picture_test.corrupted_files + picture_test.hash_errors
        #self.label_result_corrupted_files_number.config(text=f"{self.file_errors}")
        self.label_result_duplicates_number.config(text=f"{picture_test.duplicated_files}")

    def press_start(self):
        if self.is_running == False:
            self.is_running = True
            if self.source_folder == "":
                msgbox = messagebox.showinfo("Kein Ordnerpfad", "Es wurde kein Ordner ausgewählt!")
                self.is_running = False
            elif self.check_file_error.get() == False and self.check_duplicates.get() == False:
                msgbox = messagebox.showinfo("Keine Datenprüfung", "Es wurde keine Prüfoption ausgewählt!")
                self.is_running = False
            else:
                picture_test.check_for_errors_is_selected = self.check_file_error.get()
                picture_test.check_for_duplicates_is_selected = self.check_duplicates.get()
                picture_test.continue_work = True
                picture_test.reset_stats()
                self.button_control_start.config(text="STOP")
                self.write_result_in_textbox()
                self.show_duplicates_count()
                self.button_control_start.config(text="START")
        else:
            picture_test.continue_work = False
            self.button_control_start.config(text="START")
            self.is_running = False

    def create_widgets(self):
        self.label_source_path = tk.Label(self.master, text="- kein Quell-Ordner gewählt -")
        self.label_source_path.grid(row=0, column=0, columnspan=3)

        # +++ CONTROL +++
        self.frame_control = tk.LabelFrame(self.master)
        self.frame_control.grid(row=1, column=0, sticky=tk.N)

        self.label_control = tk.Label(self.frame_control, text="Einstellungen", bg="#bbbbbb", height=3, width=30)
        self.label_control.grid(row=0, column=0, columnspan=2)

        self.button_select_source_folder = tk.Button(self.frame_control, text="Quellordner wählen", command=self.select_source_folder)
        self.button_select_source_folder.grid(row=1, column=0, columnspan=2, pady=8)

        # - left frame -
        self.frame_control_left = tk.Frame(self.frame_control)
        self.frame_control_left.grid(row=2, column=0)

        self.label_control_select_find_duplicates = tk.Label(self.frame_control_left, text="Duplikate finden: ")
        self.label_control_select_find_duplicates.grid()

        self.label_control_select_file_test = tk.Label(self.frame_control_left, text="Datei überprüfen: ")
        self.label_control_select_file_test.grid()

        # - right frame -
        self.frame_control_right = tk.Frame(self.frame_control)
        self.frame_control_right.grid(row=2, column=1)

        self.checkbutton_control_select_find_duplicates = tk.Checkbutton(self.frame_control_right, variable=self.check_duplicates)
        self.checkbutton_control_select_find_duplicates.grid()

        self.checkbutton_control_select_file_test = tk.Checkbutton(self.frame_control_right, variable=self.check_file_error)
        self.checkbutton_control_select_file_test.grid()


        # +++ BUTTONS +++
        self.button_control_start = tk.Button(self.master, text="START", command=self.press_start, font=("arial", 14), height=2, width=14)
        self.button_control_start.grid(row=3, column=0, pady=8, sticky=tk.S)


        # +++ INPUT +++
        self.frame_input = tk.LabelFrame(self.master)
        self.frame_input.grid(row=1, column=2, sticky=tk.N + tk.S)

        self.label_input = tk.Label(self.frame_input, text="Quell-Dateien", bg="#bbbbbb", height=3, width=30)
        self.label_input.grid(row=0, column=0, columnspan=2)

        self.label_input_files = tk.Label(self.frame_input, text="Dateien im Quell-Ordner: ")
        self.label_input_files.grid(row=1, column=0)

        self.label_input_files_number = tk.Label(self.frame_input, text="0")
        self.label_input_files_number.grid(row=1, column=1)


        # +++ RESULT +++
        self.frame_result = tk.LabelFrame(self.master)
        self.frame_result.grid(row=2, column=2, sticky=tk.N + tk.S)

        self.label_result = tk.Label(self.frame_result, text="Ergebnis", bg="#bbbbbb", height=3, width=30)
        self.label_result.grid(row=0, column=0, columnspan=2)

        # - left frame -
        self.frame_result_left = tk.Frame(self.frame_result)
        self.frame_result_left.grid(row=1, column=0)

        self.label_result_files_ok = tk.Label(self.frame_result_left, text="Dateien in Ordnung: ")
        self.label_result_files_ok.grid()

        self.label_result_no_image_file = tk.Label(self.frame_result_left, text="Keine Bild-Dateien: ")
        self.label_result_no_image_file.grid()

        self.label_result_corrupted_files = tk.Label(self.frame_result_left, text="Dateien nicht lesbar: ")
        self.label_result_corrupted_files.grid()

        self.label_result_duplicates = tk.Label(self.frame_result_left, text="Duplikate gefunden: ")
        self.label_result_duplicates.grid()

        # - right frame -
        self.frame_result_right = tk.Frame(self.frame_result)
        self.frame_result_right.grid(row=1, column=1)

        self.label_result_files_ok_number = tk.Label(self.frame_result_right, text="0")
        self.label_result_files_ok_number.grid()

        self.label_result_no_image_file_number = tk.Label(self.frame_result_right, text="0")
        self.label_result_no_image_file_number.grid()

        self.label_result_corrupted_files_number = tk.Label(self.frame_result_right, text="0")
        self.label_result_corrupted_files_number.grid()

        self.label_result_duplicates_number = tk.Label(self.frame_result_right, text="0")
        self.label_result_duplicates_number.grid()


        # +++ LOG +++
        self.frame_log = tk.LabelFrame(self.master)
        self.frame_log.grid(row=3, column=2, sticky=tk.N + tk.S + tk.E + tk.W)
        self.frame_log.rowconfigure(0, weight=1)
        self.frame_log.columnconfigure(0, weight=1)

        self.label_log = tk.Label(self.frame_log, text="Log-Datein", bg="#bbbbbb", height=3, width=30)
        self.label_log.grid(row=0, column=0, sticky=tk.N)

        self.lsw_label_error_path = tk.Label(self.frame_log, text="Datei-Pfad der Fehler-Logdatei:\n" + self.new_error_log_path, fg="blue")
        self.lsw_label_error_path.grid(row=1, column=0, pady=10, padx=2)
        self.lsw_label_error_path.bind('<Double-1>', lambda event, log_file=picture_test.error_log: self.double_click_log(event, log_file))

        self.lsw_label_duplicates_path = tk.Label(self.frame_log, text="Datei-Pfad der Duplikaten-Logdatei:\n" + self.new_duplicates_log_path, fg="blue")
        self.lsw_label_duplicates_path.grid(row=2, column=0, pady=10, padx=2)
        self.lsw_label_duplicates_path.bind('<Double-1>', lambda event, log_file=picture_test.duplicates_log: self.double_click_log(event, log_file))

        # TEST --------------------------------------------
        #def test(event):
        #    print(f"X: {event.x} - Y: {event.y}  {text_box_info.mark_set('insert', '%d.%d' % (event.x,event.y))}")
        #    
        #def check_pos(event):
        #    print(text_box_info.index(tk.INSERT))
        #    zeile = text_box_info.index(tk.INSERT)
        #    zeile = zeile.split(".")[0]
        #    if zeile.find(":"):
        #        print(zeile.find("home"))
        #        print(text_box_info.get(zeile + ".0", zeile + ".end"))

        #--------------------------------------------------

        # +++ INFO +++
        self.frame_info = tk.LabelFrame(self.master)
        self.frame_info.grid(row=1, column=1, rowspan=3, sticky=tk.N)

        self.scroll_info = tk.Scrollbar(self.frame_info, orient="vertical")

        self.text_box_info = tk.Text(self.frame_info, yscrollcommand=self.scroll_info.set, height=50, width=140, state="disabled")
        self.text_box_info.grid(row=0, column=0)

        self.scroll_info.config(command=self.text_box_info.yview)
        self.scroll_info.grid(row=0, column=1, sticky=tk.N + tk.S)

        # TEST --------------------------------------------
        #text_box_info.bind('<Motion>',lambda event, : test(event))
        #text_box_info.bind("<Button-1>", check_pos)
        #--------------------------------------------------

# +++ RESIZE +++
#root.rowconfigure(0, weight=1)
#root.columnconfigure(0, weight=1)

def main():
    text_box_queue = Queue()

    root = tk.Tk()
    app = DafenGui(text_box_queue, master = root)
    app.master.title("Dafen22")
    
    app.mainloop()

main()

#label_source_path.rowconfigure(1, weight=1)
#label_source_path.columnconfigure(1, weight=1)

"""
# +++ MENUBAR +++
menubar = tk.Menu(root)

menu_bar = tk.Menu(menubar)
menu_bar.add_command(label="Speicherort Log-Dateien", command=open_log_settings_window)
menu_bar.add_command(label="Beenden", command=close_programm)

menubar.add_cascade(label="Menü", menu=menu_bar)

root.config(menu=menubar)
"""

