class Announcement:

    def __init__(self, id, title, creation_time, html=None):
        self.id = id
        self.title = title
        self.creation_time = creation_time
        self.html = html

    def get_id(self):
        return self.id

    def get_title(self):
        return self.title

    def get_creation_time(self):
        return self.creation_time

    def get_html(self):
        return self.html