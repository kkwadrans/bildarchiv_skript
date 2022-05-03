import config
import csv
import os
import shutil
import hashlib
from PIL import Image, UnidentifiedImageError
import glob
import traceback

class HashValueException(Exception):
    pass
class DuplicateImageException(Exception):
    pass
#to disable decompression bomb warning for large images
Image.MAX_IMAGE_PIXELS = None

output = 0
duplicate_file_names = {}
#TODO: Get actual error description AND file name!
def handleError(e):
    print("!",e)
    traceback.print_exc() #print stack trace
    with open("errors.log","a") as logfile:
        logfile.write(str(e)+"\n")

def get_values_from_input_file(csv_path): #Take IDs from CSV and return as numbers
        data = open(csv_path)
        data = csv.reader(data)  
        output = []
        for col in data:
            output.append(col[0])
        if (len(output)<1):
            raise IOError(f"Die Input-Datei {csv_path} enthält keine Einträge in der ersten Spalte oder ist keine valide CSV-Datei. Es wurden keine Einträge übernommen!")
        return output

def copy_pictures_to_output(numbers, input_folder, output_folder): #copy images from list to output_folder while checking for image errors
    global output
    for filename in os.listdir(input_folder):
        subfolder = os.path.join(input_folder,filename)
        if os.path.isdir(subfolder): #also copy pics from eventual subfolders (mit dem rückgabewert wird nichts gemacht, aber die globale variable hochgezählt)
            copy_pictures_to_output(numbers, subfolder, output_folder)
        id = filename.split(".")[0]
        id_without_v = id.replace("v","")
        if id_without_v in numbers:
            try:
                if glob.glob(f"{output_folder}/{id}.*"): #check if image with the same ID already exists in destination
                    raise DuplicateImageException(f"{id} existiert bereits im Zielordner. Die Datei wurde nicht kopiert.")
                else: 
                    print(f"Kopiere {filename} ..")
                    old_file_path= f"{input_folder}/{filename}"
                    new_file_path = f"{output_folder}/{filename}"
                    check_if_image_is_broken(old_file_path)
                    old_hash = get_hash_value(old_file_path)
                    shutil.copy(old_file_path,output_folder)
                    check_if_image_is_broken(new_file_path)
                    new_hash = get_hash_value(new_file_path)
                    if (old_hash != new_hash): #check if hash values match
                        raise HashValueException("Fehler beim Kopieren! Bitte Datei überprüfen -> "+ filename)
                    else:
                        output +=1
                        #os.remove(old_file_path) #HIER WIRD GELÖSCHT
            except Exception as e:
                handleError(e)
    return output
    

def get_hash_value(file_path): #compute checksum. here 'truncated image' exception (OS error) can occure
    try:
        image = Image.open(file_path)
        return hashlib.md5(image.tobytes()).hexdigest()
    except (OSError) as e:
        raise OSError(f"{file_path} ist kaputt oder kein Bild. {str(e)}")



def check_if_image_is_broken(file_path):
    #try:
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
    #except (UnidentifiedImageError):
    #    raise UnidentifiedImageError (f"{file_path} ist kaputt")
    #except (OSError):
    #    raise OSError (f"{file_path} ist trunkiert")


def check_for_duplicates(input_folder):
    global duplicate_file_names

    for filename in os.listdir(input_folder):
        print("Prüfe", filename, "...")
        subfolder = os.path.join(input_folder,filename)
        if os.path.isdir(subfolder):
            check_for_duplicates(subfolder) #TODO: kann man das anderes als mit global machen?
        else:
            try:
                check_if_image_is_broken(f"{input_folder}/{filename}")
            except Exception as e:
                handleError(e)
            id = filename.split(".")[0]
            if id in duplicate_file_names.keys():
                duplicate_file_names[id].append(filename)
            else:
                duplicate_file_names[id] = [filename]
            
    return duplicate_file_names


def print_duplicates(duplicate_file_names, output_file_name):
    with open(output_file_name,"w") as file:
        file.write("Diese dateinamen gibt es doppelt!: \n")
        for key in duplicate_file_names:
            if len(duplicate_file_names[key])>1:
                for item in duplicate_file_names[key]:
                    file.write(item+"  ")
                file.write("\n")


def main():
    open('errors.log', 'w').close() #delete file content
    number = 0
    #try:
        #numbers= get_values_from_input_file(config.input_file)
        #number= copy_pictures_to_output(numbers, config.input_folder,config.output_folder) 
    duplicate_file_names= check_for_duplicates(config.input_folder)
    print(duplicate_file_names)
    print_duplicates(duplicate_file_names, config.duplicate_file)
    #except Exception as e:
    #    handleError(e)
    #print(f"{number} Bilder wurden erfolgreich kopiert")

main()


