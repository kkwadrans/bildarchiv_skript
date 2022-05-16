import config
from queue import Queue
import os
import hashlib
from PIL import Image, UnidentifiedImageError
from time import strftime
import traceback

error_log = config.file_error_log
duplicates_log = config.file_duplicates_log
continue_work = False

check_for_errors_is_selected = False
check_for_duplicates_is_selected = False
file_counter = 0
files_ok = 0
no_image_files = 0
hash_errors = 0
corrupted_files = 0
duplicated_files = 0
duplicate_file_names = {}
last_checked_file = ""
start_scan_at_file = ""

infobox_queue = Queue()
files_ok_queue = Queue()
no_image_files_queue = Queue()
corrupted_files_queue = Queue()

def reset_stats():
    global file_counter
    global files_ok
    global no_image_files
    global hash_errors
    global corrupted_files
    global duplicated_files
    global duplicate_file_names

    file_counter = 0
    files_ok = 0
    no_image_files = 0
    hash_errors = 0
    corrupted_files = 0
    duplicated_files = 0
    duplicate_file_names.clear()

def make_timestamp(style:str):
    if style == "date":
        return strftime('%d.%m.%Y')
    elif style == "time":
        return strftime('%H:%M:%S')
    elif style == "all":
        return strftime('%d.%m.%Y, %H:%M:%S')

def handleError(e):
    #print("!",e)
    #traceback.print_exc() #print stack trace
    #with open("errors.log","a") as logfile:
    with open(error_log,"a") as logfile:
        logfile.write(f"{make_timestamp('time')} : {str(e)}\n")

def check_file_count(source_folder, with_subfolders = True):
    global file_counter
    for filename in os.listdir(source_folder):
        file_path = os.path.join(source_folder,filename)
        if os.path.isdir(file_path):
            if with_subfolders:
                check_file_count(file_path, True)
        else:
            file_counter += 1

def start_test(source_folder):
    global continue_work
    global start_scan_at_file
    if check_for_errors_is_selected:
        if start_scan_at_file == "":
            with open(error_log,"a") as logfile:
                logfile.write(f"\n ----- {make_timestamp('date')} ----- \nQuell-Ordner:   {source_folder}\n------------------------------\n")
        else:
            with open(error_log,"a") as logfile:
                logfile.write(f"\n ----- Fortsetzung der Suche: {make_timestamp('date')} ----- \n------------------------------\n")
    scan_source_folder(source_folder)
    if continue_work:
        if check_for_errors_is_selected:
            if hash_errors == 0 and corrupted_files == 0:
                with open(error_log,"a") as logfile:
                    logfile.write(f"Keine Fehler gefunden!\n")
        if check_for_duplicates_is_selected:
            if check_for_errors_is_selected:
                infobox_queue.put("\n\n\n")
                #result_list.append("\n\n\n")
            search_duplicates(source_folder)
    else:
        save_progress()

def save_progress():
    save_data = "Letzte Datei:\n"
    save_data += last_checked_file
    save_data += "\nDateien im Verzeichnis:\n"
    save_data += str(file_counter)
    save_data += "\nDateien OK:\n"
    save_data += str(files_ok)
    save_data += "\nDateien kein Bild\n"
    save_data += str(no_image_files)
    save_data += "\nKaputte Dateien:\n"
    save_data += str(corrupted_files)
    save_data += "\nHash Fehler:\n"
    save_data += str(hash_errors)
    save_data += "\nDuplikate:\n"
    for key, values in duplicate_file_names.items():
        save_data += key + "\n"
        for value in values:
            save_data += value + "\n"
        save_data += "\n"
    with open("continue.txt","w") as savefile:
        savefile.write(save_data)

def load_progress():
    pass

