#-----------------------------------------------------------------------
#Ensure that this code runs in a linux enrionment.
#Ensure qpdf and poppler must be installed on linux.
#
#This program was specifically created to process engineering drawings
#and convert it into text form and create a searchable csv file from
#the extracted text.
#=======================================================================
import pandas as pd
from os import listdir
import os 
import os.path, time
import subprocess
import optparse
import pandas as pd
import csv
from progress.bar import IncrementalBar
import tempfile
import PyPDF2


parser = optparse.OptionParser()
#parser.add_option('-p', '--input-path', dest='input_path', help='input path')
parser.add_argument('--input-path','-p', nargs='?', const='CONST', default='input_path')
parser.add_argument('--output-path','-o', default='output_path')
(options, args) = parser.parse_args()
input_directory = options.input_path
output_directory = options.output_path + "/"
source_path = str(input_directory + "/")

#----------create and use temporary directory----------------
o_path = tempfile.TemporaryDirectory(dir = output_path)
print(o_path.name)
output_path = str(o_path.name + "/")
#------------------------------------------------------------
print("Checking for newly added/updated files")
keywords_data_frame = pd.DataFrame(columns=["Filename", "Keywords","Revision","Drawing_Number","Mid","Created"])

inputfiles = listdir(source_path)
input_data_frame = pd.DataFrame(inputfiles, columns=["Input_Files"])
input_data_frame['Input_Revision'] = input_data_frame['Input_Files'].str[-6:-4]
input_data_frame['Drawing_Number'] = input_data_frame['Input_Files'].str[:-6]
new_drawings = input_data_frame[((input_data_frame['Drawing_Number'].isin(keywords_data_frame['Drawing_Number']))==False) & ((input_data_frame['Input_Files'].str.contains(" "))==False) & ((input_data_frame['Input_Files'].str.contains("LCS"))==False) & ((input_data_frame['Input_Files'].str.endswith("pdf")==True))]
print("Done.")
#---------------------decrypt PDF files----------------------

inputfiles = list(new_drawings['Input_Files'])
bar = IncrementalBar('Decrypting', max=len(inputfiles))
for i in range(len(inputfiles)):
    file_name = str(source_path + inputfiles[i])
    try:
        bashCommand = "qpdf --decrypt '" + file_name + "' '"+ output_path +"unlock_" + inputfiles[i] + "'"
        subprocess.check_output(['bash','-c', bashCommand])
    except:
        continue
    bar.next()
bar.finish()
print("\n")
#------------------------------------------------------------
#---------------------Removing big pages pdf file------------
outputfiles = listdir(output_path)
bar = IncrementalBar('Remove Big Files', max=len(outputfiles))
for k in range(len(outputfiles)):
    outputfilepath = output_path + outputfiles[k]
    pdfFileObj = open(outputfilepath,'rb')
    pdfReader = PyPDF2.PdfFileReader(pdfFileObj)
    num_pages = pdfReader.numPages
    if num_pages > 9:
        os.remove(outputfilepath)
    bar.next()
bar.finish()
print("\n")
#-----------------------------------------------------------
#--------------Convert remaining files into text------------
onlyfiles = listdir(output_path)
bar = IncrementalBar('Converting to text', max=len(onlyfiles))
for i in range(len(onlyfiles)):
    file_name = str(output_path + onlyfiles[i])
    file_text = (file_name[:-4] + ".txt")
    try:
        bashCommand = "pdftotext '" + file_name + "' '"+ file_text + "'"
        subprocess.check_output(['bash','-c', bashCommand])
        os.remove(file_name)
    except:
        continue    
    bar.next()
bar.finish()
print("\n")
#-----------------------------------------------------------
#-------------concatenate the text files-------------------
keywords = []
files = listdir(output_path)
bar = IncrementalBar('Concatenating', max=len(files))
for fname in files:
    files_name = fname[7:-4]
    open_file = open(output_path + fname, "r")
    list_of_text = []
    for line in open_file:
        stripped_line = line.strip()
        list_of_text.append(stripped_line) 
        refined_text = list(set([x for x in list_of_text if x and len(x)>4])) 
        listToStr = ",".join([str(x) for x in refined_text]) 
    drawing_no = files_name[:-2]
    mid = files_name[6:8]
    revision = files_name[-2:]
    file_created = time.ctime(os.path.getctime(source_path + files_name + ".pdf"))
    keywords_data_frame = keywords_data_frame.append({"Filename":files_name, "Keywords":listToStr,"Revision": revision,"Drawing_Number": drawing_no,"Mid": mid,"Created": file_created}, ignore_index=True)
    bar.next()
bar.finish()
print("\n")
#-----------------take only the latest revision--------------
filtered_drawings=[]
list_drawings = list(set(keywords_data_frame['Drawing_Number']))
bar = IncrementalBar('Check Latest Revision', max=len(list_drawings))
for i in range(len(list_drawings)):
    revision_check = keywords_data_frame[keywords_data_frame['Drawing_Number'].str.contains(str(list_drawings[i]))]
    check = revision_check.sort_values('Revision')
    check = check.iloc[-1]
    filtered_drawings.append(check) 
    bar.next()
bar.finish()
print("\n")
filtered_drawings = pd.DataFrame(filtered_drawings)
#-----------------------------------------------------------

filtered_drawings.to_csv (output_directory, index = False, header = True)
o_path.cleanup()