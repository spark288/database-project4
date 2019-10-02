python skeleton_parser.py /u/j/a/jaeyeong/private/cs564/p4/auctionbase/ebay_data/items-*.json

sort -u items.dat -o itemsUnique.dat
sort -u categories.dat -o categoriesUnique.dat
sort -u bids.dat -o bidsUnique.dat
sort -u users.dat -o usersUnique.dat