those=( \
'{"name": "Pasta zuccare",
"photo": "https://pbs.twimg.com/media/EYEk7WAXkAA41Zm?format=jpg",
"ingredients": ["pasta", "water", "butter", "sugar", "flour"],
"steps": ["cook pasta","pour almost all water away, leave as little as you can", "away from fire add some 50g of butter and stir it in with leftover water on bottom and with pasta", "put on fire and keep stirring", "once melted and boiling for some time, add lotta sugar", "stir smooth", "spoona flour", "stirrr"]}' \
'{"name": "fried chickpeas",
"photo": null,
"ingredients": ["chickpeas","butter"],
"steps": ["pull out of can","fry on butter"]}' \
'{"name": "mac n cheese",
"photo": null,
"ingredients": ["pasta", "melted cheese", "milk", "flour", "butter"],
"steps": ["cook pasta the whole time","fry flour in butter", "milk it in", "add cheese"]}' \
'{"name": "crêpès",
"photo": null,
"ingredients": ["eggs","milk", "beer", "flour", "butter"],
"steps": ["which flour into milk","add melted butter", "add beer", "add eggs", "fry in portions on crepe pan"]}' 
)

for i in "${those[@]}"
do
	curl -X POST -d "$i" http://localhost:8080/recipe/api/new
done