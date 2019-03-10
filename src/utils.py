import mmap

def get_num_lines(file_path):
    fp = open(file_path, "r+")
    buf = mmap.mmap(fp.fileno(), 0)
    lines = 0
    while buf.readline():
        lines += 1
    return lines


def clean_question(question):
    """
    clean quesetion strs
    :param question:
    :return:
    """
    question = question.replace('Â', '')
    question = question.replace('猴', 'f')
    question = question.replace('睌', 'f')
    question = question.replace('&quot;', 'f')
    question = question.replace('✴', 'fi')
    question = question.replace('⢄', 'ft')
    question = question.replace('Ã¶', 'ö')
    question = question.replace('Ã©', 'é')
    question = question.replace('送', 'fi')
    question = question.replace('畔', 'i')
    question = question.replace('㱀', 'f')
    question = question.replace('Ã¼', 'ü')
    question = question.replace('Ã±', 'ñ')
    question = question.replace('㻈', 'f')
    question = question.replace('Ã¨', 'è')
    question = question.replace('Ã¸', 'ü')
    question = question.replace('ぺ', 'ft')
    question = question.replace('*))', '*)')
    question = question.replace('Ãº', 'ú')
    question = question.replace('Ã³', 'ó')
    question = question.replace('ǎ', 'ā')
    question = question.replace('í§', 'ç')
    question = question.replace('Ã¡', 'á')
    question = question.replace('Ã¹', 'ù')
    question = question.replace('Ã¬', 'ì')
    question = question.replace('Ã‰', 'É')
    question = question.replace('Ã‰', '')
    question = question.replace('►', '')
    question = question.replace('Ã', 'í')
    question = question.replace('â€œ', '"')
    question = question.replace('â€', '"')
    question = question.replace("For 10 points name this", '')
    question = question.replace(". For 10 points, name this", '')
    question = question.replace(". For 10 points,", '')
    question = question.replace(". For 10 points,", '')
    question = question.replace(". For 10 points", '')
    question = question.replace("For 10 points,", '')
    question = question.replace(" for 10 points,", '')
    question = question.replace(" for 10 points", '')
    question = question.replace("for 10 points", '')
    question = question.replace("For ten points,", '')
    question = question.replace("For ten points", '')
    question = question.replace("or 10 points, name this", '')
    question = question.replace("FTP, identify", '')
    question = question.replace("FTP,", '')
    question = question.replace(" name this", '')
    return question