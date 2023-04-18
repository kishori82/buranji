
# youtube
https://youtu.be/IBfj_0Zf2Mo

# load data into the db
python create-word-index.py --db-file dev --books /home/kishori/Lacit/API_vision_google/books/text/*.english.txt

python create-word-index.py --db-file dev --books ../API_vision_google/books/text/*.txt
python create-word-index.py --db-file dev --books ../API_vision_google/books/text/*.txt --books-info-file book-list.tsv


# clear data: locally by deleting the db on render by connecting to the db 
# with DBeaver and manually drop the tables on the side db navigator

flask --app=run.py shell
from application import db
db.create_all()
rm buranji.db

# run the app
flask --app=run.py run


# orc
python ../API_vision_google/utilities/ocr-with-google.py --pdf-input ../API_vision_google/books/pdfs/bara-bhuyan-nakul_chandra_bhuyan-assamese.pdf --output ../API_vision_google/books/text/bara-bhuyan-nakul_chandra_bhuyan-assamese.txt --language as --pickle-folder ../API_vision_google/tmp-pickle/ --page-range-pdf 11,39
