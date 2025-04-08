import threading

def thread1():
    print("thread 1 running")

def thread2():
    print("thread 2 running")

if __name__ == "__main__":
    worm_thread = threading.Thread(target=thread1())
    nema_ascend_thread = threading.Thread(target=thread2())

    worm_thread.start()
    nema_ascend_thread.start()

    worm_thread.join()
    nema_ascend_thread.join()
    print("joined")