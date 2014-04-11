index: index.py
	@rm -rf dict_dir 2>/dev/null || true
	@rm -rf doc_weights.txt 2>/dev/null || true
	python index.py -i /Users/rahij/code/hw5/patsnap-corpus/ -d dictionary.txt -p postings.txt
search: search.py
	@rm results.txt 2>/dev/null || true
	python -m cProfile -o ~/bm.profile search.py -d dictionary.txt -p postings.txt -q ../cs3245-hw4/q1.xml -o results.txt