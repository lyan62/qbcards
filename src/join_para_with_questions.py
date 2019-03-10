import json
from tqdm import tqdm
from utils import get_num_lines

def get_questions_from_json(file_path):
    with open(file_path) as in_file:
        questions = json.loads(in_file.read())['questions']
    return questions

def get_paras_from_json(file_path):
    para_dict = {}
    with open(file_path) as in_file:
        for line in tqdm(in_file, total=get_num_lines(file_path)):
            paras = json.loads(line)
            top_para_sents = []
            for i in range(len(paras["annotated_paras"])):
                if len(paras["annotated_paras"][i]) > 0:
                    top_para_sents.append(paras["annotated_paras"][i][0]["paragraph"])
            para_dict[paras['qanta_id']] = top_para_sents

    with open('../data/question_top_para.json', 'w') as json_out:
        json.dump(para_dict, json_out, indent=2)

def main():
    json_file_path = '/home/cheng/PycharmProjects/qbcards/data/qanta.train.paragraphs.2018.04.18.jsonl'
    get_paras_from_json(json_file_path)


if __name__ == "__main__":
    main()