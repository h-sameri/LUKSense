import magic
import decimal


def pretty_size(file_size):
    if file_size < 1024:
        return str(file_size) + ' KB'
    elif file_size < 1024 * 1024:
        size_str = str(round(decimal.Decimal(file_size)/1024, 1))
        if size_str.endswith('.0'):
            size_str = size_str.replace('.0', '')
        return size_str + ' MB'
    else:
        size_str = str(round(decimal.Decimal(file_size)/(1024*1024), 1))
        if size_str.endswith('.0'):
            size_str = size_str.replace('.0', '')
        return size_str + ' GB'


def pretty_time(file_time):
    file_time = str(file_time)
    file_time = file_time.replace('-', '/')
    file_time = file_time.replace('T', ' ')
    if '.' in file_time:
        file_time = file_time[0:file_time.index('.')]
    return file_time


def save(file_path, file_data):
    f = open(file_path, 'wb')
    f.write(file_data)
    f.close()


def magic_from_buffer(file_data):
    return get_type_from_mime(magic.from_buffer(file_data, mime=True))


def magic_from_file(file_path):
    return get_type_from_mime(magic.from_file(file_path, mime=True))


def get_type_from_mime(mime):
    if mime is None:
        return 'o'
    else:
        type = mime.split('/')[0]
        if type == 'video':
            return 'v'
        elif type == 'image':
            return 'p'
        elif type == 'text':
            return 'd'
        elif type == 'application':
            if 'epub' in mime or 'pdf' in mime or 'rtf' in mime \
                or 'msword' in mime or 'document' in mime \
                or 'excel' in mime or 'xml' in mime or 'json' in mime \
                or 'powerpoint' in mime or 'ebook' in mime:
                return 'd'
            elif 'zip' in mime or 'archive' in mime or 'tar' in mime \
                or 'compress' in mime or 'rar' in mime:
                return 'a'
            else:
                return 'o'
        else:
            return 'o'
