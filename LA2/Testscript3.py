from threading import Thread
from LA2.http import http


def test_concurrent_read_write(name,index, flag):
    URL = "http://localhost/foo/" + name
    i = str(index)
    headerstr = "Content-Type: application/json\r\nThread_no: " + i + "\r\n"
    if flag:
        bodyvalue = "I am Thread no. " + str(index) + " and I am writing the file."
        resp = http(URL, bodyvalue, headerstr, True, False, "", "post").post_request(True)
        print("Response for client " + i + " : \n")
        print("\n\nPOST RESPONSE\n\n" + resp + "\n\n")
    else:
        resp = http(URL, index, headerstr, True, False, "", "get").get_request(True)
        print("Response for client " + i + " : \n")
        print("\n\nGET RESPONSE\n\n" + resp + "\n\n" )

no_of_threads = input("Enter no. of clients: ")
print("\n")
for i in range(0, int(no_of_threads)):
    flag = False
    if i == 1 or i == 3:
        flag = True
    Thread(target=test_concurrent_read_write, args=("out.txt", i, flag)).start()