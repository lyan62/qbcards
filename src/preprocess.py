import json
from collections import defaultdict
import mmap
from tqdm import tqdm
from difflib import SequenceMatcher
import pickle
import spacy
import copy
from utils import clean_question
nlp = spacy.load("en")


class question_set(object):
    def __init__(self):
        self.text_set = defaultdict(list)  # only questions
        self.question_objs = defaultdict(lambda: defaultdict(list))  # everything

    def add(self, question_obj):
        ans = question_obj['answer']
        self.question_objs[ans]['page'] = question_obj['page']
        if question_obj['text'] not in self.text_set[ans]:
            self.text_set[ans].append(question_obj['text'])
            self.question_objs[ans]["questions"].append(question_obj)

    def add_wiki(self, wikipath):
        with open(wikipath, 'r') as wikif:
            wikidict = json.loads(wikif.read())

        for ans in tqdm(self.question_objs.keys()):
            wikikey = self.question_objs[ans]['page']
            if wikikey in wikidict.keys():
                wiki_info = wikidict[wikikey]["text"]
                self.question_objs[ans]["questions"].append({'text': wiki_info})


    def print_objs_info(self):
        print("Unique answers in the dataset: {}".format(len(self.question_objs.keys())))
        question_nums = [len(v) for k, v in self.text_set.items()]
        print("Min and max number of questions that share same answer: {}, {}".
              format(min(question_nums), max(question_nums)))
        sorted_dict = sorted(self.text_set, key=lambda k: len(self.text_set[k]), reverse=True)
        print("Answer with most questions: {}".format(sorted_dict[0]))

    def match_questions_for_clues(self):
        for ans in tqdm(self.text_set.keys()):
            clues, clue_sents = match_question_blocks(self.question_objs[ans]["questions"])
            self.question_objs[ans]["clues"] = clues
            self.question_objs[ans]["clue_sents"] = clue_sents

    def match_wiki_for_clues(self, wiki_para_path):
        with open(wiki_para_path, 'r') as wikif:
            wiki_paras = json.loads(wikif.read())
            for ans in tqdm(self.text_set.keys()):
                wiki_clues, wiki_clue_sents = match_question_wiki(self.question_objs[ans]["questions"], wiki_paras)
                self.question_objs[ans]["clues_wiki"] = wiki_clues
                self.question_objs[ans]["clue_sents_wiki"] = wiki_clue_sents


    # def match_wiki_para(self, wiki_para_file):
    #     for ans in tqdm(self.question_objs.keys()):
    #         wiki_clues = []
    #         cur_qset = self.question_objs[ans]['questions']
    #
    #         wiki_info = wikidict[wikikey]['text']
    #         for q in cur_qset:
    #             wiki_match = get_longest_match(q, wiki_info)
    #             if wiki_match:
    #                 wiki_clues.append(wiki_match)
    #         self.question_objs[ans]['wiki_clues'] = wiki_clues
    #
    # def match_wiki_clues(self, wikipath):
    #     with open(wikipath) as wikif:
    #         wikidict = json.loads(wikif.read())
    #     print("Match questions to wikipage for clues...")
    #     for ans in tqdm(self.question_objs.keys()):
    #         wiki_clues = []
    #         cur_qset = self.question_objs[ans]['questions']
    #         wikikey = self.question_objs[ans]['page']
    #         wiki_info = wikidict[wikikey]['text']
    #         for q in cur_qset:
    #             wiki_match = get_longest_match(q, wiki_info)
    #             if wiki_match:
    #                 wiki_clues.append(wiki_match)
    #         self.question_objs[ans]['wiki_clues'] = wiki_clues


def get_num_lines(file_path):
    fp = open(file_path, "r+")
    buf = mmap.mmap(fp.fileno(), 0)
    lines = 0
    while buf.readline():
        lines += 1
    return lines


def build_objs_grouped_by_ans(file_path):
    objs_grouped_by_answer = question_set()
    with open(file_path) as in_file:
        questions = json.loads(in_file.read())['questions']
        for q in tqdm(questions):
            objs_grouped_by_answer.add(q)
    return objs_grouped_by_answer

def get_complete_clue(sa, ea, q1):
    while sa > 0:
        if q1[sa] != ' ':
            sa -= 1
        else:
            break
    while ea < len(q1):
        if q1[ea] != ' ':
            ea += 1
        else:
            break
    return q1[sa : ea]


