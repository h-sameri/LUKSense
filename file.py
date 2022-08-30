class File:

    def __init__(self,
                 hash,
                 path,
                 size,
                 type_general,
                 creation_time):
        self.hash = hash
        self.path = path
        self.size = size
        self.type_general = type_general
        self.creation_time = creation_time


class FileNFT:

    def __init__(self,
                 nft_id,
                 file_hash,
                 status,
                 file_name):
        self.nft_id = nft_id
        self.file_hash = file_hash
        self.status = status
        self.file_name = file_name

    def set_file(self, file):
        self.file = file

    def get_file(self):
        return self.file
