#How to upload a new db
# cd buranji where you see the utilities folder
cd buranji 

# make sure you load the shell variables by executing
source ../env_variables.sh

# if you want to create the file buranji.db file locally/remote then 
python utilities/create-word-index.py --db-file dev/prod --books ../ocr-project/books/text/*.txt --books-info-file book-list.tsv


# youtube
https://youtu.be/IBfj_0Zf2Mo

# load data into the db
python create-word-index.py --db-file dev --books /home/kishori/Lacit/ocr-project/books/text/*.english.txt
python create-word-index.py --db-file dev --books ../ocr-project/books/text/*.txt


# load the books into the db
python create-word-index.py --db-file dev --books ../ocr-project/books/text/*.txt --books-info-file book-list.tsv


# clear data: locally by deleting the db on render by connecting to the db 
# with DBeaver and manually drop the tables on the side db navigator

flask --app=run.py shell
from application import db
db.create_all()
rm buranji.db

# run the app
flask --app=run.py run


# ocr pdf copies
python utilities/ocr-with-google.py --pdf-input ../ocr-project/books/pdfs/bara-bhuyan-nakul_chandra_bhuyan-assamese.pdf --output ../ocr-project/books/text/bara-bhuyan-nakul_chandra_bhuyan-assamese.txt --language as --pickle-folder ../ocr-project/tmp-pickle/ --page-range-pdf 11,39
