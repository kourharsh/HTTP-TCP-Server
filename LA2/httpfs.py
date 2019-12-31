import socket
import threading
from threading import Lock
import os
import json
import pathlib
from mimetypes import MimeTypes
from LA2.httplib import httplib


class httpfs:
    def __init__(self, inputarray, directory):
        self.inputarray = inputarray
        self.port = 8080
        self.curr_directory = directory
        self.directory = directory
        self.debugging = False
        self.action = ""
        self.header_dict = {}
        self.req_body = ""
        self.query = ""
        self.path = ""
        self.error_code = 200
        self.host = 'localhost'
        self.client_body = ""
        self.isDirectory = False
        self.isFile = False
        self.lock = Lock()
        self.file_directory = ""
        self.patheditflag = False


    def checkinput(self):
        for i in range(0, len(self.inputarray)):
            if (self.inputarray[i] == '-p'):
                self.port = int(self.inputarray[i+1])
            if (self.inputarray[i] == '-d'):
                self.curr_directory = self.curr_directory + self.inputarray[i+1]
                #print(self.curr_directory)
                if os.path.exists(self.curr_directory):
                    if self.debugging:
                        print("Server Directory is :   " + self.curr_directory)
                else:
                    print("Error!! The current directory " + self.curr_directory + " for the server does not exists.")
                    exit()
            if (self.inputarray[i] == '-v'):
                self.debugging = True
        self.run_server()


    def run_server(self):
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            listener.bind((self.host, self.port))
            listener.listen(7)
            print('File server has been initialized and is listening at', self.port, ' :')
            while True:
                server, addr = listener.accept()
                threading.Thread(target=self.handle_client_request, args=(server, addr)).start()
        finally:
            listener.close()

    def handle_client_request(self, server, addr):
        try:
            while True:
                data = server.recv(2048)
                data = data.decode("utf-8")
                if not data:
                    break
                if self.debugging:
                    print("New Request for the server:")
                    print(data)
                self.lock.acquire()
                self.break_req(data) # break the client request for server to understand
                self.checksecurity()
                if self.error_code != 403:
                    self.directory = self.curr_directory + self.path
                    try:
                        if self.action == "GET":
                            self.make_file_name()
                            if os.path.exists(self.directory):
                                flagorig = True
                                flagnew = False
                            else:
                                flagorig = False
                                if os.path.exists(self.file_directory):
                                    flagnew = True
                                    self.directory = self.file_directory
                                else:
                                    flagnew = False
                            if flagorig or flagnew:
                                if self.debugging:
                                    print("Valid Path!")
                                self.isDirectory = os.path.isdir(self.directory)
                                if self.isDirectory:
                                    self.error_code = 200
                                    files = os.listdir(self.directory)
                                    self.req_body = json.dumps(files)
                                    if self.debugging:
                                        print("Returning a list of the current files in the current data directory!",
                                              self.directory)
                                        print("Files returned from the server: ")
                                        print(self.req_body)
                                else:
                                    self.isFile = os.path.isfile(self.directory)
                                    if self.isFile:
                                        if self.debugging:
                                            print("Returning the content of the file in the data directory",
                                                  self.directory)
                                        file_read = open(self.directory, "r")
                                        self.req_body = file_read.read()
                                        file_read.close()
                            else:
                                if self.debugging:
                                    print("Path could not be found : ", self.directory)
                                    print("Path could not be found : ", self.file_directory)
                                self.error_code = 404

                        elif self.action == "POST":
                            pathlib.Path(os.path.dirname(self.directory)).mkdir(parents=True, exist_ok=True)
                            self.make_file_name()
                            if self.patheditflag:
                                self.directory = self.file_directory
                            file_o = open(self.directory, "w")
                            file_o.write(self.client_body)
                            file_o.close()
                            self.error_code = 200
                            self.req_body = self.client_body
                            self.isFile = True

                    except OSError as err:
                        if self.debugging:
                            print(err)
                        self.error_code = 400
                        self.req_body = ""
                    except SystemError as err:
                        if self.debugging:
                            print(err)
                        self.error_code = 400
                        self.req_body = ""
                if self.isDirectory:
                    self.header_dict["Content-Type"] = "application/json"
                elif self.isFile:
                    if self.patheditflag:
                        self.directory = self.file_directory
                    #print("File type")
                    mimes_all = MimeTypes()
                    mime_type = mimes_all.guess_type(self.directory)
                    #print(mime_type[0])
                    self.header_dict["Content-Type"] = mime_type[0]

                resp = httplib(self.error_code, self.req_body, self.header_dict)
                response = resp.response_head() + self.req_body
                if self.debugging:
                    print('Response is :\n',response)
                server.sendall(response.encode("ascii"))
                self.reset()
                #self.error_code = 200
                #self.header_dict = {}
                if self.debugging:
                    print("Request processed!")
                self.lock.release()
        finally:
            server.close()

    def break_req(self, msg):
        header_l = msg.split('\r\n\r\n')
        str_upper = header_l[0]
        self.client_body = header_l[1]
        str_lines = str_upper.split('\r\n')
        first_line = str_lines[0].split(' ')
        self.action = first_line[0]
        if self.debugging:
            print("action is: ", self.action)
        self.search = first_line[1]
        #if self.debugging:
         #   print("Search folder is: ", self.search)

        if "?" in self.search:          # find the query and path
            pos = self.search.find("?")
            pos = pos
            key_r = self.search[0:pos].strip()
            pos = pos + 1
            length = len(self.search)
            value_r = self.search[pos:length]
            self.path = key_r
            self.query = value_r
        else:
            self.path = self.search

        for line in range(1, len(str_lines)):  # store all the headers from request to dictionary
            string_h = str(str_lines[line])
            pos = string_h.find(":")
            pos = pos
            key_r = string_h[0:pos].strip()
            pos = pos+1
            length = len(string_h)
            value_r = string_h[pos:length]
            self.header_dict[str(key_r)] = str(value_r).strip()
        #print(self.header_dict)
        #print(self.client_body)

    def reset(self):
        self.port = 8080
        self.action = ""
        self.header_dict = {}
        self.req_body = ""
        self.query = ""
        self.path = ""
        self.error_code = 200
        self.host = 'localhost'
        self.client_body = ""
        self.isDirectory = False
        self.isFile = False
        self.file_directory = ""
        self.patheditflag = False

    def make_file_name (self):
        pathlist = (self.directory).split("\"")
        file_name = pathlist[-1]
        if (".pdf" in file_name) or (".txt" in file_name) or (".json" in file_name) or (".html" in file_name) or (".xml" in file_name) :
            pass
        else:
            if "Content-Type" in self.header_dict.keys():
                type = self.header_dict["Content-Type"]
            else:
                type = "text"
            if type == "application/json" or type == "json":
                filetype = ".json"
            elif type == "text/plain" or type == "text":
                filetype = ".txt"
            elif type == "text/html" or type == "html":
                filetype = ".html"
            elif type == "text/pdf" or type == "pdf":
                filetype = ".pdf"
            elif type == "text/xml" or type == "xml":
                filetype = ".xml"
            else:
                filetype = ".txt"
            self.file_directory = self.directory + filetype
            self.patheditflag = True
            #if self.debugging:
             #   print("Searching File directory: " + self.file_directory)


    def checksecurity(self):
        #print(self.path)
        if ".." in self.path or "//" in self.path:
            if (self.debugging):
                print("Access is denied for the requested path! ", self.path)
            self.error_code = 403
        else:
            self.error_code = 200


inputserver = input("Please enter the command:\n")
inputarr_serv = inputserver.split(" ")
while '' in inputarr_serv:
    inputarr_serv.remove('')

if (inputarr_serv[0] == 'httpfs'):
    if (len(inputarr_serv) > 1) and (inputarr_serv[1] == 'help'):
        print("\n\nusage: httpfs [-v] [-p PORT] [-d PATH-TO-DIR]\n")
        print("-v    Prints debugging messages")
        print("-p    Specifies the port number that the server will listen and serve at.")
        print("      Default is 8080")
        print("-d    Specifies the directory that the server will use to read/write requested files. Default is the")
        print("      current directory when launching the application.")
    else:
        current_directory = os.getcwd() + "/files/a/a"
        httpfs(inputarr_serv[1:],current_directory).checkinput()
else:
    print("Invalid Command!")
    exit()
