
"module to convert image to text and evaluate the answer import time"
import language_check
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import RegexpTokenizer
from nltk.stem.porter import PorterStemmer
from nltk.corpus import wordnet as wn
from nltk.stem import WordNetLemmatizer
from tika import parser
import os
import mysql.connector
from mysql.connector import Error
from flask import Flask, request,render_template
import pandas as pd

# TikaServerJar=r"C:\Users\Viola\PycharmProjects\ocr\tika-server-1.24.jar"#

class evaluation():
    def pdf_to_text(self,filename):
        raw = parser.from_file(filename)
        text=raw["content"]

        return text

    def grammar_correction(self,data):
        print("GRAMMAR CHECK")
        tool = language_check.LanguageTool('en-US')
        # text = open(filename, "r")
        # data = text.read()
        matches = tool.check(data)
        corrected_data = language_check.correct(data, matches)
        return corrected_data
    def stop_word_removal(self,data):
        tokenizer = RegexpTokenizer(r'\w+')
        stop_words = set(stopwords.words('english'))
        word_tokens = tokenizer.tokenize(data)
        filtered_sentence = [w for w in word_tokens if not w in stop_words]
        # for w in word_tokens:
        #     if w not in stop_words:
        #         filtered_sentence.write(w)
        return (filtered_sentence)
    def lemmatization(self,data):
        lemmatizer = WordNetLemmatizer()
        lemme = []
        for w in data:
            lemme.append(lemmatizer.lemmatize(w))
        return lemme
    def wordNet(self,answer,keywords):
        lemmatizer = WordNetLemmatizer()
        extended_keywords = []
        extended_answer = []
        keywords_matched = 0
        for word in keywords:
            temp_list = []
            temp_list.extend(word)
            for happy_lemma in wn.lemmas(word):
                temp_list.append(happy_lemma.name())
                for related_lemma in happy_lemma.derivationally_related_forms():
                    temp_list.append(related_lemma.name())
            temp_list = list(set(temp_list))
            extended_keywords.append((word, temp_list))

        for word in answer:
            temp_list = []
            temp_list.extend(word)
            for happy_lemma in wn.lemmas(word):
                temp_list.append(happy_lemma.name())
                for related_lemma in happy_lemma.derivationally_related_forms():
                    temp_list.append(related_lemma.name())
            temp_list = list(set(temp_list))
            extended_answer.append((word, temp_list))

        keywords_dictionary = {key: value for (key, value) in extended_keywords}
        answer_dictionary = {key: value for (key, value) in extended_answer}
        # print("THE KEYWORD DICTIONARY")
        # print(keywords_dictionary)
        # print("THE ANSWER DICTIONARY")
        # print(answer_dictionary)

        for keyword in keywords_dictionary.keys():
            flg=0
            for answer in answer_dictionary.keys():
                if keyword == answer:
                    flg=1
                    # print("matched word:"+keyword+" "+answer)
                    keywords_matched = keywords_matched + 1
                    break
                else:
                    for iterate in wn.synsets(answer):
                        for iter in iterate.lemmas():
                            if keyword == iter.name():
                                print("matched word:" + keyword + " " + answer)
            if(flg==0):
                print("unmatched is:"+keyword)
        return keywords_matched

    def question_no_split_ans(self,ans):
        words = ans.split(" ")
        mystr = ""
        iter = 1
        newstr = ''
        flg=0
        for i in range(0, len(words)):
            q_no = str(iter) + '.'
            words[i] = words[i].replace('\n', '')
            if(i!=(len(words)-1)):
                if (words[i] == q_no or words[i+1]== 'a.' or words[i+1]=='b.'):
                    iter = iter + 1
                    newstr = newstr + mystr
                    mystr = "hai " + words[i] + " "
                else:
                    mystr = mystr + words[i] + " "

        newstr = newstr + mystr
        newstr = newstr.split("hai ")
        # print("-----this is a list of answers divided---------")
        return newstr  # list of div  answers

    def ab_separation(self,ans,keyword):
        store='0'
        new_keyword_list = keyword[0:11]
        del keyword[:11]
        index=-1
        repetition= []
        for ans_iterate in ans:
            index=index+1#no of answers to know the index
            ans_iterate_word = ans_iterate.split(" ")
            if(store==ans_iterate_word[0]):
                repetition.append(index)
            for keyword_iterate in keyword:
                keyword_iterate_word = keyword_iterate.split(" ")
                if (ans_iterate_word[0] == keyword_iterate_word[0]):
                    store=ans_iterate_word[0]
                    if (ans_iterate_word[1] == keyword_iterate_word[1]):
                        new_keyword_list.append(keyword_iterate)
                        break
        # print("HEY YOU HAV REPEATED")
        # print(repetition)
        return new_keyword_list,repetition  # a new keyword list of questions contained in the answer sheet

    def database_connection(self, name, regno, sub_name, sub_code, tot, case):
        try:
            connection = mysql.connector.connect(host='localhost',
                                                 database='student',
                                                 user="root",
                                                password="sathya123")
            if connection.is_connected():
                db_Info = connection.get_server_info()
                # print("Connected to MySQL Server version ", db_Info)
                mySql_insert_query = """INSERT INTO details (student_name,register_no,subject_name,subject_code,total_marks,status) 
                           VALUES 
                           (%s,%s,%s,%s,%s,%s) """
                values = (name, regno, sub_name, sub_code, tot, case)
                cursor = connection.cursor()
                cursor.execute("select database();")
                record = cursor.fetchone()
                # print("You're connected to database: ", record)
            cursor.execute(mySql_insert_query, values)
            connection.commit()
            # print(cursor.rowcount, "Record inserted successfully into Details table")

        except Error as e:
            print("Error while connecting to MySQL", e)
        finally:
            if (connection.is_connected()):
                cursor.close()
                connection.close()
                print("MySQL connection is closed")


