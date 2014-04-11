#!/usr/bin/python
import sys
import getopt
import os
import re
import Queue
import string
import nltk
import math

POINTER_DOCUMENTS_ALL = 0
LOG_BASE = 10
DOC_WEIGHTS_FILE='doc_weights.txt'

def usage():
  print "usage: " + sys.argv[0] + " -d dictionary-file -p postings-file -q file-of-queries -o output-file-of-results"

def parse_dictionary_file_entry(entry):
  file_entry_list_by_whitespace = entry.split()
  return file_entry_list_by_whitespace

def store_entry_in_dictionary(entry):
  """
  Stores dictionary in memory
  """
  term_pointer_list = parse_dictionary_file_entry(entry)
  term = term_pointer_list[0]
  df = term_pointer_list[1]
  file_pointer = term_pointer_list[2]
  dictionary[term] = {}
  dictionary[term]['fp'] = file_pointer
  dictionary[term]['df'] = df

def store_dictionary_in_memory(dict_file):
  """
  Reads from the dictionary file and stores file pointer and document frequency in memory
  """
  dict_file_reader = open(dict_file, 'r')
  for token in dict_file_reader.readlines():
    store_entry_in_dictionary(token)
  dict_file_reader.close()

def store_doc_weights_in_memory():
  """
  Reads the doc_weights.txt file and stores in memory, the doc_id and its weight
  """
  doc_file_reader = open(DOC_WEIGHTS_FILE, 'r')
  for l in doc_file_reader.readlines():
    doc_id, weight = l.split()
    doc_weights[doc_id] = float(weight)

def get_doc_ids_from_postings_file_at_pointer(file_pointer):
  """
  Retrieves postings list of doc_id that starts at position file_pointer
  """
  postings_file_reader = open(postings_file, "r")
  postings_file_reader.seek(file_pointer)
  doc_ids = postings_file_reader.readline().strip().split()
  postings_file_reader.close()
  return doc_ids

def write_to_output_file(line):
  """
  Writes result line to output file
  """
  prepend_char = "\n"
  if not os.path.isfile(output_file):
    output_writer = open(output_file, "w")
    prepend_char = ""
  else:
    output_writer = open(output_file, "a")
  output_writer.write(prepend_char + line)

def normalize_token(token):
  return stemmer.stem(token.lower())

def get_doc_ids_for_token(token):
  """
  Given a token, returns all doc_ids from the postings list
  """
  doc_ids = []
  if token in dictionary:
    postings_file_pointer_for_query_term = int(dictionary[token]['fp'])
    doc_ids = get_doc_ids_from_postings_file_at_pointer(postings_file_pointer_for_query_term)
  return doc_ids

def compute_weight_term_with_query(term, query):
  """
  Computes the value that has to be multiplied with the term-doc weight to calculate total score
  (no idf)
  """
  tf = 1 + math.log(query.count(term), LOG_BASE)
  return tf

def compute_weight_term_with_doc(term, doc_id, tf):
  """
  Computes the value has to be multiplied with the term-query weight to calculate total score
  """
  tf = 1 + math.log(int(tf), LOG_BASE)
  df = float(dictionary[term]['df'])
  return tf * df

def get_doc_weight(doc_id):
  """
  Returns the value of index doc_id in the pre cached dinctionary
  """
  return doc_weights[doc_id]

def perform_query(query):
  """
  Recursively evaluates query based on rank of precedence
  """
  scores = {}
  tokens = query.split()
  query_weight = 0
  for term in tokens:
    weight_term_with_query = compute_weight_term_with_query(term, query)
    query_weight += math.pow(weight_term_with_query, 2)
    normalized_token = normalize_token(term)
    postings_list = get_doc_ids_for_token(normalized_token)
    for doc_term in postings_list:
      doc_id, tf = doc_term.split(',')
      weight_term_with_doc = compute_weight_term_with_doc(normalized_token, doc_id, tf)
      if doc_id not in scores:
        scores[doc_id] = 0
      scores[doc_id] += weight_term_with_query * weight_term_with_doc

  query_weight = math.pow(query_weight, 0.5)
  for doc_id in scores:
    scores[doc_id] = scores[doc_id]/query_weight
    scores[doc_id] = scores[doc_id]/get_doc_weight(doc_id)
  return sorted(scores, key=scores.get, reverse=True)[0:10]

def perform_queries():
  query_file_reader = open(query_file, 'r')
  postings_file_reader = open(postings_file, 'r')
  for query in query_file_reader.readlines():
    query = query.strip()
    res = perform_query(query)
    write_to_output_file(" ".join(res))

dict_file = postings_file = query_file = output_file = None
try:
  opts, args = getopt.getopt(sys.argv[1:], 'd:p:q:o:')
except getopt.GetoptError, err:
  usage()
  sys.exit(2)
for o, a in opts:
  if o == '-d':
    dict_file = a
  elif o == '-p':
    postings_file = a
  elif o == '-q':
    query_file = a
  elif o == '-o':
    output_file = a
  else:
    assert False, "unhandled option"
if query_file == None or dict_file == None or postings_file == None or output_file == None:
  usage()
  sys.exit(2)

dictionary = {}
scores = {}
doc_weights = {}
store_dictionary_in_memory(dict_file)
store_doc_weights_in_memory()
stemmer = nltk.stem.porter.PorterStemmer()
all_docs = get_doc_ids_from_postings_file_at_pointer(POINTER_DOCUMENTS_ALL)
num_docs = len(all_docs)
perform_queries()
