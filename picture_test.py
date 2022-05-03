import config
import csv
import os
import hashlib
from PIL import Image, UnidentifiedImageError
from time import strftime
import traceback

check_for_errors_is_selected = False
check_for_duplicates_is_selected = False
file_counter = 0
files_ok = 0
hash_errors = 0
corrupted_files = 0
duplicated_files = 0
duplicate_file_names = {}

def reset_stats():
    global file_counter
    global files_ok
    global hash_errors
    global corrupted_files
    global duplicated_files
    global duplicate_file_names

    file_counter = 0
    files_ok = 0
    hash_errors = 0
    corrupted_files = 0
    duplicated_files = 0
    duplicate_file_names.clear()

def make_timestamp():
    return strftime('%H:%M:%S')

def handleError(e):
    print("!",e)
    traceback.print_exc() #print stack trace
    with open("errors.log","a") as logfile:
        logfile.write(f"{make_timestamp()}: {str(e)}+\n")

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
    result_list = put_test_entry_in_list(source_folder, result_list)
    if check_for_duplicates_is_selected:
        result_list.append("\nGefundene Duplikate:")
        result_list.append(search_for_duplicates())
    return result_list

def put_test_entry_in_list(source_folder, list_result: list):
    for filename in os.listdir(source_folder):
        file_path = os.path.join(source_folder,filename)
        if os.path.isdir(file_path):
            list_result = put_test_entry_in_list(file_path, list_result)
        else:
            try:
                global files_ok
                global check_for_errors_is_selected
                global check_for_duplicates_is_selected
                if check_for_errors_is_selected:
                    get_hash_value(file_path)
                    check_if_image_is_broken(file_path)
                    list_result.append(f"{make_timestamp()} : {file_path} ist OK!")
                    files_ok += 1
            except (UnidentifiedImageError) as e:
                list_result.append(f"{make_timestamp()} : {e}")
                #handleError(e)
                pass
            except (OSError) as e:
                list_result.append(f"{make_timestamp()} : {e}")
                #handleError(e)
                pass
            if check_for_duplicates_is_selected:
                    fill_filelist_for_duplicates(filename, file_path)
    global duplicate_file_names
    return list_result

def get_hash_value(file_path): #compute checksum. here 'truncated image' exception (OS error) can occure
    try:
        global hash_errors
        image = Image.open(file_path)
        return hashlib.md5(image.tobytes()).hexdigest()
    except (OSError) as e:
        hash_errors += 1
        raise OSError(f"{file_path} ist kaputt oder kein Bild.\n{str(e)}")

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

def search_for_duplicates():
    global duplicated_files
    search_result = ""
    for key, values in duplicate_file_names.items():
        if len(values) > 1:
            search_result += (f"\nID: {key}\n")
            duplicated_files += 1
            for value in values:
                search_result += (f"{value}\n")
    if search_result == "":
        search_result += "Keine\n"
    return search_result
