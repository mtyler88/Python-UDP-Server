from helpers import *
from time import time

class Connection:
    def __init__(self, address, username):
        self.username=username
        self.address=address
        self.s_number=0
        self.s_number_b=int.to_bytes(self.s_number, 4, BYTE_ORDER)
        self.rs_number=0
        self.rs_number_b=int.to_bytes(self.rs_number, 4, BYTE_ORDER)
        self.ack_field=0
        self.ack_field_b=int.to_bytes(self.ack_field, 4, BYTE_ORDER)
        self.last_message_time=time()

    def tell_alive(self, socket):
        self.send_data(BYTE_COMMAND['still_alive'], socket)

    def process_data(self, data): 
        new_rs=int.from_bytes(data[0:4], BYTE_ORDER)
        self.ack_check(new_rs)
        self.last_message_time=time()
        data=data[12:]
        if data[0:4]==BYTE_COMMAND['input']:
            return ("input", int.from_bytes(data[4:], BYTE_ORDER))
        elif data[0:4]==BYTE_COMMAND['position']:
            return ("position", int.from_bytes(data[4:8], BYTE_ORDER), int.from_bytes(data[8:12], BYTE_ORDER))
        else:
            return None

    def send_data(self, data, socket):
        message=HEADER_NAME+self.username+self.s_number_b+self.rs_number_b+self.ack_field_b+data
        socket.sendto(message, self.address)
        self.s_number+=1
        if self.s_number>INT32_MAX:
            self.s_number=0
        self.s_number_b=int.to_bytes(self.s_number, 4, BYTE_ORDER)

    def ack_check(self, new_rs):
        if check_higher(new_rs, self.rs_number):
            if new_rs<self.rs_number:
                ack_shift=new_rs+INT32_MAX+1-self.rs_number
            else:
                ack_shift=new_rs-self.rs_number
            if ack_shift>=ACK_FIELD_LENGTH:
                self.ack_field=0
                self.ack_field_b=int.to_bytes(self.ack_field, 4, BYTE_ORDER)
            else:
                self.ack_field=(self.ack_field<<ack_shift)%(1<<ACK_FIELD_LENGTH)|(1<<ack_shift-1)
                self.ack_field_b=int.to_bytes(self.ack_field, 4, BYTE_ORDER)
            self.rs_number=new_rs
            self.rs_number_b=int.to_bytes(new_rs, 4, BYTE_ORDER)
        else:
            if self.rs_number<new_rs:
                ack_point=self.rs_number+INT32_MAX+1-new_rs
            else:
                ack_point=self.rs_number-new_rs
            if ack_point>0 and ack_point<=ACK_FIELD_LENGTH:            
                self.ack_field |= 1<<(ack_point-1)
                self.ack_field_b=int.to_bytes(self.ack_field, 4, BYTE_ORDER)
