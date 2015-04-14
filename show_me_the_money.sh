#!/usr/bin/env bash
MR_HYDE=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
while true; do
echo "STOCK DOWNLOADER RUNNING ON THIS TERMINAL"
echo "$(date) - show_me_the_money.sh executed" >> main.log
cp $MR_HYDE/ArticleFinder/finder.log /var/www/
cp $MR_HYDE/main.log /var/www/
cp $MR_HYDE/articles/fetcher.log /var/www/
chmod a+r /var/www/finder.log
chmod a+r /var/www/main.log
chmod a+r /var/www/fetcher.log
if pgrep python>/dev/null
then
echo "$(date) - stock program is running - " >> main.log
else
python $MR_HYDE/ArticleFinder/articleFinder.py &
echo "article finder executed at $(date)" >> main.log
sleep 60 &
python $MR_HYDE/articleFetcher/wget.py $MR_HYDE/articles/ $MR_HYDE/ArticleFinder/newsList.txt &
echo "article fetch executed at $(date)" >> main.log
fi
sleep 1200
done

