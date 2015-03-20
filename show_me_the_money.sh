#!/usr/bin/env bash
echo "STOCK DOWNLOADER RUNNING ON THIS TERMINAL"
echo "$(date) - show_me_the_money.sh executed"
if pgrep python>/dev/null
then
echo "$(date) - stock program is running - "
else
MR_HYDE=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
python $MR_HYDE/ArticleFinder/articleFinder.py $MR_HYDE/symbols.csv $MR_HYDE/newsList.txt
echo "sleeping..."
sleep 60
python $MR_HYDE/articleFetcher/wget.py $MR_HYDE/articles/ $MR_HYDE/newsList.txt
fi