def match_question_blocks(question_obj_list):
    clues = []
    sas = []
    clue_sents = set()

    # get clue and clue sentences in a pairewise manner
    for i in range(len(question_obj_list)):
        for j in range(i+1, len(question_obj_list)):
            q1, q2 = clean_question(question_obj_list[i]["text"]), \
                     clean_question(question_obj_list[j]["text"])
            question_matcher = SequenceMatcher(None, q1, q2)
            matching_blocks = question_matcher.get_matching_blocks()
            longest_match = sorted(matching_blocks, key=lambda k: k.size, reverse=True)[0]
            if longest_match.size > 10:
                sa, sb, span = longest_match.a, longest_match.b, longest_match.size
                # print(i, j, longest_match, "q1: ", q1[sa:sa + span],
                #       "q2: ", q2[sb:sb + span])
                clue = q1[sa : sa+span]
                complete_clue = get_complete_clue(sa, sa+span, q1)
                if clue != '':
                    clues.append(complete_clue.strip())
                    sas.append(sa)
                    clue_sent = clean_question(get_clue_sent(question_obj_list[i], sa))
                    if len(clue_sent) > 1:
                        clue_sents.add(clue_sent.strip())

    # deduplicate clues
    if len(clues) > 1:
        clues = deduplicate_clues(clues)
    return clues, list(clue_sents)

def match_question_wiki(question_obj_list, wiki_paras):
    clues = []
    sas = []
    clue_sents = set()

    # get clue and clue sentences in a pairewise manner
    for i in range(len(question_obj_list)):
        qanta_id = question_obj_list[i]["qanta_id"]
        paras = wiki_paras[str(qanta_id)]
        for j in range(len(paras)):
            q1, q2 = clean_question(question_obj_list[i]["text"]), \
                     clean_question(paras[j])
            clues, sas, clue_sents = get_pairwise_match(q1, q2, clues, sas, clue_sents, question_obj_list, i)

    # deduplicate clues
    if len(clues) > 1:
        clues = deduplicate_clues(clues)
    return clues, list(clue_sents)

def get_clue_sent(question_obj, sa):
    tokenization_list = question_obj["tokenizations"]
    shead, stail = 0, len(question_obj['text'])
    for tl in tokenization_list:
        if sa >= tl[0] and sa <= tl[1]:
            shead, stail = tl[0], tl[1]
    clue_sent = question_obj["text"][shead:stail]

    return clue_sent

def get_token_index_list(sent):
    import re
    idxs = []
    for m in re.finditer(r'\S+', sent):
        index, item = m.start(), m.group()
        idxs.append([index, index+len(item)])
    return idxs


def get_longest_match(q1, q2):
    question_matcher = SequenceMatcher(None, q1, q2)
    matching_blocks = question_matcher.get_matching_blocks()
    longest_match = sorted(matching_blocks, key=lambda k: k.size, reverse=True)[0]
    if longest_match.size > 10:
        sa, sb, span = longest_match.a, longest_match.b, longest_match.size
        # print(i, j, longest_match, "q1: ", q1[sa:sa + span],
        #       "q2: ", q2[sb:sb + span])
        match = q1[sa: sa + span].replace(". For 10 points, name this ", '')
        if match != '':
            return match
    else:
        return None

def get_pairwise_match(q1, q2, clues, sas, clue_sents, question_obj_list, i):
    question_matcher = SequenceMatcher(None, q1, q2)
    matching_blocks = question_matcher.get_matching_blocks()
    longest_match = sorted(matching_blocks, key=lambda k: k.size, reverse=True)[0]
    if longest_match.size > 10:
        sa, sb, span = longest_match.a, longest_match.b, longest_match.size
        # print(i, j, longest_match, "q1: ", q1[sa:sa + span],
        #       "q2: ", q2[sb:sb + span])
        clue = q1[sa: sa + span]
        complete_clue = get_complete_clue(sa, sa + span, q1)
        if clue != '':
            clues.append(complete_clue.strip())
            sas.append(sa)
            clue_sent = clean_question(get_clue_sent(question_obj_list[i], sa))
            if len(clue_sent) > 1:
                css = clue_sent.strip().split(",")
                for s in css:
                    clue_sents.add(s)
    return clues, sas, clue_sents


def deduplicate_clues(clues):
    ic = 0
    while ic < len(clues) - 1:
            jc = ic + 1
            while jc < len(clues):
                c1, c2 = clues[ic], clues[jc]
                clue_matcher = SequenceMatcher(None, c1, c2)
                r = clue_matcher.ratio()
                if r > 0.6:
                    if len(c1) > len(c2):
                        clues.remove(c2)
                    else:
                        clues.remove(c1)
                else:
                    jc += 1
            ic += 1
    return clues




def main():
    file_path = '../data/qanta.train.2018.04.18.json'
    objs_grouped_by_answer = build_objs_grouped_by_ans(file_path)
    objs_grouped_by_answer.print_objs_info()
    print("Get clues by compare questions in a pairwise manner...")
    objs_grouped_by_answer.match_questions_for_clues()

    print("Get clues by compare questions with wiki...")
    wiki_para_path = '/home/cheng/PycharmProjects/qbcards/data/question_top_para.json'
    objs_grouped_by_answer.match_wiki_for_clues(wiki_para_path)


    with open('../data/question.clues.json', 'w') as json_out:
        json.dump(objs_grouped_by_answer.question_objs, json_out, indent=2)



if __name__ == "__main__":
    main()
