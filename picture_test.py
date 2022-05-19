import config
from queue import Queue
import os
import hashlib
from PIL import Image, UnidentifiedImageError
from time import strftime
import traceback

# disable DecompressionBombWarning
Image.MAX_IMAGE_PIXELS = None

save_label_source_folder = "Quellordner:\n"
save_label_check_errors = "\nAuf Fehler pruefen:\n"
save_label_check_duplicates = "\nAuf Duplikate pruefen:\n"
save_label_last_checked_file = "\nLetzte Datei:\n"
save_label_file_count = "\nDateien im Verzeichnis:\n"
save_label_files_ok = "\nDateien OK:\n"
save_label_no_image_files = "\nDateien kein Bild:\n"
save_label_corropted_files = "\nKaputte Dateien:\n"
save_label_hash_errors = "\nHash Fehler:\n"
save_label_file_duplicates = "\nDuplikate:\n"

error_log = config.file_error_log
duplicates_log = config.file_duplicates_log

start_new_test = True
continue_work = False

check_for_errors_is_selected = False
check_for_duplicates_is_selected = False
file_counter = 0
files_ok = 0
no_image_files = 0
hash_errors = 0
corrupted_files = 0
file_duplicates = 0
duplicate_file_names = {}
last_checked_file = ""
start_scan_at_file = ""

infobox_queue = Queue()
#files_ok_queue = Queue()
#no_image_files_queue = Queue()
#corrupted_files_queue = Queue()

def program_start():
    """
    check if there an incomplete file-test
    """
    global start_new_test
    if os.path.isfile(config.save_file):
        start_new_test = False
        return load_progress()
    else:
        start_new_test = True
        return ""


def reset_stats():
    """
    clear stats for a new test
    """
    global files_ok
    global no_image_files
    global hash_errors
    global corrupted_files
    global file_duplicates
    global duplicate_file_names

    if start_new_test:
        files_ok = 0
        no_image_files = 0
        hash_errors = 0
        corrupted_files = 0
        file_duplicates = 0
        duplicate_file_names.clear()


def make_timestamp(style:str):
    if style == "date":
        return strftime('%d.%m.%Y')
    elif style == "time":
        return strftime('%H:%M:%S')
    elif style == "all":
        return strftime('%d.%m.%Y, %H:%M:%S')


def write_error_in_log(e):
    with open(error_log,"a") as logfile:
        logfile.write(f"{make_timestamp('time')} : {str(e)}\n")


def prepare_for_a_new_file_test(source_folder, with_subfolders = True):
    """
    reset a eventually unfinished filetest and
    counts the files in the new sourcefolder
    """
    global start_new_test
    global start_scan_at_file
    
    if not start_new_test:
        start_new_test = True
        start_scan_at_file = ""
        reset_stats()
        if os.path.isfile(config.save_file):
            try:
                os.remove(config.save_file)
            except OSError as e:
                print(e)
    check_file_count(source_folder, with_subfolders)


def check_file_count(source_folder, with_subfolders = True):
    """
    counts the files in the selected folder
    """
    global file_counter
                    
    for filename in os.listdir(source_folder):
        file_path = os.path.join(source_folder,filename)
        if os.path.isdir(file_path):
            if with_subfolders:
                check_file_count(file_path, True)
        else:
            file_counter += 1


def start_test(source_folder):
    prepare_error_log(source_folder)
    scan_source_folder(source_folder)
    check_for_interrupted_file_testing(source_folder)


def prepare_error_log(source_folder):
    """
    print new headlines in error-log
    """
    global check_for_errors_is_selected
    global start_scan_at_file

    if check_for_errors_is_selected:
        if start_scan_at_file == "":
            with open(error_log,"a") as logfile:
                logfile.write(f"\n ----- {make_timestamp('date')} ----- \nQuell-Ordner:   {source_folder}\n------------------------------\n")
        else:
            with open(error_log,"a") as logfile:
                logfile.write(f"\n ----- Fortsetzung der Suche: {make_timestamp('date')} ----- \n------------------------------\n")


