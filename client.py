import socket
import threading
import pickle
import select
from queue import Queue


class Client:
    """
    Select based Client class.
    """
    def __init__(self, master, addr):
        # master is the object that should handle the data.
        self.master = master
        self.RUN = True
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.s.connect(addr)
        self.s.setblocking(False)

        self.data_to_send = Queue()

        self.main_thread = threading.Thread(target=self.run, daemon=True)
        self.main_thread.start()

    def run(self):
        """
        Runs the select business.
        """
        try:
            while self.RUN:
                read_list, write_list, exception_list = select.select([self.s], [self.s], [])

                if len(read_list) != 0:
                    data = self.recv_all()
                    self.proceed_data(self.s, data)

                if len(write_list) != 0:
                    self.send_data(write_list)
        except:
            self.close()

    def proceed_data(self, client, byte_data):
        if byte_data is not None:
            try:
                data = pickle.loads(byte_data)
                # master should have a receive_data method.
                self.master.receive_data(data)
            except EOFError:
                pass

    def send_data(self, w_list):
        while not self.data_to_send.empty():
            if self.s in w_list:
                data = self.data_to_send.get()
                data = pickle.dumps(data)
                self.s.send(data)

    def send(self, data):
        # outside method to call from master.
        self.data_to_send.put(data)

    def recv_all(self):
        # receives all data (in case it's bigger than the buffer).
        BUFF_SIZE = 4096  # 4 KiB
        data = b''
        while True:
            part = self.s.recv(BUFF_SIZE)
            data += part
            if len(part) < BUFF_SIZE:
                # either 0 or end of data
                break
        return data

    def close(self):
        # closes the server safely to avoid trouble.
        self.RUN = False
        try:
            self.s.close()
        except OSError:
            pass