# total_marks=10
eval=evaluation()
api=Flask(__name__,template_folder='template')
UPLOAD_DIRECTORY = "Answer/"

@api.route("/whole results/")
def generate_file():
    connection = mysql.connector.connect(host='localhost',
                                         database='student',
                                        user = "root",
                                        password = "sathya123"
                                            )

    cur = connection.cursor()
    cur.execute("SELECT * FROM details")
    header = [row[0] for row in cur.description]
    data = cur.fetchall()
    pd.DataFrame(data).to_excel('result.xls', header=header, index=False)
    data_xls = pd.read_excel(r'result.xls')
    return data_xls.to_html(index=False)
    # above code directly generates table in web page
    #     from tabulate import tabulate
    #     data=tabulate(data, tablefmt='html')
    #     return data


@api.route("/", methods=["POST","GET"])
def upload_file():
    tot = 0
    store_my_previous_mark = 0
    if request.method=="POST":
        # total_marks=request.form['mark']
        # total_marks=int(total_marks)
        sub_name=request.form['sub_name']
        sub_code=request.form['sub_code']
        name=request.form['name_field']
        print(name)
        regno=request.form['regno_field']
        print(regno)
        mark=request.files['mark']

        file1= request.files['file_field']

        keyword=request.files['keyword']
        # print(keyword.filename)
        if file1.filename != '':
            ans_path=os.path.join(os.path.join(UPLOAD_DIRECTORY), file1.filename)
            file1.save(os.path.join(os.path.join(UPLOAD_DIRECTORY), file1.filename))
        if keyword.filename != '':
            key_path = os.path.join(os.path.join(UPLOAD_DIRECTORY), keyword.filename)
            keyword.save(os.path.join(os.path.join(UPLOAD_DIRECTORY), keyword.filename))
        if mark.filename != '':
            mark_path = os.path.join(os.path.join(UPLOAD_DIRECTORY), mark.filename)
            mark.save(os.path.join(os.path.join(UPLOAD_DIRECTORY), mark.filename))


            # '''remove comment of below code to evaluate from image'''
            data = eval.pdf_to_text(ans_path)
            key = eval.pdf_to_text(key_path)
            mrk = eval.pdf_to_text(mark_path)
            # print(key)
            key=key.replace("\n",'')
            # print(data)



            # print(data)
            answer_file = open(ans_path, "w+")
            answer_file.write(data.encode('ascii', 'ignore').decode('ascii'))
            answer_file.close()

            #print(key)
            key_file = open(key_path, "w+")
            key_file.write(key.encode('ascii', 'ignore').decode('ascii'))
            key_file.close()

            #print(mark)
            mark_file = open(mark_path, "w+")
            mark_file.write(mrk.encode('ascii', 'ignore').decode('ascii'))
            mark_file.close()

            # calculate number of lines in the answer
            # answer_file = open(ans_path, "r")
            # line = list(answer_file)
            # # print(len(line))
            # answer_file.close()
            ans=open(ans_path,"r")
            anss=ans.read()
            #-----------------------------------here i add
            answer=eval.question_no_split_ans(anss)#returned a list# answer=ans.read().split("\n\n")

            # print("THE RETURNED ANSWER VALUE IS")
            # print(answer)

            keys = open(key_path, "r")
            keyss=keys.read();
            # -----------------------------------here i add#keyss = keys.read().split("\n\n")
            keyword=eval.question_no_split_ans(keyss)#list returned

            # print("THE RETURNED KEYWORD VALUE IS")
            # print(keyword)
            # print(len(keyword))

            mark = open(mark_path, "r")
            marks = mark.read()
            marks = eval.question_no_split_ans(marks)

            # print("THE RETURNED MARK LIST")
            # print(marks)
            markss=[]
            new_keyword_list=[]
            repetition=[]

            #A call for new keyword list based on the answer written
            new_keyword_list,repetition=eval.ab_separation(answer,keyword)
            # print("new keyword list is-----------")
            # print(new_keyword_list)
            #
            # print("Repetition list")
            # print(repetition)

            count=-1
            for data,keywords,mark in zip(answer,new_keyword_list,marks):
                    count=count+1
                    if data == '':
                        continue
                    elif keywords == '':
                        continue
                    else:
                        corrected_data = eval.grammar_correction(data)
                        corrected_keywords = eval.grammar_correction(keywords)
                        print("----------------------------------------------------")
                        print("\n\nTHE ANSWER IS\n")
                        print(data)
                        print("THE KEYWORDS ARE")
                        print( keywords+"\n")
                        print("THE TOTAL MARK ALLOTED IS")
                        print("count",count)
                        if(count>10):
                            mark_al=mark[-3]+mark[-2]
                            print(mark[-3]+mark[-2])
                        else:
                            mark_al=mark[-2]
                        print("marks[-2]??????")
                        print(mark_al)

                        # print(corrected_keywords[1].split())
                        stopword_removed_answer = eval.stop_word_removal(data)
                        stopword_removed_keywords = eval.stop_word_removal(keywords)

                        print("Stop word removed")
                        print(stopword_removed_keywords)

                        lemme_answer = eval.lemmatization(stopword_removed_answer)
                        lemme_keywords = eval.lemmatization(stopword_removed_keywords)
                        print("lemme keywords")
                        print(lemme_keywords)
                        keywords_len=len(lemme_keywords)-1
                        print("keyword length")
                        print(keywords_len)

                        no_of_matched_words = eval.wordNet(lemme_answer, lemme_keywords)
                       # no_of_matched_words=3;
                        print("The number of matched words")
                        no_of_matched_words=no_of_matched_words-1
                        print(no_of_matched_words-1)

                        # percentage of keywords present in answer
                        match_percentage = (no_of_matched_words / keywords_len) * 100
                        print(match_percentage)
                        # overall_percentage=(grammar_percentage+match_percentage)/2

                        mark=float(mark_al)
                        print("------------------------MARK---------------",mark)
                        q_mark = (match_percentage / 100) * mark
                        q_mark=round(q_mark, 2)

                        #what if 12a and 12b is written award highest mark

                        pop_it_out= 0
                        for i in repetition:
                            if(i==count):
                                print("GOTCHA")
                                print(store_my_previous_mark)
                                if(store_my_previous_mark>q_mark):
                                    q_mark=store_my_previous_mark
                                pop_it_out=1
                        store_my_previous_mark=q_mark
                        if(pop_it_out==1):
                            print("I DELETED")
                            del markss[-1]
                            print(markss)
                            pop_it_out=0
                        markss.append(q_mark)
                        mark_file = open("final_marks.xls", "w")
                        n = mark_file.write(str(q_mark))
                        n = mark_file.write("\n")
                        mark_file.close()
                        print("The mark is:\n", markss)


        tot=round(sum(markss),2)
        if tot>=80:
            case="Best"
        elif tot>=50:
            case="Average"
        else:
            case="Worst"
        print("The total mark is \n",tot)

        # DATABASE CONNECTION
        eval.database_connection(name, regno, sub_name, sub_code, tot, case)
        return render_template("result.html", mark=markss, tot=tot, name=name, regno=regno, case=case,
                               sub_name=sub_name, sub_code=sub_code)
    return render_template("upload.html")

if __name__ == "__main__":
    path=api.run(port=8001)