def scan_source_folder(source_folder):
    """
    - scans the files in the selected folder for errors
    - if continues a unfinished filetest it seeks the last checked file first
    - while checking files, every loop checks for stop-command (continue_work = False)
    """
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
                    continue
                if start_scan_at_file == file_path:
                    start_scan_at_file = ""
                    continue
                if check_for_errors_is_selected:
                    if check_file_extension(file_path):
                        try:
                            get_hash_value(file_path)
                            check_if_image_is_broken(file_path)
                            infobox_queue.put(f"{make_timestamp('time')} : {file_path} ist OK!")
                            #list_result.append(f"{make_timestamp('time')} : {file_path} ist OK!")
                            files_ok += 1
                            #files_ok_queue.put(f"{files_ok}")
                        except (UnidentifiedImageError) as e:
                            infobox_queue.put(f"{make_timestamp('time')} : {e}")
                            #list_result.append(f"{make_timestamp('time')} : {e}")
                            write_error_in_log(e)
                        except (OSError) as e:
                            infobox_queue.put(f"{make_timestamp('time')} : {e}")
                            #list_result.append(f"{make_timestamp('time')} : {e}")
                            write_error_in_log(e)
                    else:
                            no_image_files += 1
                            #no_image_files_queue.put(no_image_files)
                            infobox_queue.put(f"{make_timestamp('time')} : {file_path} ist keine Bild-Datei")
                            with open(error_log,"a") as logfile:
                                logfile.write(f"{make_timestamp('time')} : {file_path} ist keine Bild-Datei\n")
                if check_for_duplicates_is_selected:
                        fill_filelist_for_duplicates(filename, file_path)
        else:
            start_scan_at_file = last_checked_file
            break


def check_for_interrupted_file_testing(source_folder):
    """
    - if the filetest is finished, it delete a eventually savefile(continue.txt) and set to "new file-test" mode
    - if the filetest is interrupted, it switch to "continue test" mode and create a new savefile and saves the current data
    """
    global continue_work
    global start_new_test

    if continue_work:
        finish_results(source_folder)
        if os.path.isfile(config.save_file):
            try:
                os.remove(config.save_file)
            except OSError as e:
                print(e)
        start_new_test = True
    else:
        start_new_test = False
        save_progress(source_folder)


def finish_results(source_folder):
    """
    if it is selected:
    it checks the counted errors, and write a comment in log if there is no error
    create the duplicates result report
    """
    if check_for_errors_is_selected:
        if hash_errors == 0 and corrupted_files == 0:
            with open(error_log,"a") as logfile:
                logfile.write(f"Keine Fehler gefunden!\n")
    if check_for_duplicates_is_selected:
        if check_for_errors_is_selected:
            infobox_queue.put("\n\n\n")
        print_duplicates_result(source_folder)

def check_file_extension(file_path):
    """
    if the current file has one of the wanted extensions, it returns "True"
    """
    return file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.tif', '.tiff', '.bmp', '.gif'))


def get_hash_value(file_path): #compute checksum. here 'truncated image' exception (OS error) can occure
    try:
        global hash_errors

        image = Image.open(file_path)
        return hashlib.md5(image.tobytes()).hexdigest()
    except (OSError):
        hash_errors += 1
        #corrupted_files_queue.put(hash_errors + corrupted_files)
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
        #corrupted_files_queue.put(hash_errors + corrupted_files)
        raise UnidentifiedImageError (f"{file_path} ist kaputt")
    except (OSError):
        corrupted_files += 1
        #corrupted_files_queue.put(hash_errors + corrupted_files)
        raise OSError (f"{file_path} ist trunkiert")


def fill_filelist_for_duplicates(filename, file_path):
    """
    while the file-test is running, every filename (and path) is saved in a dictionary to compare it when the test has finished
    """
    global duplicate_file_names

    if  not os.path.isdir(filename):
        id = filename.split(".")[0]
        if id in duplicate_file_names.keys():
            duplicate_file_names[id].append(file_path)
        else:
            duplicate_file_names[id] = [file_path]


def print_duplicates_result(source_folder):
    """
    bring the duplicates-result to screen and log-file
    """
    global file_duplicates

    duplicates = f"---------------------------------  {make_timestamp('all')}  --------------------------------- \nQuell-Ordner:   {source_folder}\n------------------------------------------------------------------------------------------\nGefundene Duplikate: {file_duplicates}"
    duplicate_search_result = check_filelist_for_duplicates()
    duplicates += duplicate_search_result
    infobox_queue.put(duplicates)
    duplicates += "\n\n\n\n"
    save_duplicates_log(duplicates)


def check_filelist_for_duplicates():
    """
    checks the dictionary (with the saved filenames) for duplicates
    """
    global file_duplicates

    search_result = ""
    for key, values in duplicate_file_names.items():
        if len(values) > 1:
            search_result += (f"\n\nDateiname: {key}\n")
            file_duplicates += 1
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


