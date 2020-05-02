from fyp_detection_functions import Detector
from fyp_detection_framework import DataLoader, DetectionFramework
import pandas as pd
import time


class MiniDetectionFramework:
    """
        Runs the detection model/algorithm on queries in different ways.
        Mini version for use only for timing how fast relation extraction is.
    """

    def __init__(self, ckpt_path):
        """
        Initializer
        """

        self.support = []  # stores the list of relation support examples which have been loaded. multiple datasets can be used, each dataset is a separate list.
        self.detector = Detector(chpt_path=ckpt_path)  # the detector/model
        self.queries = []
        self.ckpt_path = ckpt_path

    def load_support_file(self, path):
        """
        Loads the relation support data which is mentioned.
        """
        self.support = []
        self.support.append(DataLoader.load_relation_support_csv(path))

    def load_queries_csv(self, path):
        """
        Loads the queries which are contained at the passed path.
        Detects if the head and tail are specified. If so, these are loaded using a special function.
        """
        self._load_queries_predefined_head_tail_csv(path)

    def _load_queries_predefined_head_tail_csv(self, path):
        """
        Loads the queries which are contained at the passed path, these queries are supposed to have the head and tail to use defined.
        """
        self.queries = DataLoader.load_query_with_head_tail_csv(path)

    def detect(self):
        """
            Runs the detection algorithm for the particular queries

            queries - the set of queries to run the algorithm on
            rt_results - real time results list - if specified, then the analysis results will be added to this list as they are evaluated.
            cancel_flag - set the index 0 element to True if you want the analysis to be cancelled.
        """
        if len(self.support) == 0:
            raise ValueError("No relation support has been added!")

        if len(self.queries) == 0:
            raise ValueError("No queries have been added!")

        results = []

        time_info = []   # tuples of char length to time taken

        for i, sup in enumerate(self.support):  # iterate through the support datasets
            for q in self.queries:  # iterate through the possible queries

                # the head and tail are predefined in the query, so just those are used.

                start = time.time()
                result = self.detector.run_detection_algorithm(q, sup)
                end = time.time()
                time_info.append((len(q['sentence'].split(" ")), end - start))
                # self.detector.print_result(result['sentence'], result['head'], result['tail'], result['pred_relation'])

                result['rel_sup_ind'] = (i + 1)  # the index of the relation support dataset which is used
                results.append(result)

        return time_info


# In this file, the runtime of the relation extraction model will be timed by using different inputs
ck_path = "/home/gssenthil/workspace/FewRel/checkpoint/NA-predict-model.pth.tar"
det_framwork = None

sup_datasets = ['test_relation_support_dataset.csv', 'test_relation_support_dataset_2.csv', 'test_relation_support_dataset_3.csv', 'test_relation_support_dataset_4.csv']
query_csvs = ['test_queries_with_head_tail.csv', 'test_queries_with_head_tail_2.csv', 'test_queries_with_head_tail_3.csv']
query_csvs_no_head_tail = ['test_queries_without_head_tail.csv', 'test_queries_without_head_tail_2.csv', 'test_queries_without_head_tail_3.csv']

print("==RELATION EXTRACTION ALONE==")

for si, sup_dataset_path in enumerate(sup_datasets):
    for qi, query_csv_path in enumerate(query_csvs):
        print()
        print("Support Dataset {}, Query Set {}".format(si+1, qi+1))
        start = time.time()
        det_framwork = None
        det_framwork = MiniDetectionFramework(ck_path)
        det_framwork.load_support_file(sup_dataset_path)
        det_framwork.load_queries_csv(query_csv_path)

        time_info = det_framwork.detect()
        end = time.time()
        total_time_req = end - start
        df = pd.read_csv(sup_dataset_path)
        total_sup_length = 0
        N = df['reldescription'].unique().shape[0]
        K = df[df['reldescription'] == df['reldescription'].iloc[0]].shape[0]
        for i, row in df.iterrows():
            total_sup_length += len(row['sentence'].split(" "))
        print("{}-way {}-shot".format(N, K))
        print("Num Queries: "+str(len(time_info)))
        print("Total Time Required: {} s".format(end - start))
        avg_sup_sentence_length = total_sup_length / (N*K)
        print("Average Support Sentence Length: {} words (divided by spaces)".format(avg_sup_sentence_length))
        time_per_query = total_time_req/len(time_info)
        print("Average Time per Query: {} s".format(time_per_query))
        avg_query_length = sum(i[0] for i in time_info) / len(time_info)
        print("Average query length: {} words (divided by spaces)".format(avg_query_length))
        print("Average Time per Query per Support Sentence: {} s".format(total_time_req / (len(time_info) * N * K)))


print()
print()
print("==FULL PIPELINE - RELATION EXTRACTION, NER, COREF, SENTIMENT==")
d = DetectionFramework(ck_path)
for si, sup_dataset_path in enumerate(sup_datasets):
    for qi, query_csv_path in enumerate(query_csvs_no_head_tail):
        print()
        print("Support Dataset {}, Query Set {}".format(si + 1, qi + 1))

        start_time = time.time()
        d.clear_support_queries()
        d.load_support_files(".", sup_dataset_path)
        d.load_queries_csv(query_csv_path)
        end_time = time.time()
        print("Detection Framework INIT time: {} s".format(end_time - start_time))

        start = time.time()
        results = d.detect()
        end = time.time()
        total_time_req = end - start
        df = pd.read_csv(sup_dataset_path)
        total_sup_length = 0
        N = df['reldescription'].unique().shape[0]
        K = df[df['reldescription'] == df['reldescription'].iloc[0]].shape[0]
        for i, row in df.iterrows():
            total_sup_length += len(row['sentence'].split(" "))
        print("{}-way {}-shot".format(N, K))
        print("Num Queries: " + str(len(results)))
        print("Total Time Required: {} s".format(end - start))
        avg_sup_sentence_length = total_sup_length / (N * K)
        print("Average Support Sentence Length: {} words (divided by spaces)".format(avg_sup_sentence_length))
        time_per_query = total_time_req / len(results)
        print("Average Time per Query: {} s".format(time_per_query))
        df = pd.read_csv(query_csv_path)
        avg_query_length = sum(len(i['sentence'].split(" ")) for ii, i in df.iterrows()) / len(results)
        print("Average query length: {} words (divided by spaces)".format(avg_query_length))
        print("Average Time per Query per Support Sentence: {} s".format(total_time_req / (len(results) * N * K)))