def scan_source_folder(source_folder):
    global files_ok
    global no_image_files
    global check_for_errors_is_selected
    global check_for_duplicates_is_selected
    global continue_work
    global last_checked_file
    global start_scan_at_file
    for filename in os.listdir(source_folder):
        if continue_work:
            file_path = os.path.join(source_folder,filename)
            last_checked_file = file_path
            if os.path.isdir(file_path):
                scan_source_folder(file_path)
            else:
                if start_scan_at_file != "" and start_scan_at_file != file_path:
                    print(f"conti: {file_path}")
                    continue
                if start_scan_at_file != "":
                    start_scan_at_file = ""
                if check_for_errors_is_selected:
                    if check_file_extension(file_path):
                        try:
                            get_hash_value(file_path)
                            check_if_image_is_broken(file_path)
                            infobox_queue.put(f"{make_timestamp('time')} : {file_path} ist OK!")
                            #list_result.append(f"{make_timestamp('time')} : {file_path} ist OK!")
                            files_ok += 1
                            files_ok_queue.put(f"{files_ok}")
                        except (UnidentifiedImageError) as e:
                            infobox_queue.put(f"{make_timestamp('time')} : {e}")
                            #list_result.append(f"{make_timestamp('time')} : {e}")
                            handleError(e)
                        except (OSError) as e:
                            infobox_queue.put(f"{make_timestamp('time')} : {e}")
                            #list_result.append(f"{make_timestamp('time')} : {e}")
                            handleError(e)
                    else:
                            no_image_files += 1
                            no_image_files_queue.put(no_image_files)
                            infobox_queue.put(f"{make_timestamp('time')} : {file_path} ist keine Bild-Datei")
                            with open(error_log,"a") as logfile:
                                logfile.write(f"{make_timestamp('time')} : {file_path} ist keine Bild-Datei\n")
                if check_for_duplicates_is_selected:
                        fill_filelist_for_duplicates(filename, file_path)
        else:
            break

def check_file_extension(file_path):
    return file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.tif', '.tiff', '.bmp', '.gif'))

def get_hash_value(file_path): #compute checksum. here 'truncated image' exception (OS error) can occure
    try:
        global hash_errors
        image = Image.open(file_path)
        return hashlib.md5(image.tobytes()).hexdigest()
    except (OSError):
        hash_errors += 1
        corrupted_files_queue.put(hash_errors + corrupted_files)
        raise OSError(f"{file_path} ist kaputt oder kein Bild.")
        #raise OSError(f"{file_path} ist kaputt oder kein Bild.\n{str(e)}")

def check_if_image_is_broken(file_path):
    try:
        global corrupted_files
        statfile = os.stat(file_path)
        filesize = statfile.st_size
        if filesize == 0:
            raise UnidentifiedImageError(f"{file_path} ist 0 bit groß")
        img = Image.open(file_path) # open the image file
        img.verify() # verify that it is an image that can be opened
        img.close()
        img = Image.open(file_path) 
        img.transpose(Image.FLIP_LEFT_RIGHT) #check for truncated image
        img.close()
    except (UnidentifiedImageError):
        corrupted_files += 1
        corrupted_files_queue.put(hash_errors + corrupted_files)
        raise UnidentifiedImageError (f"{file_path} ist kaputt")
    except (OSError):
        corrupted_files += 1
        corrupted_files_queue.put(hash_errors + corrupted_files)
        raise OSError (f"{file_path} ist trunkiert")

def fill_filelist_for_duplicates(filename, file_path):
    global duplicate_file_names
    if  not os.path.isdir(filename):
        id = filename.split(".")[0]
        if id in duplicate_file_names.keys():
            duplicate_file_names[id].append(file_path)
        else:
            duplicate_file_names[id] = [file_path]

def search_duplicates(source_folder):
    global duplicated_files
    duplicate_search_result = check_for_duplicated_files()
    duplicates = f"---------------------------------  {make_timestamp('all')}  --------------------------------- \nQuell-Ordner:   {source_folder}\n------------------------------------------------------------------------------------------\nGefundene Duplikate: {duplicated_files}"
    duplicates += duplicate_search_result
    infobox_queue.put(duplicates)
    #result_list.append(duplicates)
    duplicates += "\n\n\n\n"
    save_duplicates_log(duplicates)

def check_for_duplicated_files():
    global duplicated_files
    search_result = ""
    for key, values in duplicate_file_names.items():
        if len(values) > 1:
            search_result += (f"\n\nDateiname: {key}\n")
            duplicated_files += 1
            i = 1
            for value in values:
                if i > 1:
                    search_result += (f"\n")
                i += 1
                search_result += (f"{value}")
    if search_result == "":
        search_result += " \nKeine"
    return search_result

def save_duplicates_log(duplicates):
     with open(duplicates_log,"a") as logfile:
        logfile.write(f"{duplicates}")