def save_progress(source_folder):
    save_data = save_label_source_folder
    save_data += source_folder
    save_data += save_label_check_errors
    save_data += str(check_for_errors_is_selected)
    save_data += save_label_check_duplicates
    save_data += str(check_for_duplicates_is_selected)
    save_data += save_label_last_checked_file
    save_data += last_checked_file
    save_data += save_label_file_count
    save_data += str(file_counter)
    save_data += save_label_files_ok
    save_data += str(files_ok)
    save_data += save_label_no_image_files
    save_data += str(no_image_files)
    save_data += save_label_corropted_files
    save_data += str(corrupted_files)
    save_data += save_label_hash_errors
    save_data += str(hash_errors)
    save_data += save_label_file_duplicates
    for key, values in duplicate_file_names.items():
        save_data += key + "\n"
        for value in values:
            save_data += value + "\n"
        save_data += "\n"
    with open(config.save_file,"w") as savefile:
        savefile.write(save_data)


def load_progress():
    global start_scan_at_file
    global check_for_errors_is_selected
    global check_for_duplicates_is_selected
    global file_counter
    global files_ok
    global no_image_files
    global corrupted_files
    global hash_errors
    global duplicate_file_names

    bool_set_source_folder = False
    bool_set_scan_file = False
    bool_set_check_errors = False
    bool_set_check_duplicates = False
    bool_set_file_counter = False
    bool_set_files_ok = False
    bool_set_no_image_files = False
    bool_set_corrupted_files = False
    bool_set_hash_errors = False
    bool_set_duplicates_file_names = False
    bool_set_duplicate_headline = True
    current_duplicate_filename = ""

    source_folder = ""
    with open(config.save_file,"r") as loaded_data:
        for file_line in loaded_data:
            # read headlines
            if save_label_source_folder.strip() in file_line.strip():
                bool_set_source_folder = True
            elif save_label_last_checked_file.strip() in file_line.strip():
                bool_set_scan_file = True
            elif save_label_check_errors.strip() in file_line.strip():
                bool_set_check_errors = True    
            elif save_label_check_duplicates.strip() in file_line.strip():
                bool_set_check_duplicates = True
            elif save_label_file_count.strip() in file_line.strip():
                bool_set_file_counter = True
            elif save_label_files_ok.strip() in file_line.strip():
                bool_set_files_ok = True
            elif save_label_no_image_files.strip() in file_line.strip():
                bool_set_no_image_files = True
            elif save_label_corropted_files.strip() in file_line.strip():
                bool_set_corrupted_files = True
            elif save_label_hash_errors.strip() in file_line.strip():
                bool_set_hash_errors = True
            elif save_label_file_duplicates.strip() in file_line.strip():
                bool_set_duplicates_file_names = True
            # read values
            elif bool_set_source_folder:
                source_folder = file_line.strip()
                bool_set_source_folder = False
            elif bool_set_scan_file:
                start_scan_at_file = file_line.strip()
                bool_set_scan_file = False
            elif bool_set_check_errors:
                check_for_errors_is_selected = bool(file_line.strip())
                bool_set_check_errors = False
            elif bool_set_check_duplicates:
                check_for_duplicates_is_selected = bool(file_line.strip())
                bool_set_check_duplicates = False    
            elif bool_set_file_counter:
                file_counter= int(file_line.strip())
                bool_set_file_counter = False
            elif bool_set_files_ok:
                files_ok = int(file_line.strip())
                bool_set_files_ok = False
            elif bool_set_no_image_files:
                no_image_files = int(file_line.strip())
                bool_set_no_image_files = False
            elif bool_set_corrupted_files:
                corrupted_files = int(file_line.strip())
                bool_set_corrupted_files = False
            elif bool_set_hash_errors:
                hash_errors = int(file_line.strip())
                bool_set_hash_errors = False
            # read duplicates/file list
            elif bool_set_duplicates_file_names:
                if bool_set_duplicate_headline:
                    current_duplicate_filename = file_line.strip()
                    bool_set_duplicate_headline = False
                elif not bool_set_duplicate_headline and file_line.strip() == "":
                    bool_set_duplicate_headline = True
                else:
                    if current_duplicate_filename in duplicate_file_names.keys():
                        duplicate_file_names[current_duplicate_filename].append(file_line.strip())
                    else:
                        duplicate_file_names[current_duplicate_filename] = [file_line.strip()]
    return source_folder