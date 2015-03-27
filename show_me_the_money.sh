#!/usr/bin/env bash
while true; do
echo "STOCK DOWNLOADER RUNNING ON THIS TERMINAL"
echo "$(date) - show_me_the_money.sh executed" >> main.log
if pgrep python>/dev/null
then
echo "$(date) - stock program is running - " >> main.log
else
MR_HYDE=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
python $MR_HYDE/ArticleFinder/articleFinder.py debug &
echo "article finder executed at $(date)" >> main.log
sleep 60
python $MR_HYDE/articleFetcher/wget.py $MR_HYDE/articles/ $MR_HYDE/ArticleFinder/newsList.txt &
echo "article fetch executed at $(date)" >> main.log
fi
sleep 1200
done