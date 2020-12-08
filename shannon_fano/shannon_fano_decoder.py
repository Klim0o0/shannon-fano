from hashlib import md5
from typing import Tuple, List, Dict
from bitarray import bitarray

from shannon_fano.decoder import Decoder
from shannon_fano.file import File


class ShannonFanoDecoder(Decoder):

    @classmethod
    def decode(cls, archive_data: bytes) -> List[File]:
        index = 0
        decoded_files: List[File] = []
        data_list: List[bytes] = []
        while index < len(archive_data):
            data = cls.get_data(archive_data, index)
            index = data[1] + 1
            data_list.append(data[0])
        for i in range(0, len(data_list), 4):
            file_path = cls.get_file_path(data_list[i])
            encoding_dictionary = cls.get_encoding_dictionary(data_list[i + 1])
            file_data = cls.decode_file_data(encoding_dictionary,
                                             data_list[i + 2])
            if md5(file_data).digest() != data_list[i + 3]:
                file_data = None

            decoded_files.append(File(file_path,
                                      file_data,
                                      data_list[i + 3]))

        return decoded_files

    @classmethod
    def get_file_path(cls, file_path_data: bytes):
        file_path: str = ''
        for i in file_path_data:
            file_path += chr(i)
        return file_path

    @classmethod
    def decode_file_data(cls, encoding_dictionary: Dict[int, bitarray],
                         file_data: bytes):
        empty_bits_count = file_data[-1]
        bit_file_data = bitarray()
        bit_file_data.frombytes(file_data[0:len(file_data) - 1:])
        decoding_dictionary = {}
        decode_file_data = bytearray()
        for i in encoding_dictionary:
            decoding_dictionary[encoding_dictionary[i].to01()] = i
        temp = ''
        for bit in bit_file_data[0:len(bit_file_data) - empty_bits_count]:
            temp += '1' if bit else '0'
            if temp in decoding_dictionary.keys():
                decode_file_data.append(decoding_dictionary[temp])
                temp = ''
        return decode_file_data

    @classmethod
    def get_encoding_dictionary(cls, encoding_dictionary_data: bytes):
        encoding_dictionary_bits = bitarray()
        encoding_dictionary_bits.frombytes(encoding_dictionary_data)
        index = 0
        encoding_dictionary: Dict[int, bitarray] = {}

        while len(encoding_dictionary_bits) - index > 7:
            symbol: bitarray = encoding_dictionary_bits[index:index + 8:]
            code_len_bits: bitarray = \
                encoding_dictionary_bits[index + 8:index + 16:]
            code_len = int(code_len_bits.to01(), 2)
            code = encoding_dictionary_bits[index + 16:index + 16 + code_len:]
            encoding_dictionary[int(symbol.to01(), 2)] = code
            index += 16 + code_len
        return encoding_dictionary

    @classmethod
    def get_data(cls, archive_data: bytes, index: int) -> Tuple[bytes, int]:
        data = bytearray()
        while archive_data[index] != 0:
            for i in range(1, archive_data[index] + 1):
                data.append(archive_data[index + i])
            index += archive_data[index] + 1
        return bytes(data), index
