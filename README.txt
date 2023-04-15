
# youtube
https://youtu.be/IBfj_0Zf2Mo

# load data into the db
python create-word-index.py --db-file buranji.db --books /home/kishori/Lacit/API_vision_google/books/text/*.english.txt

python create-word-index.py --db-file buranji.db --books ../API_vision_google/books/text/*.txt
python create-word-index.py --db-file buranji.db --books ../API_vision_google/books/text/*.txt --books-info-file book-list.tsv


# clear data: locally by deleting the db on render by connecting to the db 
# with DBeaver and manually drop the tables on the side db navigator

flask --app=run.py shell
from application import db
db.create_all()
rm buranji.db

# run the app
flask --app=run.py run


