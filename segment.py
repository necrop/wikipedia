import os
import re

from wikipedia import wikipediaconfig

DUMP_FILE = wikipediaconfig.CURRENT_DUMP
OUTPUT_DIR = wikipediaconfig.DUMP_SEGMENTED_DIR
FILESIZE = wikipediaconfig.SEGMENT_SIZE  # Number of lines per file
NAMESPACES = wikipediaconfig.NAMESPACES

XML_DECLARATION = '<?xml version="1.0" encoding="UTF-8"?>'
ROOT_TAG = 'mediawiki'
ROOT = """
<%s
    xmlns="http://www.mediawiki.org/xml/export-0.8/"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.mediawiki.org/xml/export-0.8/ http://www.mediawiki.org/xml/export-0.8.xsd"
    version="0.8"
    xml:lang="en">
""" % ROOT_TAG

DISAMBIGUATION_TEMPLATE = re.compile(r'^\{\{([a-z-]+ disambiguation|disambig|dab|disamb|hndis|geodis|numberdis|letter-numbercombdisambig)(\||\}\})')


def segment():
    line_count = 0
    file_count = 0
    page_buffer = []
    file_buffer = []
    collect = False
    with open(DUMP_FILE) as filehandle:
        for line in filehandle:
            line_count += 1
            if line.strip().startswith('<page'):
                collect = True
            if collect:
                page_buffer.append(line)
            if line.strip().startswith('</page'):
                collect = False
                if page_is_usable(page_buffer):
                    file_buffer.extend(page_buffer)
                    if len(file_buffer) > FILESIZE:
                        file_count += 1
                        print_buffer(file_buffer, file_count)
                        file_buffer = []
                        print('printing file #%d: line %d' % (file_count, line_count))
                page_buffer = []

    file_count += 1
    print_buffer(file_buffer, file_count)


def print_buffer(buffer, file_count):
    filename = '%d' % file_count
    filename = '0' * (6 - len(filename)) + filename + '.xml'
    out_file = os.path.join(OUTPUT_DIR, filename)
    with open(out_file, 'w') as output_filehandle:
        output_filehandle.write(XML_DECLARATION + '\n')
        output_filehandle.write(ROOT)
        output_filehandle.writelines(buffer)
        output_filehandle.write('</%s>\n' % ROOT_TAG)


def page_is_usable(buffer):
    buffer2 = [line.strip().lower() for line in buffer]
    title = None
    disambiguation_page = False
    redirect_page = False
    for line in buffer2:
        if line.startswith('<title>'):
            title = line.replace('<title>', '').replace('</title>', '')
        elif line.startswith('{{disambiguation'):
            disambiguation_page = True
        elif DISAMBIGUATION_TEMPLATE.search(line):
            disambiguation_page = True
        elif line.startswith('<redirect'):
            redirect_page = True

    if redirect_page or disambiguation_page:
        return False
    if title and ':' in title:
        meta = title.split(':')[0]
        if meta in NAMESPACES:
            return False

    return True


if __name__ == '__main__':
    segment()
