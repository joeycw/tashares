# tashares

Tashares is a python module to forecast China A-shares price trend in 1, 2 and 5 days.
It's an open-source tool, that utilizes **yfinance** and **talib** to generate 155 techinical analysis features, and then apply **catboost** to build three ranking models that order all stock prices of interest from trending up to trending down relatively.

# installation

TA Lib (technical analysis library) is a prerequisite, which can be installed from source code <https://ta-lib.org/hdr_dw.html>.

On a Linux machine, download source code <a href="http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz"> ta-lib-0.4.0-src.tar.gz </a>, and then run the following to complete installation.

```
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
sudo make install
```

Ref to <a href="https://pypi.org/project/TA-Lib/">Python wrapper for TA-LIB</a> for installatiob instructions on ther platforms.

Then this is the recommended way to install tashares:

```
pip install tashares
```

The latest code on github can be installed with:

```
pip install git+https://github.com/joeycw/tashares
```

# quick start

After installation, launch python3, run a test

```
>>> from tashares.tashares import Tashares
>>> tas = Tashares()
>>> tas()
```

The test result looks like the following, and the ashares list is under the *data* folder, *tashares/data/list_of_interest*.

```
   rank     symbol       date     day_1     day_2     day_5     score                        shortname
0      0  300059.SZ 2022-02-18  0.316329  0.256538  0.338447  0.303771               east_money_informa
1      1  600000.SS 2022-02-18  0.086610  0.229318  0.278299  0.198076  shanghai_pudong_development_ban
2      2  000100.SZ 2022-02-18 -0.004794  0.180493  0.398047  0.191249               tcl_technology_gro
3      3  000725.SZ 2022-02-18 -0.056116  0.084442  0.306973  0.111766                boe_technology_gp
4      4  601899.SS 2022-02-18  0.029995 -0.122044 -0.079928 -0.057326        zijin_mining_group_co.ltd
5      5  600660.SS 2022-02-18 -0.038651 -0.057926 -0.117553 -0.071377  fuyao_glass_industry_group_co._
6      6  000001.SZ 2022-02-18 -0.151842 -0.119519  0.037139 -0.078074                     ping_an_bank
7      7  601888.SS 2022-02-18 -0.243156 -0.091782  0.088246 -0.082231  china_tourism_group_duty_free_c
8      8  000333.SZ 2022-02-18 -0.191822 -0.098220  0.019681 -0.090121               midea_group_co_ltd
9      9  002594.SZ 2022-02-18 -0.152458 -0.182644  0.015600 -0.106501                  byd_company_ltd
10    10  688256.SS 2022-02-18 -0.207314 -0.168954 -0.126835 -0.167701  cambricon_technologies_corporat
11    11  601111.SS 2022-02-18 -0.222781 -0.134231 -0.374176 -0.243729                    air_china_ltd
12    12  601168.SS 2022-02-18 -0.231550 -0.242365 -0.306838 -0.260251          western_mining_co._ltd.
13    13  002415.SZ 2022-02-18 -0.178105 -0.295894 -0.322221 -0.265407               hangzhou_hikvision
14    14  601318.SS 2022-02-18 -0.476346 -0.201118 -0.211716 -0.296394  ping_an_insurance(group)co.of_c
15    15  601668.SS 2022-02-18 -0.351012 -0.250289 -0.473890 -0.358397  china_construction_engineering_
16    16  600196.SS 2022-02-18 -0.357091 -0.418911 -0.440672 -0.405558  shanghai_fosun_pharmaceutical_g
17    17  002460.SZ 2022-02-18 -0.382765 -0.583493 -1.123627 -0.696628               ganfeng_lithium_co
18    18  600111.SS 2022-02-18 -0.716760 -0.801826 -1.196879 -0.905155  china_nthn_rare_earth_(gp)_hi-t
19    19  002466.SZ 2022-02-18 -1.019046 -0.866705 -1.299832 -1.061861               tianqi_lithium_cor
```

Once a customized symbol list of interest is available, run the following to produce predictive results.

```
>>> tas = Tashares(symbol_list="/absolute/path/to/list_of_ashares")
>>> tas()
```

The format of symbol list is the following. There is a longer list *list_of_all* of more than 1000 under the *data* folder.

```
002415.SZ
000100.SZ
601168.SS
002466.SZ
601668.SS
```

# experimental results

Trained catboost models on 5 years trading history, from 2015-01-01 to 2020-01-01, and tested on about 2 years trading history after 2020-01-01. Here each trading day is treated as a ranking list.

Here are the test metrics for the model to predict next day's trending:
| Metric | Value |
| ----------- | ----------- |
|ranking AUC | 0.5548286031164161 |
|ranking QueryAUC | 0.5656376778982241|
|ranking DCG:top=20 |4.602394544886906|
|ranking NDCG:top=20 |0.6537243035654637|
|ranking MAP:top=10 |0.5476869971732982|
|ranking MRR:top=10 |0.8856164383561643|
|ranking PrecisionAt:top=10 |**0.6618721461187219**|
|ranking RecallAt:top=10 |0.009447016096515872|
|ranking PrecisionAt:top=20 |0.6239726027397255|
|ranking RecallAt:top=20 |0.017115635510283153|

Here is a real-world experiment lasting half year so far. The dotted vertical line indicates the date of forecasting launch, coupled with certain trading strategy.

<img src="./tashares/docs/snapshot.png" alt="drawing" width="300"/>

On US stocks, the same approach shows much worse ranking metrics that hasn't been applied to real world.

# other content

- send out daily email with the forecasting results enclosed. Find the script **sendemail.py** under the *docs* folder. In case you are using gmail free service, your own passcode obtained from gmail is required in Line 29.

- dump training/test/forecast samples into three csv files rspectively for further study.

   1. (optional) specify StartFromDate in cfg.ini, Default 2015-01-01
   2. (optional) specify MaxTrainingDate in cfg.ini, Default = 2020-01-01
   3. (optional) prepare a customized symbol list, Default *list_of_all* under the data folder
   4. run the following to dump samples in current working directory. Three files are generated,
      1. *training_ashares.csv*, containing samples from StartFromDate to MaxTrainingDate
      2. *test_ashares.csv*, containing samples from MaxTrainingDate to yesterday
      3. *forecasting_ashares.csv*, containing samples of yesterday (just one day)

   ```
   >>> from tashares.wrapper import dump_datafiles
   >>> dump_datafiles()
   ```

   5. to get samples of customized list

   ```
   >>> dump_datafiles(symbol_list='/absolute/path/to/list')
   ```

   6. (optional) specify the directory to dump the three cvs files.

   ```
   >>> dump_datafiles(symbol_list='/absolute/path/to/list', data_dir='/tmp')
   ```

# reference

- technical analysis library ta lib source code <https://ta-lib.org/hdr_dw.html>

- ta lib python wrapper <https://github.com/mrjbq7/ta-lib>

- yfinance <https://pypi.org/project/yfinance/>

- catboost <https://catboost.ai/>

- packaging python project <http://alexanderwaldin.github.io/packaging-python-project.html>
- pypi publish package <https://realpython.com/pypi-publish-python-package/>

# disclaimer

This software is released under the mit license.
