from feedback import Feedback
from flask import g


class NFTDoc:

    def __init__(self,
                 id=None,
                 owner=None,
                 name=None,
                 description=None,
                 price=None,
                 status=None,
                 creation_time=None,
                 preview_of=None,
                 update_time=None,
                 cur=None):
        if cur is None:
            self.cur = g.cur
        else:
            self.cur = cur
        self.id = id
        self.owner = owner
        self.name = name
        self.description = description
        self.price = price
        self.status = status
        self.creation_time = creation_time
        self.preview_of = preview_of
        #
        if update_time is None:
            self.__set_update_time()
        else:
            self.update_time = update_time
        self.files = None
        self.preview_files = None
        self.feedback = Feedback()

    def set_files(self, file_nfts):
        self.files = file_nfts

    def set_preview_files(self, file_nfts):
        self.preview_files = file_nfts

    def set_feedback(self, feedback):
        self.feedback = feedback

    def __process_files(self):
        file_str = ''
        t, v, p, d, a, o = 0, 0, 0, 0, 0, 0
        file_keys = []
        file_size = 0
        #
        if self.files is not None:
            t = len(self.files)
            for file in self.files:
                file_str += file.file_name.replace('_', ' ').replace('-', ' ').replace('.', ' ')
                file_str += ' '
                if file.get_file().type_general == 'v':
                    v += 1
                elif file.get_file().type_general == 'p':
                    p += 1
                elif file.get_file().type_general == 'd':
                    d += 1
                elif file.get_file().type_general == 'a':
                    a += 1
                else:
                    o += 1
                file_keys.append({
                     'hash' : file.file_hash ,
                     'name' : file.file_name ,
                     'size' : file.get_file().size
                })
                file_size += file.get_file().size
        #
        self.files_str = file_str
        self.files_counts = {
             't' : t ,
             'v' : v ,
             'p' : p ,
             'd' : d ,
             'a' : a ,
             'o' : o
        }
        self.files_keys = file_keys
        self.files_size = file_size

    def __process_preview_files(self):
        self.preview_files_str = ''
        if self.preview_files is not None:
            for file in self.preview_files:
                self.preview_files_str += file.file_hash
                self.preview_files_str += ' '
                self.preview_files_str += file.file_name
                self.preview_files_str += ' '
                #preview_files_size += file.size

    def get_nft(self):
        self.__process_files()
        self.__process_preview_files()
        nft = {}
        nft['id'] = self.id
        nft['owner'] = self.owner
        nft['name'] = self.name
        nft['description'] = self.description
        nft['price'] = self.price
        nft['status'] = self.status
        nft['creation_time'] = self.creation_time
        nft['update_time'] = self.update_time
        nft['files'] = self.files_str
        nft['files_keys'] = self.files_keys
        nft['files_count'] = self.files_counts
        nft['files_size'] = self.files_size
        nft['preview_files'] = self.preview_files_str
        #nft['preview_files_size'] = preview_files_size
        if self.preview_files is not None:
            nft['preview_files_count'] = len(self.preview_files)
        else:
            nft['preview_files_count'] = 0
        nft['average_quality'] = self.feedback.average_quality
        nft['quality_count'] = self.feedback.quality_count
        nft['total_count']= self.feedback.total_count
        nft['malicious_percent'] = self.feedback.malicious_percent
        nft['misleading_percent'] = self.feedback.misleading_percent
        nft['genuine_percent'] = self.feedback.genuine_percent
        return nft

    def edit_nft(self):
        nft = {}
        nft['name'] = self.name
        nft['description'] = self.description
        nft['price'] = self.price
        # nft['status'] = self.status
        return { 'doc' : nft }

    # def upload_preview_files

    def upload_files(self):
        self.__process_files()
        nft = {}
        nft['files'] = self.files_str
        nft['files_keys'] = self.files_keys
        nft['files_count'] = self.files_counts
        nft['files_size'] = self.files_size
        self.__set_update_time()
        nft['update_time'] = self.update_time
        return { 'doc' : nft }

    def upload_preview_files(self):
        self.__process_preview_files()
        nft = {}
        nft['preview_files'] = self.preview_files_str
        #nft['preview_files_size'] = preview_files_size
        if self.preview_files is not None:
            nft['preview_files_count'] = len(self.preview_files)
        else:
            nft['preview_files_count'] = 0
        self.__set_update_time()
        nft['update_time'] = self.update_time
        return { 'doc' : nft }

    def upload_preview_files_cron(self):
        self.__process_preview_files()
        nft = {}
        nft['preview_files'] = self.preview_files_str
        #nft['preview_files_size'] = preview_files_size
        if self.preview_files is not None:
            nft['preview_files_count'] = len(self.preview_files)
        else:
            nft['preview_files_count'] = 0
        return { 'doc' : nft }

    def rate_nft(self):
        nft = {}
        nft['average_quality'] = self.feedback.average_quality
        nft['quality_count'] = self.feedback.quality_count
        nft['total_count']= self.feedback.total_count
        nft['malicious_percent'] = self.feedback.malicious_percent
        nft['misleading_percent'] = self.feedback.misleading_percent
        nft['genuine_percent'] = self.feedback.genuine_percent
        return { 'doc' : nft }

    def __set_update_time(self):
        self.cur.execute('SELECT MAX(creation_time) FROM file WHERE hash IN (SELECT file_hash FROM file_nft WHERE nft_id=%s);',
                      (self.id,))
        update_time = self.cur.fetchone()
        if update_time is None:
            self.update_time = self.creation_time
        else:
            self.update_time = update_time[0]
