import config
from queue import Queue
import os
import hashlib
from PIL import Image, UnidentifiedImageError
from time import strftime
import traceback

error_log = config.file_error_log
duplicates_log = config.file_duplicates_log

check_for_errors_is_selected = False
check_for_duplicates_is_selected = False
file_counter = 0
files_ok = 0
no_image_files = 0
hash_errors = 0
corrupted_files = 0
duplicated_files = 0
duplicate_file_names = {}

infobox_queue = Queue()

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
        logfile.write(f"{make_timestamp('time')}: {str(e)}\n")

def check_file_count(source_folder, with_subfolders = True):
    global file_counter
    for filename in os.listdir(source_folder):
        file_path = os.path.join(source_folder,filename)
        if os.path.isdir(file_path):
            if with_subfolders:
                check_file_count(file_path, True)
        else:
            file_counter += 1

def start_test(source_folder):     # create_non_global_result_list
    result_list = []
    if check_for_errors_is_selected:
        with open(error_log,"a") as logfile:
            logfile.write(f"\n ----- {make_timestamp('date')} ----- \nQuell-Ordner:   {source_folder}\n------------------------------\n")
    result_list = scan_source_folder(source_folder, result_list)
    if check_for_errors_is_selected:
        if hash_errors == 0 and corrupted_files == 0:
            with open(error_log,"a") as logfile:
                logfile.write(f"Keine Fehler gefunden!\n")
    if check_for_duplicates_is_selected:
        if check_for_errors_is_selected:
            result_list.append("\n\n\n")
        search_duplicates(source_folder, result_list)
    return result_list

def scan_source_folder(source_folder, list_result: list):
    global files_ok
    global no_image_files
    global check_for_errors_is_selected
    global check_for_duplicates_is_selected
    for filename in os.listdir(source_folder):
        file_path = os.path.join(source_folder,filename)
        if os.path.isdir(file_path):
            list_result = scan_source_folder(file_path, list_result)
        else:
            if check_file_extension(file_path):
                if check_for_errors_is_selected:
                    try:
                        get_hash_value(file_path)
                        check_if_image_is_broken(file_path)
                        infobox_queue.put(f"{make_timestamp('time')} : {file_path} ist OK!")
                        #list_result.append(f"{make_timestamp('time')} : {file_path} ist OK!")
                        files_ok += 1
                    except (UnidentifiedImageError) as e:
                        infobox_queue.put(f"{make_timestamp('time')} : {e}")
                        #list_result.append(f"{make_timestamp('time')} : {e}")
                        handleError(e)
                    except (OSError) as e:
                        infobox_queue.put(f"{make_timestamp('time')} : {e}")
                        #list_result.append(f"{make_timestamp('time')} : {e}")
                        handleError(e)
                if check_for_duplicates_is_selected:
                    fill_filelist_for_duplicates(filename, file_path)
            else:
                    no_image_files += 1
    return list_result

def check_file_extension(file_path):
    return file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif'))

def get_hash_value(file_path): #compute checksum. here 'truncated image' exception (OS error) can occure
    try:
        global hash_errors
        image = Image.open(file_path)
        return hashlib.md5(image.tobytes()).hexdigest()
    except (OSError):
        hash_errors += 1
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
        raise UnidentifiedImageError (f"{file_path} ist kaputt")
    except (OSError):
        corrupted_files += 1
        raise OSError (f"{file_path} ist trunkiert")

def fill_filelist_for_duplicates(filename, file_path):
    global duplicate_file_names
    id = filename.split(".")[0]
    if id in duplicate_file_names.keys():
        duplicate_file_names[id].append(file_path)
    else:
        duplicate_file_names[id] = [file_path]

def search_duplicates(source_folder, result_list):
    duplicates = f"---------------------------------  {make_timestamp('all')}  --------------------------------- \nQuell-Ordner:   {source_folder}\n------------------------------------------------------------------------------------------\nGefundene Duplikate:"
    duplicates += check_for_duplicated_files()
    result_list.append(duplicates)
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